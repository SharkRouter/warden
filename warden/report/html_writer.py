# ruff: noqa: E501
"""Self-contained HTML report generation — Warden v2 Rich Report.

CRITICAL: No external requests. All CSS and layout are embedded.
Air-gapped environments work perfectly — system font stack only.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from warden import __scoring_model__, __version__
from warden.models import ScanResult, ScoreLevel, Severity
from warden.scoring.dimensions import ALL_DIMENSIONS, GROUPS, TOTAL_RAW_MAX

SEVERITY_COLORS = {
    Severity.CRITICAL: "#ff3b3b",
    Severity.HIGH: "#ff8c00",
    Severity.MEDIUM: "#f5c518",
    Severity.LOW: "#4ade80",
}

LEVEL_COLORS = {
    ScoreLevel.GOVERNED: "#4ade80",
    ScoreLevel.PARTIAL: "#ff8c00",
    ScoreLevel.AT_RISK: "#ff3b3b",
    ScoreLevel.UNGOVERNED: "#ff3b3b",
}

# WhiteFin (formerly SharkRouter) estimated score (from competitors.py registry)
_SHARKROUTER_SCORE = 91

# --- Dimension gap recommendation templates ---
_REC_TEMPLATES = {
    "D1": ("Establish a live tool inventory", "No tool catalog detected. Without a centralized inventory of MCP tools and their schemas, governance policies have nothing to enforce against. Deploy a tool registry with auto-discovery."),
    "D2": ("Deploy risk classification for tool calls", "No risk scoring on tool invocations. Every tool call carries the same implicit trust level. Classify tools by risk (destructive, financial, exfiltration) and enforce approval gates for high-risk categories."),
    "D3": ("Implement policy enforcement on tool calls", "No deny/allow/audit policies detected. Agents can invoke any tool without restriction. Deploy an inline policy engine with deny-by-default for destructive and financial tools."),
    "D4": ("Move credentials to a secrets manager", "API keys or credentials found in source code. Move to HashiCorp Vault, AWS Secrets Manager, or environment-level secret stores. Rotate all exposed keys immediately. Add .env to .gitignore."),
    "D5": ("Remove PII from log files and add tokenization", "Sensitive data detected in log content. Install presidio-analyzer for PII detection. Tokenize before sending to LLM providers. Configure log scrubbing for email addresses, phone numbers, and SSNs."),
    "D6": ("Add framework detection coverage", "No LangChain/AutoGen/CrewAI framework governance detected. Framework-aware scanners catch framework-specific vulnerabilities like unsafe agent loops and unvalidated tool outputs."),
    "D7": ("Add human-in-the-loop approval gates", "No approval gates or dry-run preview detected. Agents can execute irreversible operations with no confirmation. Deploy plan-execute separation with mandatory human approval for destructive actions."),
    "D8": ("Implement cryptographic agent identity", "No agent registry or identity tokens. Agents are anonymous with unrestricted tool access. Deploy an agent passport system with delegation chains and lifecycle state management."),
    "D9": ("Deploy behavioral detection and kill switch", "No behavioral baselines, no anomaly detection, no auto-suspend capability. A compromised agent can operate indefinitely. Salami slicing across sessions is undetectable."),
    "D10": ("Add prompt injection detection", "No prompt injection or jailbreak prevention detected. Deploy content filtering at the prompt layer to catch injection attacks before they reach agent logic."),
    "D11": ("Integrate cloud security posture management", "No cloud/platform security integration. Add SSO/IdP, SIEM integration, and marketplace-ready configurations for enterprise deployment."),
    "D12": ("Add LLM observability and cost tracking", "No model analytics or cost monitoring. Deploy observability tools that track token usage, latency, and cost per agent operation."),
    "D13": ("Implement data recovery and rollback", "No rollback or undo capability for agent actions. A single bad tool call is permanent. Deploy point-in-time recovery with action journaling."),
    "D14": ("Enable compliance evidence generation", "No SOC2/ISO evidence or regulatory mapping. For EU AI Act Article 14 and BOI 364 compliance (deadline August 2026), deploy automated compliance reporting with audit trail verification."),
    "D15": ("Add post-execution result verification", "No result validation after tool execution. Deploy PASS/FAIL verdicts with failure fingerprinting to catch silent failures and unexpected side effects."),
    "D16": ("Implement data flow governance", "No taint labels or data classification. Sensitive data can flow freely between tools and agents. Deploy cross-tool leakage prevention with data classification tags."),
    "D17": ("Add adversarial resilience testing", "No trap defense or adversarial testing detected. Deploy content injection tests, RAG poisoning detection, and behavioral trap simulation per the DeepMind AI Agent Traps framework."),
}

# --- Risk tag descriptions for MCP tools ---
_RISK_TAG_DESCRIPTIONS = {
    "destructive": "Can delete, destroy, or irreversibly modify data",
    "financial": "Handles payments, transfers, or financial operations",
    "exfiltration": "Can send data externally via email, webhook, or upload",
    "write-access": "Can create, modify, or execute operations",
    "read-only": "Read-only access with low risk profile",
}


def write_html_report(result: ScanResult, output_path: Path) -> None:
    """Write self-contained HTML report. No external requests."""
    html = _build_html(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def _build_html(result: ScanResult) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    sections = [
        _header(result, timestamp),
        _scan_scope(result),
        _hero(result),
        _summary_grid(result),
        _discovered_tools(result),
        _governance_detection(result),
        _detected_solutions_table(result),
        _findings_section(result),
        _recommendations(result),
        _email_form(result),
        _footer(),
    ]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Warden Governance Report — {result.total_score}/100</title>
{_css()}
</head>
<body>
<div class="hdr">
{''.join(sections[:1])}
</div>
{sections[1]}
<div class="body">
{''.join(sections[2:])}
</div>
{_js()}
</body>
</html>"""


def _css() -> str:
    return """<style>
:root {
  --bg:#0a0c10;--surface:#10131a;--surface2:#161b24;
  --border:#1e2535;--border2:#252d3d;
  --text:#e2e8f0;--text2:#94a3b8;--muted:#4b5563;
  --critical:#ff3b3b;--high:#ff8c00;--medium:#f5c518;--low:#4ade80;
  --info:#60a5fa;--purple:#a78bfa;--teal:#00bcd4;
  --mono:'SF Mono','Cascadia Code','JetBrains Mono','Fira Code',Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--sans);background:var(--bg);color:var(--text);font-size:14px;line-height:1.6}

.hdr{background:var(--surface);border-bottom:1px solid var(--border);padding:22px 40px;display:flex;align-items:flex-start;justify-content:space-between;gap:24px;flex-wrap:wrap}
.logo{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.logo-name{font-family:var(--mono);font-size:15px;font-weight:700;color:var(--info);letter-spacing:1px}
.logo-tag{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:2px;text-transform:uppercase}
.meta{font-family:var(--mono);font-size:11px;color:var(--text2);line-height:2.1}
.meta strong{color:var(--text)}
.priv{font-family:var(--mono);font-size:10px;color:var(--text2);background:rgba(96,165,250,.06);border:1px solid rgba(96,165,250,.15);border-radius:4px;padding:8px 12px;line-height:2;max-width:280px}

.body{max-width:1100px;margin:0 auto;padding:28px 40px 80px;display:flex;flex-direction:column;gap:22px}

/* --- Section cards --- */
.sec{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden}
.sec-head{display:flex;align-items:center;justify-content:space-between;padding:13px 24px;border-bottom:1px solid var(--border);background:rgba(255,255,255,.01)}
.sec-title{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:var(--text2)}
.sec-count{font-family:var(--mono);font-size:11px;color:var(--muted)}
.sec-body{padding:0}

/* --- Hero --- */
.hero{display:grid;grid-template-columns:auto 1fr;gap:32px;align-items:start;padding:28px 32px}
.hero-left{display:flex;flex-direction:column;align-items:center;gap:12px}
.gauge{position:relative;width:150px;height:150px}
.gauge svg{transform:rotate(-90deg)}
.gauge-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.g-num{font-family:var(--mono);font-size:38px;font-weight:700;line-height:1}
.g-denom{font-family:var(--mono);font-size:12px;color:var(--muted)}
.g-raw{font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:2px}
.lvl-badge{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:2px;padding:4px 14px;border-radius:20px}
.lvl-governed{background:rgba(74,222,128,.1);color:var(--low);border:1px solid rgba(74,222,128,.3)}
.lvl-partial{background:rgba(255,140,0,.1);color:var(--high);border:1px solid rgba(255,140,0,.3)}
.lvl-at_risk{background:rgba(255,59,59,.1);color:var(--critical);border:1px solid rgba(255,59,59,.3)}
.lvl-ungoverned{background:rgba(255,59,59,.1);color:var(--critical);border:1px solid rgba(255,59,59,.3)}

.dims{display:flex;flex-direction:column;gap:0}
.dim-group{font-family:var(--mono);font-size:9px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;padding:10px 0 4px;border-top:1px solid var(--border);margin-top:4px}
.dim-group:first-child{border-top:none;margin-top:0;padding-top:0}
.dim-row{display:grid;grid-template-columns:190px 1fr 58px;align-items:center;gap:10px;padding:3px 0}
.dim-label{font-size:12px;color:var(--text2);display:flex;align-items:center;gap:5px}
.bar-track{height:5px;background:var(--border2);border-radius:3px;overflow:hidden}
.bar-fill{height:100%;border-radius:3px}
.dim-val{font-family:var(--mono);font-size:11px;color:var(--text2);text-align:right}
.dim-details{cursor:pointer}.dim-details summary{list-style:none}.dim-details summary::-webkit-details-marker{display:none}
.dim-details summary .dim-label::after{content:'\\25B8';font-size:9px;color:var(--muted);transition:transform 0.15s}
.dim-details[open] summary .dim-label::after{transform:rotate(90deg)}
.dim-detail-body{padding:4px 0 8px 12px;border-left:2px solid var(--border2);margin:2px 0 6px 8px}
.dim-detail-item{font-size:11px;color:var(--text2);padding:2px 0;line-height:1.5}
.dim-subtotal{font-family:var(--mono);font-size:10px;color:var(--info);text-align:right;margin:3px 0}
.caveat{font-size:11px;color:var(--text2);font-style:italic;margin-top:14px;padding-top:12px;border-top:1px solid var(--border)}

/* --- Summary grid --- */
.sum-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--border)}
.sum-cell{background:var(--surface);padding:18px 22px}
.sum-label{font-family:var(--mono);font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px}
.sum-val{font-family:var(--mono);font-size:24px;font-weight:700;line-height:1;margin-bottom:4px}
.sum-sub{font-size:11px;color:var(--text2)}

/* --- Discovered tools --- */
.tool-item{display:grid;grid-template-columns:22px 1fr;gap:0 14px;padding:16px 24px;border-bottom:1px solid var(--border);align-items:start}
.tool-item:last-child{border-bottom:none}
.rdot{width:9px;height:9px;border-radius:50%;margin-top:6px;flex-shrink:0}
.rdot.critical{background:var(--critical);box-shadow:0 0 5px var(--critical)}
.rdot.high{background:var(--high)}
.rdot.medium{background:var(--medium)}
.rdot.low{background:var(--low)}
.rdot.info{background:var(--info)}
.tname{font-family:var(--mono);font-size:13px;font-weight:600;margin-bottom:3px;display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.tdesc{font-size:13px;color:var(--text2);margin-bottom:7px;line-height:1.5}
.ttags{display:flex;gap:5px;flex-wrap:wrap}
.tag{font-family:var(--mono);font-size:10px;padding:2px 7px;border-radius:3px;border:1px solid}
.tag.d{color:var(--critical);border-color:rgba(255,59,59,.3);background:rgba(255,59,59,.06)}
.tag.f{color:var(--high);border-color:rgba(255,140,0,.3);background:rgba(255,140,0,.06)}
.tag.e{color:var(--high);border-color:rgba(255,140,0,.3);background:rgba(255,140,0,.06)}
.tag.w{color:var(--medium);border-color:rgba(245,197,24,.3);background:rgba(245,197,24,.06)}
.tag.r{color:var(--low);border-color:rgba(74,222,128,.3);background:rgba(74,222,128,.06)}
.tag.u{color:var(--critical);border-color:rgba(255,59,59,.3);background:rgba(255,59,59,.06)}
.tag.n{color:var(--info);border-color:rgba(96,165,250,.3);background:rgba(96,165,250,.06)}
.rbadge{font-family:var(--mono);font-size:10px;font-weight:700;padding:2px 7px;border-radius:3px;letter-spacing:1px}
.rbadge.critical{background:rgba(255,59,59,.12);color:var(--critical)}
.rbadge.high{background:rgba(255,140,0,.12);color:var(--high)}
.rbadge.medium{background:rgba(245,197,24,.12);color:var(--medium)}
.rbadge.low{background:rgba(74,222,128,.12);color:var(--low)}

/* --- Governance detection --- */
.gov-row{display:flex;align-items:flex-start;gap:14px;padding:15px 24px;border-bottom:1px solid var(--border)}
.gov-row:last-child{border-bottom:none}
.gov-ico{font-size:16px;flex-shrink:0;width:22px;margin-top:2px}
.gov-name{font-family:var(--mono);font-size:13px;font-weight:600;margin-bottom:3px}
.gov-desc{font-size:12px;color:var(--text2);margin-bottom:7px;line-height:1.5}
.gov-pts{font-family:var(--mono);font-size:12px;font-weight:700;padding:3px 10px;border-radius:4px;flex-shrink:0;white-space:nowrap}
.gov-pts.pos{color:var(--low);background:rgba(74,222,128,.1)}
.gov-pts.zero{color:var(--muted);background:var(--border)}

/* --- Findings --- */
.fg-hdr{font-family:var(--mono);font-size:12px;font-weight:700;letter-spacing:1px;cursor:pointer;display:flex;align-items:center;gap:8px;padding:8px 24px;user-select:none}
.fg-cnt{padding:2px 9px;border-radius:10px;font-size:11px}
.fg-body{display:none;padding:0 24px 8px}.fg-body.open{display:block}
.f-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px 16px;margin-bottom:6px;cursor:pointer}
.f-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.f-sev{font-family:var(--mono);font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;white-space:nowrap}
.f-dim{font-family:var(--mono);font-size:10px;color:var(--text2);background:var(--surface);padding:2px 6px;border-radius:3px}
.f-msg{font-size:13px;color:var(--text);margin:6px 0 2px}
.f-loc{font-family:var(--mono);font-size:11px;color:var(--info)}
.f-detail{font-size:12px;color:var(--text2);margin-top:8px;padding-top:8px;border-top:1px solid var(--border);display:none}
.f-card.exp .f-detail{display:block}
.f-rem{color:var(--low)}
.f-compliance{font-family:var(--mono);font-size:10px;color:var(--text2);margin-top:4px}
.f-compliance span{background:rgba(96,165,250,.08);color:var(--info);padding:1px 6px;border-radius:3px;margin-right:4px}
.arrow{transition:transform .2s;display:inline-block}.arrow.open{transform:rotate(90deg)}

/* --- Recommendations --- */
.rec{display:grid;grid-template-columns:30px 1fr;gap:0 14px;padding:18px 24px;border-bottom:1px solid var(--border);align-items:start}
.rec:last-child{border-bottom:none}
.rec-n{font-family:var(--mono);font-size:13px;font-weight:700;color:var(--info);margin-top:2px}
.rec-title{font-weight:600;margin-bottom:5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.rec-body{font-size:13px;color:var(--text2);line-height:1.6}
.rec-pts{font-family:var(--mono);font-size:11px;color:var(--low);padding:2px 8px;border:1px solid rgba(74,222,128,.25);border-radius:3px;background:rgba(74,222,128,.06)}

/* --- Workaround tax --- */
.workaround-box{margin-top:14px;padding:16px 20px;background:rgba(255,140,0,0.05);border:1px solid rgba(255,140,0,0.25);border-left:3px solid var(--high);border-radius:6px}
.workaround-label{font-family:var(--mono);font-size:10px;color:var(--high);letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
.workaround-text{font-size:13px;color:var(--text2);line-height:1.6}
.workaround-text strong{color:var(--text)}

/* --- Comparison card --- */
.cmp{border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-top:18px}
.cmp-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--border)}
.cmp-col{padding:18px 20px}
.cmp-cur{background:var(--surface2)}
.cmp-sr{background:#090f0a;border-left:2px solid rgba(74,222,128,.35)}
.cmp-lbl{font-family:var(--mono);font-size:10px;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px}
.cmp-lbl.c{color:var(--muted)}
.cmp-lbl.s{color:rgba(74,222,128,.6)}
.cmp-score{font-family:var(--mono);font-size:30px;font-weight:700;line-height:1}
.cmp-score.c{color:var(--critical)}
.cmp-score.s{color:var(--low)}
.cmp-denom{font-family:var(--mono);font-size:13px;color:var(--muted)}
.cmp-lvl{font-family:var(--mono);font-size:10px;letter-spacing:1px;margin-top:4px;margin-bottom:14px}
.cmp-lvl.c{color:var(--critical)}
.cmp-lvl.w{color:var(--medium)}
.cmp-lvl.s{color:var(--low)}
.cmp-grp{font-family:var(--mono);font-size:9px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;padding:8px 0 3px;border-top:1px solid var(--border);margin-top:4px}
.cmp-grp:first-child{border-top:none;margin-top:0;padding-top:0}
.cmp-dim{display:grid;grid-template-columns:140px 1fr 50px;align-items:center;gap:8px;padding:3px 0;font-size:11px}
.cmp-dim-lbl{color:var(--text2)}
.cmp-bt{height:5px;background:var(--border);border-radius:3px;overflow:hidden}
.cmp-bf{height:100%;border-radius:3px}
.cmp-val{font-family:var(--mono);font-size:10px;text-align:right}
.cmp-val.c{color:var(--muted)}
.cmp-val.s{color:var(--low);font-weight:700}
.delta{color:rgba(74,222,128,.5);font-weight:400;font-size:9px}
.cmp-foot{background:rgba(74,222,128,.04);border-top:1px solid var(--border);padding:10px 20px;font-family:var(--mono);font-size:11px;color:var(--text2);display:flex;justify-content:space-between;align-items:center}
.cmp-foot a{color:var(--info);text-decoration:none}
.cmp-delta{font-family:var(--mono);font-size:14px;font-weight:700;color:var(--low)}

/* --- Solutions table --- */
.sol-table{border-collapse:collapse;font-size:12px;font-family:var(--mono);white-space:nowrap;width:100%}
.sol-table th{text-align:center;padding:8px 12px;color:var(--text2);font-weight:600;border-bottom:1px solid var(--border2)}
.sol-table th:first-child{text-align:left}
.sol-table td{text-align:center;padding:7px 12px;border-bottom:1px solid var(--border)}
.sol-table td:first-child{text-align:left;color:var(--text2)}
.sol-table tr.sr{background:rgba(74,222,128,0.06)}
.sol-table tr.sr td{color:var(--low);font-weight:700}
.sol-table tfoot td{font-weight:700;border-top:2px solid var(--border2)}

/* --- Email form --- */
.email-wrap{display:grid;grid-template-columns:1fr auto;gap:24px;padding:28px 32px;align-items:center}
.email-info{font-size:13px;color:var(--text2);line-height:1.6}
.email-cols{display:flex;gap:32px;margin-top:16px}
.email-col-hdr{font-family:var(--mono);font-size:10px;letter-spacing:1px;margin-bottom:6px}
.email-col li{list-style:none;font-size:12px;color:var(--text2);padding:2px 0}
.email-form{background:var(--surface2);border:1px solid var(--border2);border-radius:8px;padding:24px;min-width:280px;display:flex;flex-direction:column;gap:10px}
.email-input{background:#0a0c10;border:1px solid var(--border2);border-radius:5px;padding:10px 14px;font-family:var(--mono);font-size:13px;color:var(--text);outline:none;width:100%}
.email-input:focus{border-color:var(--info)}
.email-btn{background:var(--info);color:#000;border:none;border-radius:5px;padding:10px 20px;font-family:var(--mono);font-size:12px;font-weight:700;letter-spacing:1px;cursor:pointer;width:100%;transition:background 0.2s}
.email-btn:hover{background:#93c5fd}
.email-bar{padding:12px 32px;background:rgba(0,0,0,0.2);border-top:1px solid var(--border);font-size:12px;color:var(--text2);display:flex;align-items:center;justify-content:space-between}

/* --- Footer --- */
.foot{text-align:center;padding:28px 40px;font-family:var(--mono);font-size:11px;color:var(--text2);line-height:2.2;max-width:1100px;margin:0 auto}
.foot a{color:var(--info);text-decoration:none}
.foot-cta{display:inline-block;margin-top:12px;background:#fff;color:#000 !important;padding:10px 24px;border-radius:8px;font-weight:700;font-size:13px;text-decoration:none !important;letter-spacing:0.5px}
.foot-cta:hover{background:#e2e8f0;color:#000 !important}
.foot-priv{color:var(--muted);font-size:10px;margin-top:8px}

/* --- Responsive --- */
@media(max-width:768px){
  .hero{grid-template-columns:1fr}
  .sum-grid{grid-template-columns:repeat(2,1fr)}
  .cmp-grid{grid-template-columns:1fr}
  .dim-row{grid-template-columns:140px 1fr 50px}
  .email-wrap{grid-template-columns:1fr}
  .hdr{flex-direction:column}
}
</style>"""


def _js() -> str:
    return """<script>
function toggleGroup(id){
  var b=document.getElementById(id);
  var a=document.getElementById(id+'-arrow');
  if(b){b.classList.toggle('open');if(a)a.classList.toggle('open')}
}
function toggleFinding(el){el.classList.toggle('exp')}
function submitEmail(btn){
  var input=btn.parentElement.querySelector('input[type=email]');
  var status=document.getElementById('email-status');
  var email=input.value.trim();
  if(!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email)){
    status.style.color='var(--critical)';
    status.textContent='Please enter a valid email address.';
    return;
  }
  btn.disabled=true;btn.textContent='SENDING...';
  var data=JSON.parse(document.getElementById('warden-data').textContent);
  data.email=email;
  var company=document.getElementById('warden-company');
  if(company&&company.value)data.company=company.value;
  fetch('https://api.whitefin.ai/v1/warden/submit',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(data)
  }).then(function(r){
    if(r.ok){btn.style.background='var(--low)';btn.style.color='#000';btn.textContent='\\u2713 SENT';input.disabled=true;
      status.style.color='var(--low)';status.textContent='Check your inbox \\u2014 report and guide on their way.';}
    else{btn.textContent='SEND REPORT \\u2192';btn.disabled=false;
      status.style.color='var(--critical)';status.textContent='Failed to send. Try again.';}
  }).catch(function(){btn.textContent='SEND REPORT \\u2192';btn.disabled=false;
    status.style.color='var(--critical)';status.textContent='Network error. Try again.';});
}
</script>"""


def _header(result: ScanResult, timestamp: str) -> str:
    return f"""
  <div>
    <div class="logo">
      <span style="font-size:20px">&#129416;</span>
      <div><div class="logo-name">WARDEN</div><div class="logo-tag">AI Agent Governance Report</div></div>
    </div>
    <div class="meta">
      <strong>Scan path:</strong> {_esc(result.target_path)}<br>
      <strong>Scanned:</strong> {timestamp}<br>
      <strong>Warden:</strong> v{__version__} &middot; Scoring model v{__scoring_model__} &middot; {len(ALL_DIMENSIONS)} dimensions (weighted) &middot; {TOTAL_RAW_MAX} pts
    </div>
  </div>
  <div class="priv">&#128274; Privacy guarantee<br>All data collected locally &mdash; nothing left this machine.<br>API keys: partial hashes only.<br>Log content: never stored.</div>"""


def _scan_scope(result: ScanResult) -> str:
    """Scan scope bar — file counts and layer summary."""
    py = result.file_counts.get("python", 0)
    js = result.file_counts.get("js", 0)
    other = result.file_counts.get("other", 0)
    total = py + js + other

    parts = []
    if py:
        parts.append(f"{py:,} Python")
    if js:
        parts.append(f"{js:,} JS/TS")
    if other:
        parts.append(f"{other:,} other")

    file_str = f"{total:,} files" + (f" ({' &middot; '.join(parts)})" if parts else "")

    # Count unique scanner layers that produced findings
    layers = {f.layer for f in result.findings}
    layer_count = len(layers) if layers else 0

    dirname = Path(result.target_path).name or result.target_path

    return f"""
  <div style="font-family:var(--mono);font-size:11px;color:var(--text2);padding:10px 32px;border-bottom:1px solid var(--border);background:var(--surface)">
    &#128202; Scanned {file_str} in <strong style="color:var(--text)">{_esc(dirname)}</strong> across {layer_count} scan layers
  </div>"""


def _hero(result: ScanResult) -> str:
    score = result.total_score
    level = result.level
    color = LEVEL_COLORS.get(level, "#999")
    lvl_cls = f"lvl-{level.value.lower()}"

    # Raw score
    raw_total = sum(ds.raw for ds in result.dimension_scores.values())

    # SVG gauge — solid color, no gradient
    r = 60
    circ = 2 * 3.14159 * r
    dash = (score / 100) * circ
    gauge_color = color

    gauge_svg = f"""<div class="gauge">
      <svg width="150" height="150" viewBox="0 0 150 150">
        <circle cx="75" cy="75" r="{r}" fill="none" stroke="{_esc('#1e2535')}" stroke-width="8"/>
        <circle cx="75" cy="75" r="{r}" fill="none" stroke="{gauge_color}" stroke-width="8" stroke-dasharray="{dash:.0f} {circ:.0f}" stroke-linecap="round"/>
      </svg>
      <div class="gauge-center">
        <div class="g-num" style="color:{color}">{score}</div>
        <div class="g-denom">/ 100</div>
        <div class="g-raw">{raw_total} / {TOTAL_RAW_MAX} raw</div>
      </div>
    </div>"""

    # Build per-dimension findings index for expandable details
    dim_findings: dict[str, list] = {}
    for f in result.findings:
        dim_findings.setdefault(f.dimension, []).append(f)

    # Dimension bars grouped
    dim_html = []
    for group_name, dims in GROUPS.items():
        grp_raw = 0
        grp_max = 0
        for dim in dims:
            ds = result.dimension_scores.get(dim.id)
            grp_raw += ds.raw if ds else 0
            grp_max += ds.max if ds else dim.max_score
        dim_html.append(f'<div class="dim-group">{_esc(group_name)} ({grp_raw} / {grp_max})</div>')
        for dim in dims:
            ds = result.dimension_scores.get(dim.id)
            raw = ds.raw if ds else 0
            mx = ds.max if ds else dim.max_score
            pct = round(raw / mx * 100) if mx else 0
            bar_color = _pct_color(pct)
            val_style = ' style="color:var(--critical)"' if pct == 0 and mx > 0 else ""

            # Build expandable detail content
            findings_for_dim = dim_findings.get(dim.id, [])
            signals = ds.signals if ds else []
            detail_items = []
            for sig in signals:
                detail_items.append(f'<div class="dim-detail-item">{_esc(sig)}</div>')
            for ff in findings_for_dim[:5]:
                sev_color = SEVERITY_COLORS.get(ff.severity, "#999")
                detail_items.append(f'<div class="dim-detail-item"><span style="color:{sev_color};font-weight:600">{ff.severity.value}</span> {_esc(ff.message[:120])}</div>')
            if len(findings_for_dim) > 5:
                detail_items.append(f'<div class="dim-detail-item" style="color:var(--text2)">+ {len(findings_for_dim) - 5} more findings</div>')

            if detail_items:
                detail_html = f'<details class="dim-details"><summary class="dim-row"><div class="dim-label">{dim.id} {_esc(dim.name)}</div><div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{bar_color}"></div></div><div class="dim-val"{val_style}>{raw} / {mx}</div></summary><div class="dim-detail-body">{"".join(detail_items)}</div></details>'
            else:
                detail_html = f'<div class="dim-row"><div class="dim-label">{dim.id} {_esc(dim.name)}</div><div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{bar_color}"></div></div><div class="dim-val"{val_style}>{raw} / {mx}</div></div>'
            dim_html.append(detail_html)

    caveat = '<div class="caveat">Score reflects only what Warden can observe locally. Undetected controls are scored as 0, not assumed good. Dimensions are weighted by governance impact. Methodology: <a href="https://github.com/whitefinsec/warden/blob/main/SCORING.md" style="color:var(--info);text-decoration:none">SCORING.md</a></div>'

    return f"""
  <div class="sec">
    <div class="hero">
      <div class="hero-left">
        {gauge_svg}
        <div class="lvl-badge {lvl_cls}">{level.value.replace('_', ' ')}</div>
      </div>
      <div class="dims">
        {''.join(dim_html)}
        {caveat}
      </div>
    </div>
  </div>"""


def _summary_grid(result: ScanResult) -> str:
    has_mcp = bool(result.mcp_tools)
    secrets = sum(1 for f in result.findings if f.layer == 4)
    gaps = sum(1 for ds in result.dimension_scores.values() if ds.pct == 0)
    refs = set()
    for f in result.findings:
        if f.compliance.eu_ai_act:
            refs.add(f.compliance.eu_ai_act)
        if f.compliance.owasp_llm:
            refs.add(f.compliance.owasp_llm)
        if f.compliance.mitre_atlas:
            refs.add(f.compliance.mitre_atlas)

    sec_sub = "In source code" if secrets > 0 else "None detected"
    gap_sub = f"of {len(ALL_DIMENSIONS)} dimensions" if gaps > 0 else "All dimensions covered"

    cells = []
    if has_mcp:
        mcp_servers = len({t.server for t in result.mcp_tools})
        mcp_total = len(result.mcp_tools)
        crit_tools = sum(1 for t in result.mcp_tools if t.severity == Severity.CRITICAL)
        cells.append(f'<div class="sum-cell"><div class="sum-label">MCP Servers</div><div class="sum-val" style="color:var(--medium)">{mcp_servers}</div><div class="sum-sub">{mcp_total} tools exposed</div></div>')
        cells.append(f'<div class="sum-cell"><div class="sum-label">Critical Tools</div><div class="sum-val" style="color:var(--critical)">{crit_tools}</div><div class="sum-sub">{"No approval gate" if crit_tools > 0 else "None detected"}</div></div>')
    else:
        # No MCP — show findings-focused cells
        total_findings = len(result.findings)
        crits = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
        highs = sum(1 for f in result.findings if f.severity == Severity.HIGH)
        cells.append(f'<div class="sum-cell"><div class="sum-label">Total Findings</div><div class="sum-val" style="color:var(--high)">{total_findings:,}</div><div class="sum-sub">{crits} CRITICAL &middot; {highs} HIGH</div></div>')
        detected = [c for c in result.competitors if c.confidence != "low"]
        det_names = ", ".join(c.display_name for c in detected[:3]) if detected else "None detected"
        cells.append(f'<div class="sum-cell"><div class="sum-label">Tools Detected</div><div class="sum-val" style="color:var(--low)">{len(detected)}</div><div class="sum-sub">{_esc(det_names)}</div></div>')

    cells.append(f'<div class="sum-cell"><div class="sum-label">Credentials</div><div class="sum-val" style="color:var(--high)">{secrets}</div><div class="sum-sub">{_esc(sec_sub)}</div></div>')
    cells.append(f'<div class="sum-cell"><div class="sum-label">Governance Gaps</div><div class="sum-val" style="color:var(--critical)">{gaps}</div><div class="sum-sub">{_esc(gap_sub)}</div></div>')
    cells.append(f'<div class="sum-cell"><div class="sum-label">Compliance Refs</div><div class="sum-val" style="color:var(--info)">{len(refs)}</div><div class="sum-sub">EU AI Act / OWASP / MITRE</div></div>')

    return f"""
  <div class="sec">
    <div class="sum-grid">
      {''.join(cells)}
    </div>
  </div>"""


def _discovered_tools(result: ScanResult) -> str:
    if not result.mcp_tools:
        return ""

    tools_sorted = sorted(result.mcp_tools, key=lambda t: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(t.severity.value, 4))
    crit_count = sum(1 for t in tools_sorted if t.severity == Severity.CRITICAL)
    high_count = sum(1 for t in tools_sorted if t.severity == Severity.HIGH)
    count_label = f"{len(tools_sorted)} total"
    if crit_count:
        count_label += f" &middot; {crit_count} CRITICAL"
    if high_count:
        count_label += f" &middot; {high_count} HIGH"

    top_tools = tools_sorted[:4]
    rest_count = len(tools_sorted) - 4

    items = []
    for t in top_tools:
        sev_low = t.severity.value.lower()
        desc = _tool_description(t)
        tags_html = []
        for tag in t.risk_tags:
            tag_cls = {"destructive": "d", "financial": "f", "exfiltration": "e", "write-access": "w", "read-only": "r"}.get(tag, "n")
            tags_html.append(f'<span class="tag {tag_cls}">{_esc(tag)}</span>')
        if not t.has_auth:
            tags_html.append('<span class="tag u">no auth</span>')
        if not t.has_schema:
            tags_html.append('<span class="tag u">no schema</span>')

        items.append(f"""<div class="tool-item">
  <div class="rdot {sev_low}"></div>
  <div>
    <div class="tname"><span class="rbadge {sev_low}">{t.severity.value}</span> {_esc(t.name)} <span style="font-family:var(--mono);font-size:10px;color:var(--muted)">{_esc(t.server)} MCP</span></div>
    <div class="tdesc">{_esc(desc)}</div>
    <div class="ttags">{''.join(tags_html)}</div>
  </div>
</div>""")

    if rest_count > 0:
        items.append(f"""<div class="tool-item">
  <div class="rdot info"></div>
  <div>
    <div class="tname" style="color:var(--muted)">+ {rest_count} additional tools &mdash; LOW / MEDIUM risk</div>
    <div class="tdesc" style="color:var(--muted)">Full list in warden_report.json</div>
  </div>
</div>""")

    return f"""
  <div class="sec">
    <div class="sec-head"><span class="sec-title">&#9874; Discovered Tools</span><span class="sec-count">{count_label}</span></div>
    {''.join(items)}
  </div>"""


def _tool_description(tool) -> str:
    """Generate human-readable description from risk tags and metadata."""
    parts = []
    tags = set(tool.risk_tags)

    if "financial" in tags and "destructive" in tags:
        parts.append("Financial tool with destructive capabilities.")
    elif "financial" in tags:
        parts.append("Financial operation tool.")
    elif "destructive" in tags:
        parts.append("Destructive tool that can delete or irreversibly modify data.")
    elif "exfiltration" in tags:
        parts.append("Can send data externally. Classic exfiltration vector.")
    elif "write-access" in tags:
        parts.append("Write-access tool that can create or modify resources.")
    elif "read-only" in tags:
        parts.append("Read-only tool with limited risk profile.")
    else:
        parts.append("Tool with unclassified risk profile.")

    if not tool.has_auth:
        parts.append("No authentication configured.")
    if not tool.has_schema:
        parts.append("No input schema defined.")
    if "destructive" in tags or "financial" in tags:
        parts.append("Agent can call this without any human confirmation.")

    return " ".join(parts)


def _governance_detection(result: ScanResult) -> str:
    detected = [c for c in result.competitors if c.confidence != "low"]

    # Build governance rows: detected tools + zero-scoring dimensions
    rows = []

    for c in detected:
        signal_str = c.signals[0] if c.signals else "configuration file"
        # Build capability tags
        strengths = c.strengths[:4] if c.strengths else []
        weaknesses = c.weaknesses[:4] if c.weaknesses else []
        tag_html = []
        for s in strengths:
            tag_html.append(f'<span class="tag r">{_esc(s)} &#10003;</span>')
        for w in weaknesses:
            tag_html.append(f'<span class="tag u">{_esc(w)} &#10007;</span>')

        rows.append(f"""<div class="gov-row">
  <div class="gov-ico">&#9989;</div>
  <div style="flex:1">
    <div class="gov-name">{_esc(c.display_name)} &mdash; detected</div>
    <div class="gov-desc">Detected via {_esc(signal_str)}. {_esc(c.category.replace('_', ' ').title())} &mdash; {_esc(c.gtm_signal) if c.gtm_signal else 'governance tool detected in project.'}</div>
    <div style="display:flex;gap:5px;flex-wrap:wrap">{' '.join(tag_html)}</div>
  </div>
  <div class="gov-pts pos">{c.warden_score} / {TOTAL_RAW_MAX}</div>
</div>""")

    # Zero-scoring dimensions
    for dim in ALL_DIMENSIONS:
        ds = result.dimension_scores.get(dim.id)
        raw = ds.raw if ds else 0
        mx = ds.max if ds else dim.max_score
        if raw == 0 and mx > 0:
            rows.append(f"""<div class="gov-row">
  <div class="gov-ico">&#10060;</div>
  <div style="flex:1">
    <div class="gov-name">{dim.id}: {_esc(dim.name)} &mdash; none detected</div>
    <div class="gov-desc">{_esc(dim.description)}</div>
  </div>
  <div class="gov-pts zero">0 / {mx} pts</div>
</div>""")

    if not rows:
        return ""

    dim_count = len(ALL_DIMENSIONS)
    tool_count = len(detected)

    return f"""
  <div class="sec">
    <div class="sec-head"><span class="sec-title">&#128737; Governance Layer Detection</span><span class="sec-count">{tool_count} tool{'s' if tool_count != 1 else ''} detected &middot; {dim_count} dimensions</span></div>
    {''.join(rows)}
  </div>"""


def _detected_solutions_table(result: ScanResult) -> str:
    """Solutions comparison — rows=tools, cols=D1-D17 + /235 + /100."""
    detected = [c for c in result.competitors if c.confidence != "low" and c.id != "sharkrouter"]

    # Column headers: Tool | D1 | D2 | ... | D17 | /235 | /100
    dim_ths = ""
    for dim in ALL_DIMENSIONS:
        dim_ths += f'<th style="text-align:center;padding:6px 4px;color:var(--muted);font-weight:400" title="{_esc(dim.name)} /{dim.max_score}">{dim.id}</th>'

    # Max pts sub-header row
    max_pts_cells = '<th style="text-align:left;padding:3px 10px;font-size:10px;color:var(--muted)">Max pts</th>'
    for dim in ALL_DIMENSIONS:
        max_pts_cells += f'<th style="text-align:center;padding:3px 4px;font-size:10px;color:var(--muted)">{dim.max_score}</th>'
    max_pts_cells += f'<th style="text-align:center;padding:3px 4px;font-size:10px;color:var(--muted);border-left:1px solid var(--border2)">{TOTAL_RAW_MAX}</th><th></th>'

    # --- WhiteFin row (always first, green highlight) ---
    shark_raw_total = round(_SHARKROUTER_SCORE / 100 * TOTAL_RAW_MAX)
    shark_cells = '<td style="padding:7px 10px;color:var(--low);font-weight:700">WhiteFin</td>'
    for dim in ALL_DIMENSIONS:
        est = round(dim.max_score * (_SHARKROUTER_SCORE / 100))
        est = min(est, dim.max_score)
        shark_cells += f'<td style="text-align:center;color:var(--low)">{est}</td>'
    shark_cells += f'<td style="text-align:center;color:var(--low);font-weight:700;border-left:1px solid var(--border2)">{shark_raw_total}</td>'
    shark_cells += f'<td style="text-align:center;color:var(--low);font-weight:700">{_SHARKROUTER_SCORE}</td>'
    shark_row = f'<tr style="background:rgba(74,222,128,0.06);border-bottom:2px solid rgba(74,222,128,0.2)">{shark_cells}</tr>'

    # --- Your Scan row (actual per-dim scores) ---
    raw_total = sum(ds.raw for ds in result.dimension_scores.values())
    scan_color = LEVEL_COLORS.get(result.level, "#999")
    scan_cells = f'<td style="padding:7px 10px;color:{scan_color};font-weight:700">Your Scan</td>'
    for dim in ALL_DIMENSIONS:
        ds = result.dimension_scores.get(dim.id)
        raw = ds.raw if ds else 0
        mx = ds.max if ds else dim.max_score
        pct = round(raw / mx * 100) if mx else 0
        cell_color = _pct_color(pct)
        style = f'color:{cell_color}' if pct < 80 else 'color:var(--low)'
        if raw == 0 and mx > 0:
            style = 'color:var(--critical)'
        scan_cells += f'<td style="text-align:center;{style}">{raw}</td>'
    scan_cells += f'<td style="text-align:center;font-weight:700;border-left:1px solid var(--border2);color:{scan_color}">{raw_total}</td>'
    scan_cells += f'<td style="text-align:center;font-weight:700;color:{scan_color}">{result.total_score}</td>'
    scan_row = f'<tr style="border-bottom:1px solid var(--border)">{scan_cells}</tr>'

    # --- Detected tool rows (only totals, dims show —) ---
    det_rows = []
    for c in detected:
        comp_raw = c.warden_score  # This is actually the raw-ish estimate
        comp_norm = round(c.warden_score / TOTAL_RAW_MAX * 100)
        det_cells = f'<td style="padding:7px 10px">{_esc(c.display_name)}</td>'
        for dim in ALL_DIMENSIONS:
            det_cells += '<td style="text-align:center;color:var(--muted)">&mdash;</td>'
        det_cells += f'<td style="text-align:center;font-weight:700;border-left:1px solid var(--border2)">{comp_raw}</td>'
        det_cells += f'<td style="text-align:center;font-weight:700">{comp_norm}</td>'
        det_rows.append(f'<tr style="border-bottom:1px solid var(--border)">{det_cells}</tr>')

    dim_count = len(ALL_DIMENSIONS)
    tool_count = 2 + len(detected)  # shark + scan + detected

    disclaimer = '<div style="font-size:11px;color:var(--muted);font-style:italic;padding:12px 24px;font-family:var(--mono)">WhiteFin per-dimension scores are proportional estimates from total score. Detected tool scores are totals only (per-dimension breakdown not available). Methodology: <a href="https://github.com/whitefinsec/warden/blob/main/SCORING.md" style="color:var(--info);text-decoration:none">SCORING.md</a></div>'

    return f"""
  <div class="sec">
    <div class="sec-head"><span class="sec-title">&#128202; Solutions Comparison</span><span class="sec-count">{tool_count} rows &middot; {dim_count} dimensions &middot; {TOTAL_RAW_MAX} max pts</span></div>
    <div style="padding:16px 24px 8px;overflow-x:auto">
      <table class="sol-table">
        <thead>
          <tr style="border-bottom:1px solid var(--border2)">
            <th style="text-align:left;padding:6px 10px;color:var(--muted);font-weight:400">Tool</th>
            {dim_ths}
            <th style="text-align:center;padding:6px 8px;color:var(--text2);font-weight:700;border-left:1px solid var(--border2)">/{TOTAL_RAW_MAX}</th>
            <th style="text-align:center;padding:6px 8px;color:var(--text2);font-weight:700">/100</th>
          </tr>
          <tr style="border-bottom:1px solid var(--border)">{max_pts_cells}</tr>
        </thead>
        <tbody>
          {shark_row}
          {scan_row}
          {''.join(det_rows)}
        </tbody>
      </table>
    </div>
    {disclaimer}
  </div>"""


def _findings_section(result: ScanResult) -> str:
    if not result.findings:
        return """
  <div class="sec">
    <div class="sec-head"><span class="sec-title">&#128270; Findings</span><span class="sec-count">0 findings</span></div>
    <div style="padding:24px;color:var(--text2)">No findings. Your governance posture is clean.</div>
  </div>"""

    groups_html = []
    for sev in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW):
        sev_findings = [f for f in result.findings if f.severity == sev]
        if not sev_findings:
            continue
        sev_low = sev.value.lower()
        color = SEVERITY_COLORS[sev]
        gid = f"fg-{sev_low}"

        preview = sev_findings[:3]
        rest = sev_findings[3:]

        cards = [_finding_card(f, color, sev_low) for f in preview]

        rest_html = ""
        if rest:
            rest_cards = [_finding_card(f, color, sev_low) for f in rest]
            rest_html = f"""<details style="margin-top:4px">
    <summary style="cursor:pointer;font-family:var(--mono);font-size:11px;color:var(--text2);margin-bottom:8px;padding-left:24px">Show {len(rest)} more {sev.value} findings</summary>
    {''.join(rest_cards)}
  </details>"""

        open_cls = " open" if sev == Severity.CRITICAL else ""
        arrow_cls = " open" if sev == Severity.CRITICAL else ""

        groups_html.append(f"""<div>
  <div class="fg-hdr" style="color:{color}" onclick="toggleGroup('{gid}')">
    <span id="{gid}-arrow" class="arrow{arrow_cls}">&#9654;</span>
    {sev.value} <span class="fg-cnt" style="background:rgba({_color_rgb(color)},.12);color:{color}">{len(sev_findings)}</span>
  </div>
  <div id="{gid}" class="fg-body{open_cls}">{''.join(cards)}{rest_html}</div>
</div>""")

    return f"""
  <div class="sec">
    <div class="sec-head"><span class="sec-title">&#128270; Findings</span><span class="sec-count">{len(result.findings)} total</span></div>
    {''.join(groups_html)}
  </div>"""


def _finding_card(f, color: str, sev_low: str) -> str:
    loc = ""
    if f.file and f.line:
        short = f.file if len(f.file) <= 60 else "..." + f.file[-57:]
        loc = f'<div class="f-loc">{_esc(short)}:{f.line}</div>'

    comp_tags = ""
    tags = []
    if f.compliance.eu_ai_act:
        tags.append(f"<span>EU AI Act {_esc(f.compliance.eu_ai_act)}</span>")
    if f.compliance.owasp_llm:
        tags.append(f"<span>OWASP {_esc(f.compliance.owasp_llm)}</span>")
    if f.compliance.mitre_atlas:
        tags.append(f"<span>MITRE {_esc(f.compliance.mitre_atlas)}</span>")
    if tags:
        comp_tags = f'<div class="f-compliance">{"".join(tags)}</div>'

    return f"""<div class="f-card" onclick="toggleFinding(this)">
  <div class="f-top">
    <span class="f-sev" style="background:rgba({_color_rgb(color)},.12);color:{color}">{f.severity.value}</span>
    <span class="f-dim">{f.dimension}</span>
  </div>
  <div class="f-msg">{_esc(f.message)}</div>
  {loc}
  <div class="f-detail">
    <div class="f-rem">{_esc(f.remediation)}</div>
    {comp_tags}
  </div>
</div>"""


def _recommendations(result: ScanResult) -> str:
    if not result.findings and not any(ds.raw < ds.max for ds in result.dimension_scores.values()):
        return ""

    # Build recommendations from dimension gaps
    dim_gaps = []
    for dim in ALL_DIMENSIONS:
        ds = result.dimension_scores.get(dim.id)
        raw = ds.raw if ds else 0
        mx = ds.max if ds else dim.max_score
        gap = mx - raw
        if gap > 0:
            dim_gaps.append((dim.id, dim.name, raw, mx, gap))
    dim_gaps.sort(key=lambda x: x[4], reverse=True)

    top5 = dim_gaps[:5]
    if not top5:
        return ""

    items = []
    # First recommendation gets special treatment with workaround tax + comparison card
    first = True
    for i, (dim_id, name, raw, mx, gap) in enumerate(top5, 1):
        template = _REC_TEMPLATES.get(dim_id)
        if template:
            title, body = template
        else:
            title = f"Improve {name}"
            body = f"Currently scoring {raw}/{mx}. Address gaps to gain up to +{gap} raw points toward your governance score."

        # Find related findings for additional context
        dim_findings = [f for f in result.findings if f.dimension == dim_id]
        finding_context = ""
        if dim_findings:
            finding_count = len(dim_findings)
            finding_context = f" ({finding_count} finding{'s' if finding_count != 1 else ''} in this dimension)"

        extras = ""
        if first and result.total_score < _SHARKROUTER_SCORE:
            extras = _workaround_tax() + _comparison_card(result)
            first = False

        items.append(f"""<div class="rec">
  <div class="rec-n">#{i}</div>
  <div>
    <div class="rec-title">{_esc(title)} <span class="rec-pts">+{gap} pts</span></div>
    <div class="rec-body">{_esc(body)}{_esc(finding_context)}</div>
    {extras}
  </div>
</div>""")

    return f"""
  <div class="sec">
    <div class="sec-head"><span class="sec-title">&#128161; Recommendations</span><span class="sec-count">ordered by score impact</span></div>
    {''.join(items)}
  </div>"""


def _workaround_tax() -> str:
    return """<div class="workaround-box">
  <div class="workaround-label">&#9888; The Workaround Tax</div>
  <div class="workaround-text">
    <strong>Stop paying the Workaround Tax.</strong>
    Relying on prompt-filters and out-of-band monitoring forces your developers to write
    manual security logic scattered across every agent and service.
    A centralized gateway enforces policy automatically &mdash; at the interception layer,
    on every tool call, without code changes in your agents.
  </div>
</div>"""


def _comparison_card(result: ScanResult) -> str:
    score = result.total_score
    level = result.level
    shark_score = _SHARKROUTER_SCORE
    delta = shark_score - score

    # Pick dimensions with biggest gap (WhiteFin estimate - current score)
    gap_dims = []
    for dim in ALL_DIMENSIONS:
        ds = result.dimension_scores.get(dim.id)
        raw = ds.raw if ds else 0
        mx = ds.max if ds else dim.max_score
        if mx == 0:
            continue
        sr_dim = min(round(mx * (shark_score / 100)), mx)
        gap = sr_dim - raw
        if gap > 0:
            gap_dims.append((dim.id, dim.name, raw, mx, sr_dim, gap))
    # Show up to 5 biggest gaps
    gap_dims.sort(key=lambda x: x[5], reverse=True)
    gap_dims = gap_dims[:5]

    # Current side dimension rows
    cur_rows = []
    sr_rows = []
    for dim_id, name, raw, mx, sr_dim, gap in gap_dims:
        cur_pct = round(raw / mx * 100) if mx else 0
        cur_color = _pct_color(cur_pct)
        val_style = ' style="color:var(--critical)"' if raw == 0 else ""
        cur_rows.append(f'<div class="cmp-dim"><span class="cmp-dim-lbl">{dim_id} {_esc(name)}</span><div class="cmp-bt"><div class="cmp-bf" style="width:{cur_pct}%;background:{cur_color}"></div></div><span class="cmp-val"{val_style}>{raw}/{mx}</span></div>')
        sr_pct = round(sr_dim / mx * 100) if mx else 0
        sr_rows.append(f'<div class="cmp-dim"><span class="cmp-dim-lbl">{dim_id} {_esc(name)}</span><div class="cmp-bt"><div class="cmp-bf" style="width:{sr_pct}%;background:var(--low)"></div></div><span class="cmp-val s">{sr_dim} <span class="delta">+{gap}</span></span></div>')

    # Level symbol: ✓ for GOVERNED, ~ for PARTIAL, ✗ for AT_RISK/UNGOVERNED
    if level == ScoreLevel.GOVERNED:
        cur_symbol = "&#10003;"
        cur_lvl_cls = "s"
    elif level == ScoreLevel.PARTIAL:
        cur_symbol = "&#126;"
        cur_lvl_cls = "w"
    else:
        cur_symbol = "&#10007;"
        cur_lvl_cls = "c"
    sr_lvl_cls = "s"

    return f"""<div class="cmp">
  <div class="cmp-grid">
    <div class="cmp-col cmp-cur">
      <div class="cmp-lbl c">Current state</div>
      <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px">
        <span class="cmp-score c">{score}</span><span class="cmp-denom">/ 100</span>
      </div>
      <div class="cmp-lvl {cur_lvl_cls}">{cur_symbol} {level.value.replace('_', ' ')}</div>
      {''.join(cur_rows)}
    </div>
    <div class="cmp-col cmp-sr">
      <div class="cmp-lbl s">+ WhiteFin (full deployment)</div>
      <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:4px">
        <span class="cmp-score s">{shark_score}</span><span class="cmp-denom">/ 100</span>
      </div>
      <div class="cmp-lvl {sr_lvl_cls}">&#10003; GOVERNED</div>
      {''.join(sr_rows)}
    </div>
  </div>
  <div class="cmp-foot">
    <span>* Projection based on SharkRouter's estimated score. Actual results may vary.&nbsp;&nbsp;<a href="https://sharkrouter.ai">sharkrouter.ai &rarr;</a></span>
    <span class="cmp-delta">{score} &rarr; {shark_score} &middot; +{delta} pts</span>
  </div>
</div>"""


def _email_form(result: ScanResult) -> str:
    crits = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
    detected_tools = [c.display_name for c in result.competitors if c.confidence != "low"]
    finding_counts = {}
    for sev in Severity:
        finding_counts[sev.value] = sum(1 for f in result.findings if f.severity == sev)

    dim_scores = {}
    for dim_id, ds in result.dimension_scores.items():
        dim_scores[dim_id] = ds.raw

    data_json = json.dumps({
        "score": result.total_score,
        "level": result.level.value,
        "total_findings": len(result.findings),
        "critical_count": crits,
        "finding_counts": finding_counts,
        "detected_tools": detected_tools,
        "mcp_tool_count": len(result.mcp_tools),
        "dimensions": dim_scores,
        "warden_version": __version__,
        "scoring_model": __scoring_model__,
        "source": "html_report",
    })

    crit_label = f'<span style="color:var(--critical);font-weight:600">{crits} CRITICAL</span> finding{"s" if crits != 1 else ""}' if crits else f'{len(result.findings)} findings'

    return f"""
  <div class="sec" style="border-color:rgba(96,165,250,0.25)">
    <div class="email-wrap">
      <div>
        <div style="font-family:var(--mono);font-size:10px;color:var(--info);letter-spacing:2px;text-transform:uppercase;margin-bottom:8px">&#9993; Get your remediation guide</div>
        <div style="font-size:18px;font-weight:700;margin-bottom:6px">Personalized remediation plan for your {crit_label}</div>
        <div class="email-info">
          We'll email you a prioritized remediation guide with the exact steps to fix your
          biggest governance gaps — ranked by point impact, with actionable instructions per dimension.
        </div>
        <div class="email-cols">
          <div>
            <div class="email-col-hdr" style="color:var(--low)">&#10003; WE SEND</div>
            <ul>
              <li>&rarr; Your score ({result.total_score}/100)</li>
              <li>&rarr; Top dimension gaps + fixes</li>
              <li>&rarr; Finding counts by severity</li>
              <li>&rarr; Detected tools summary</li>
            </ul>
          </div>
          <div>
            <div class="email-col-hdr" style="color:var(--critical)">&#10007; WE NEVER SEND</div>
            <ul>
              <li>&rarr; API key values</li>
              <li>&rarr; Log file content</li>
              <li>&rarr; File paths or hostnames</li>
              <li>&rarr; Any PII</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="email-form">
        <div style="font-size:13px;color:var(--text2);margin-bottom:4px;line-height:1.5">Enter your work email to receive the report and remediation guide.</div>
        <input type="email" class="email-input" placeholder="you@company.com">
        <input type="text" id="warden-company" class="email-input" placeholder="Company (optional)">
        <button class="email-btn" onclick="submitEmail(this)">SEND REPORT &rarr;</button>
        <div id="email-status" style="font-family:var(--mono);font-size:11px;color:var(--muted);text-align:center;min-height:16px"></div>
        <div style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border);font-size:11px;color:var(--muted);line-height:1.7">
          Max 3 emails total. Unsubscribe anytime.<br>
          <a href="https://sharkrouter.ai/privacy" style="color:var(--info);text-decoration:none">Privacy policy &rarr;</a>
        </div>
      </div>
    </div>
    <div class="email-bar">
      <span>Prefer to keep it local? Report saved at <span style="font-family:var(--mono);color:var(--text)">./warden_report.html</span></span>
      <span style="font-family:var(--mono);font-size:10px">warden scan --no-email for CI/headless use</span>
    </div>
    <script type="application/json" id="warden-data">{data_json}</script>
  </div>"""


def _footer() -> str:
    return f"""
  <div class="foot">
    Generated by <strong>Warden v{__version__}</strong> &middot; Open Source &middot; MIT License &middot;
    <a href="https://github.com/SharkRouter/warden">github.com/sharkrouter/warden</a><br>
    Scoring model v{__scoring_model__} &middot; {len(ALL_DIMENSIONS)} weighted dimensions &middot; {TOTAL_RAW_MAX} pts &middot; methodology in SCORING.md<br>
    <div class="foot-priv">Scan data stays on your machine. Email delivery is opt-in only.<br>
    When opted in: score + metadata only. Never: keys, logs, paths, or PII.</div>
    <a href="https://sharkrouter.ai/privacy" style="font-size:10px">Privacy policy</a> &middot;
    To enforce policies on what Warden found &rarr; <a href="https://sharkrouter.ai" class="foot-cta">Explore what 91/100 looks like &rarr;</a>
  </div>"""


def _pct_color(pct: int) -> str:
    if pct >= 80:
        return "var(--low)"
    if pct >= 60:
        return "var(--info)"
    if pct >= 35:
        return "var(--high)"
    if pct > 0:
        return "var(--critical)"
    return "var(--muted)"


def _color_rgb(hex_color: str) -> str:
    """Convert hex color to r,g,b string for rgba()."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"
    return "255,255,255"


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
