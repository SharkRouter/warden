# ruff: noqa: E501
"""Self-contained HTML report generation.

CRITICAL: No external requests. All CSS and layout are embedded.
Air-gapped environments work perfectly — system font stack only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from warden import __scoring_model__, __version__
from warden.models import ScanResult, ScoreLevel, Severity
from warden.scoring.dimensions import GROUPS

SEVERITY_COLORS = {
    Severity.CRITICAL: "#ff3b3b",
    Severity.HIGH: "#ff8c00",
    Severity.MEDIUM: "#f5c518",
    Severity.LOW: "#4ade80",
}

LEVEL_COLORS = {
    ScoreLevel.GOVERNED: "#4ade80",
    ScoreLevel.PARTIAL: "#f5c518",
    ScoreLevel.AT_RISK: "#ff8c00",
    ScoreLevel.UNGOVERNED: "#ff3b3b",
}

# Embedded market data: (id, display_name, category, warden_score, heatmap_x, heatmap_y)
# x: 0=prompt, 1=framework, 2=gateway, 3=infra  y: 0=observe, 1=detect, 2=enforce, 3=full
_MARKET_REGISTRY: list[tuple[str, str, str, int, int, int]] = [
    ("sharkrouter", "SharkRouter", "Tool-Call Gateway", 87, 2, 3),
    ("zenity", "Zenity", "Agent Governance", 48, 2, 2),
    ("wiz", "Wiz", "Cloud AI-SPM", 41, 3, 2),
    ("oasis", "Oasis Security", "NHI Access", 38, 3, 1),
    ("lasso", "Lasso / Noma", "Agent Monitoring", 30, 1, 1),
    ("kong", "Kong AI Gateway", "API Gateway", 27, 2, 1),
    ("robust", "Robust / Cisco", "AI Firewall", 26, 0, 2),
    ("rubrik", "Rubrik Annapurna", "Data + Agents", 26, 3, 1),
    ("portkey", "Portkey", "LLM Gateway", 24, 2, 1),
    ("pangea", "Pangea / CalypsoAI", "Prompt Layer", 23, 0, 1),
    ("neuraltrust", "NeuralTrust", "LLM Gateway", 23, 2, 1),
    ("knostic", "Knostic", "Agent Monitoring", 22, 1, 1),
    ("promptsec", "Prompt Security", "Prompt Layer", 21, 0, 2),
    ("cfenvoy", "CF / Envoy", "Proxy", 20, 2, 0),
    ("mcpscan", "mcp-scan", "Vuln Scanner", 18, 1, 0),
    ("lakera", "Lakera Guard", "Prompt Layer", 13, 0, 1),
    ("aifw", "aiFWall", "Prompt Firewall", 11, 0, 0),
]

# Heatmap pixel positions per grid cell (x-axis: 4 cols, y-axis: 4 rows)
_HM_X = [112, 292, 472, 652]  # center x per column
_HM_Y = [380, 275, 170, 65]   # center y per row (bottom=observe, top=full)


def write_html_report(result: ScanResult, output_path: Path) -> None:
    """Write self-contained HTML report. No external requests."""
    html = _build_html(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def _build_html(result: ScanResult) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    sections = [
        _header(result, timestamp),
        _hero(result),
        _summary_grid(result),
        _findings_section(result),
        _detected_tools(result),
        _remediation_actions(result),
        _market_table(result),
        _heatmap(result),
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
<div class="wrap">
{''.join(sections)}
</div>
{_js()}
</body>
</html>"""


def _css() -> str:
    return """<style>
:root {
  --bg:#0a0c10; --surface:#10131a; --surface2:#161b24; --border:#1e2535;
  --text:#e2e8f0; --muted:#64748b;
  --critical:#ff3b3b; --high:#ff8c00; --medium:#f5c518; --low:#4ade80;
  --info:#60a5fa; --teal:#00bcd4;
  --critical-dim:rgba(255,59,59,.12); --high-dim:rgba(255,140,0,.12);
  --medium-dim:rgba(245,197,24,.12); --low-dim:rgba(74,222,128,.12);
  --teal-dim:rgba(0,188,212,.12);
  --mono:'SF Mono','Cascadia Code','JetBrains Mono','Fira Code',Consolas,monospace;
  --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--sans);background:var(--bg);color:var(--text);line-height:1.6}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px 48px}

/* --- SECTION CARDS --- */
.sec{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:28px 32px;margin-top:24px}
.sec-title{font-size:13px;font-weight:700;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:18px}

/* --- HEADER --- */
.hdr{display:flex;justify-content:space-between;align-items:flex-start;padding:32px 0 24px;flex-wrap:wrap;gap:16px}
.hdr-left{display:flex;align-items:center;gap:14px}
.hdr-logo{font-family:var(--mono);font-size:18px;font-weight:800;color:var(--teal);letter-spacing:3px}
.hdr-sub{font-size:13px;color:var(--muted)}
.hdr-meta{font-family:var(--mono);font-size:11px;color:var(--muted);line-height:1.8}
.hdr-badge{font-family:var(--mono);font-size:10px;color:var(--low);border:1px solid rgba(74,222,128,.25);padding:6px 12px;border-radius:6px;text-align:right;white-space:nowrap;max-width:280px;line-height:1.6}

/* --- HERO --- */
.hero{display:flex;gap:48px;align-items:flex-start;flex-wrap:wrap}
.hero-gauge{flex-shrink:0}
.hero-dims{flex:1;min-width:300px}
.gauge-label{text-align:center;margin-top:8px}
.level-badge{font-family:var(--mono);font-size:12px;font-weight:700;padding:4px 14px;border-radius:4px;display:inline-block}
.lvl-governed{background:var(--low-dim);color:var(--low)}
.lvl-partial{background:var(--medium-dim);color:var(--medium)}
.lvl-at_risk{background:var(--high-dim);color:var(--high)}
.lvl-ungoverned{background:var(--critical-dim);color:var(--critical)}

/* dimension bars */
.dim-group-label{font-family:var(--mono);font-size:10px;color:var(--teal);letter-spacing:2px;margin:16px 0 6px;padding-bottom:4px;border-bottom:1px solid var(--border)}
.dim-group-label:first-child{margin-top:0}
.dim-row{display:flex;align-items:center;gap:8px;margin:5px 0}
.dim-lbl{font-size:12px;width:170px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dim-track{flex:1;height:7px;background:#1e293b;border-radius:4px;overflow:hidden;min-width:60px}
.dim-fill{height:100%;border-radius:4px}
.dim-val{font-family:var(--mono);font-size:11px;color:var(--muted);width:50px;text-align:right}
.dim-subtotal{font-family:var(--mono);font-size:11px;color:var(--teal);text-align:right;margin:4px 0 0;padding-top:4px;border-top:1px dashed var(--border)}

/* --- SUMMARY GRID --- */
.sgrid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.sgrid-cell{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:16px;text-align:center}
.sgrid-val{font-family:var(--mono);font-size:28px;font-weight:700}
.sgrid-lbl{font-size:11px;color:var(--muted);margin-top:4px}

/* --- FINDINGS --- */
.fg-hdr{font-family:var(--mono);font-size:12px;font-weight:700;letter-spacing:1px;cursor:pointer;display:flex;align-items:center;gap:8px;margin-bottom:8px;user-select:none}
.fg-cnt{padding:2px 9px;border-radius:10px;font-size:11px}
.fg-body{display:none}.fg-body.open{display:block}
.f-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:12px 16px;margin-bottom:6px}
.f-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.f-sev{font-family:var(--mono);font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;white-space:nowrap}
.f-dim{font-family:var(--mono);font-size:10px;color:var(--muted);background:var(--surface);padding:2px 6px;border-radius:3px}
.f-msg{font-size:13px;margin:6px 0 2px}
.f-loc{font-family:var(--mono);font-size:11px;color:var(--teal)}
.f-detail{font-size:12px;color:var(--muted);margin-top:8px;padding-top:8px;border-top:1px solid var(--border);display:none}
.f-card.exp .f-detail{display:block}
.f-rem{color:var(--teal)}
.arrow{transition:transform .2s;display:inline-block}.arrow.open{transform:rotate(90deg)}

/* --- DETECTED TOOLS --- */
.tc{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:14px 18px;margin-bottom:8px}
.tc-top{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.tc-name{font-weight:600;font-size:14px}
.tc-cat{font-family:var(--mono);font-size:10px;padding:2px 8px;border-radius:4px}
.tc-conf{font-family:var(--mono);font-size:10px;padding:2px 8px;border-radius:4px}
.tc-conf-high{background:var(--low-dim);color:var(--low)}
.tc-conf-medium{background:var(--medium-dim);color:var(--medium)}
.tc-signals{font-size:11px;color:var(--muted);margin-top:6px}
.tc-tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.tc-tag{font-size:10px;padding:2px 8px;border-radius:4px}
.tc-str{background:var(--low-dim);color:var(--low)}
.tc-wk{background:var(--critical-dim);color:var(--critical)}

/* --- REMEDIATION --- */
.rem-card{background:var(--surface2);border:1px solid var(--border);border-left:3px solid var(--teal);border-radius:8px;padding:14px 18px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;gap:12px}
.rem-num{font-family:var(--mono);font-size:24px;font-weight:700;color:var(--teal);flex-shrink:0}
.rem-text{font-size:13px;flex:1}.rem-text .sub{color:var(--muted);font-size:12px}
.rem-impact{font-family:var(--mono);font-size:12px;color:var(--low);white-space:nowrap}
.cmp-card{background:var(--surface2);border:1px solid var(--teal);border-radius:10px;padding:20px 24px;margin-top:16px}
.cmp-title{font-family:var(--mono);font-size:13px;color:var(--teal);margin-bottom:12px;letter-spacing:1px}
.cmp-row{display:flex;justify-content:space-between;font-size:13px;padding:4px 0;border-bottom:1px solid var(--border)}
.cmp-row:last-child{border-bottom:none}
.cmp-delta{font-family:var(--mono);font-size:12px}
.cmp-pos{color:var(--low)}.cmp-neg{color:var(--critical)}
.cmp-cta{display:inline-block;margin-top:16px;background:linear-gradient(135deg,var(--teal),#0097a7);color:#000;padding:10px 24px;border-radius:8px;font-weight:700;font-size:13px;text-decoration:none}

/* --- MARKET TABLE --- */
.mkt-toggle{cursor:pointer;color:var(--teal);font-family:var(--mono);font-size:12px;user-select:none}
.mkt-wrap{display:none;overflow-x:auto;margin-top:12px}.mkt-wrap.open{display:block}
.mkt-tbl{width:100%;border-collapse:collapse;font-size:12px}
.mkt-tbl th,.mkt-tbl td{padding:6px 10px;border:1px solid var(--border);text-align:center}
.mkt-tbl th{background:#1e293b;color:var(--teal);font-family:var(--mono);font-size:10px}
.mkt-tbl .sr-row{background:rgba(0,188,212,.06)}

/* --- HEATMAP --- */
.hm-wrap{overflow-x:auto}

/* --- EMAIL FORM --- */
.email-sec{display:flex;gap:32px;flex-wrap:wrap;align-items:flex-start}
.email-left{flex:1;min-width:280px}
.email-right{flex:1;min-width:260px;display:flex;flex-direction:column;gap:10px}
.email-cols{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:12px;font-size:12px}
.email-col h4{font-family:var(--mono);font-size:11px;letter-spacing:1px;margin-bottom:6px}
.email-col li{list-style:none;padding:2px 0}
.email-input{width:100%;padding:10px 14px;border-radius:6px;border:1px solid var(--border);background:var(--surface2);color:var(--text);font-size:14px;font-family:var(--sans)}
.email-btn{width:100%;padding:12px;border:none;border-radius:6px;background:linear-gradient(135deg,var(--teal),#0097a7);color:#000;font-weight:700;font-size:14px;cursor:pointer;font-family:var(--mono);letter-spacing:1px;transition:opacity .2s}
.email-btn:hover{opacity:.9}
.email-note{font-size:11px;color:var(--muted);text-align:center}

/* --- FOOTER --- */
.ftr{text-align:center;padding:32px 0;font-size:12px;color:var(--muted);line-height:2}
.ftr a{color:var(--teal);text-decoration:none}
.ftr-cta{display:inline-block;margin-top:12px;background:linear-gradient(135deg,var(--teal),#0097a7);color:#000;padding:10px 24px;border-radius:8px;font-weight:700;font-size:13px;text-decoration:none}

/* --- RESPONSIVE --- */
@media(max-width:768px){
  .hero{flex-direction:column;align-items:center}
  .sgrid{grid-template-columns:repeat(2,1fr)}
  .sgrid-cell:last-child{grid-column:span 2}
  .email-sec{flex-direction:column}
  .hdr{flex-direction:column}
  .dim-lbl{width:120px}
  .cmp-row{flex-direction:column;gap:2px}
}

/* pulse animation for heatmap */
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
.hm-pulse{animation:pulse 2s ease-in-out infinite}
</style>"""


def _js() -> str:
    return """<script>
function toggleGroup(id){
  var b=document.getElementById(id);
  var a=document.getElementById(id+'-arrow');
  if(b){b.classList.toggle('open');if(a)a.classList.toggle('open')}
}
function toggleMarket(){
  var w=document.getElementById('mkt-wrap');
  if(w)w.classList.toggle('open');
  var a=document.getElementById('mkt-arrow');
  if(a)a.classList.toggle('open');
}
function toggleFinding(el){el.classList.toggle('exp')}
function submitEmail(btn){
  var email=document.getElementById('warden-email').value;
  if(!email||email.indexOf('@')<1){btn.textContent='Enter valid email';return}
  btn.disabled=true;btn.textContent='SENDING...';
  var data=JSON.parse(document.getElementById('warden-data').textContent);
  fetch('https://api.sharkrouter.ai/v1/warden/submit',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({email:email,score:data.score,level:data.level,
      total_findings:data.total_findings,critical_count:data.critical_count,
      warden_version:data.warden_version,scoring_model:data.scoring_model})
  }).then(function(r){
    if(r.ok){btn.textContent='\\u2713 SENT';btn.style.background='#4ade80'}
    else{btn.textContent='SEND REPORT \\u2192';btn.disabled=false}
  }).catch(function(){btn.textContent='SEND REPORT \\u2192';btn.disabled=false});
}
</script>"""


def _header(result: ScanResult, timestamp: str) -> str:
    return f"""
<div class="hdr">
  <div>
    <div class="hdr-left">
      <span style="font-size:28px">&#x1F988;</span>
      <div>
        <div class="hdr-logo">WARDEN</div>
        <div class="hdr-sub">AI Agent Governance Report</div>
      </div>
    </div>
    <div class="hdr-meta" style="margin-top:10px">
      {_esc(result.target_path)}<br>
      {timestamp} &middot; Warden v{__version__} &middot; Scoring Model v{__scoring_model__}
    </div>
  </div>
  <div class="hdr-badge">&#x1F512; All data collected locally<br>Nothing left this machine</div>
</div>"""


def _hero(result: ScanResult) -> str:
    score = result.total_score
    level = result.level
    color = LEVEL_COLORS.get(level, "#999")
    lvl_cls = f"lvl-{level.value.lower()}"

    # SVG gauge
    r = 65
    circ = 2 * 3.14159 * r
    offset = circ - (score / 100) * circ
    if score >= 80:
        g1, g2 = "#4ade80", "#00bcd4"
    elif score >= 50:
        g1, g2 = "#f5c518", "#4ade80"
    elif score >= 25:
        g1, g2 = "#ff8c00", "#f5c518"
    else:
        g1, g2 = "#ff3b3b", "#ff3b3b"

    gauge_svg = f"""<svg width="150" height="150" viewBox="0 0 150 150">
  <defs><linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="{g1}"/><stop offset="100%" stop-color="{g2}"/>
  </linearGradient></defs>
  <circle cx="75" cy="75" r="{r}" fill="none" stroke="#1e293b" stroke-width="10"/>
  <circle cx="75" cy="75" r="{r}" fill="none" stroke="url(#sg)" stroke-width="10"
    stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"
    transform="rotate(-90 75 75)"/>
  <text x="75" y="72" text-anchor="middle" fill="{color}"
    font-family="var(--mono)" font-size="38" font-weight="700">{score}</text>
  <text x="75" y="92" text-anchor="middle" fill="#64748b"
    font-family="var(--mono)" font-size="13">/100</text>
</svg>"""

    # Dimension bars grouped
    dim_html = []
    for group_name, dims in GROUPS.items():
        dim_html.append(f'<div class="dim-group-label">{_esc(group_name)}</div>')
        grp_raw = 0
        grp_max = 0
        for dim in dims:
            ds = result.dimension_scores.get(dim.id)
            raw = ds.raw if ds else 0
            mx = ds.max if ds else dim.max_score
            pct = ds.pct if ds else 0
            grp_raw += raw
            grp_max += mx
            bar_color = _pct_color(pct)
            dim_html.append(f"""<div class="dim-row">
  <div class="dim-lbl">{dim.id} {_esc(dim.name)}</div>
  <div class="dim-track"><div class="dim-fill" style="width:{pct}%;background:{bar_color}"></div></div>
  <div class="dim-val">{raw}/{mx}</div>
</div>""")
        grp_pct = round(grp_raw / grp_max * 100) if grp_max else 0
        dim_html.append(f'<div class="dim-subtotal">{grp_raw}/{grp_max} ({grp_pct}%)</div>')

    return f"""
<div class="sec">
  <div class="hero">
    <div class="hero-gauge">
      {gauge_svg}
      <div class="gauge-label"><span class="level-badge {lvl_cls}">{level.value.replace('_', ' ')}</span></div>
    </div>
    <div class="hero-dims">
      {''.join(dim_html)}
    </div>
  </div>
</div>"""


def _summary_grid(result: ScanResult) -> str:
    total = len(result.findings)
    crits = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
    secrets = len(result.secrets)
    active = sum(1 for ds in result.dimension_scores.values() if ds.raw > 0)
    return f"""
<div class="sec">
  <div class="sec-title">Summary</div>
  <div class="sgrid">
    <div class="sgrid-cell"><div class="sgrid-val" style="color:var(--teal)">{total}</div><div class="sgrid-lbl">Total Findings</div></div>
    <div class="sgrid-cell"><div class="sgrid-val" style="color:var(--critical)">{crits}</div><div class="sgrid-lbl">Critical</div></div>
    <div class="sgrid-cell"><div class="sgrid-val" style="color:var(--high)">{secrets}</div><div class="sgrid-lbl">Secrets Found</div></div>
    <div class="sgrid-cell"><div class="sgrid-val" style="color:var(--teal)">{active}/17</div><div class="sgrid-lbl">Dimensions Active</div></div>
    <div class="sgrid-cell"><div class="sgrid-val" style="color:var(--info)">12</div><div class="sgrid-lbl">Scan Layers</div></div>
  </div>
</div>"""


def _findings_section(result: ScanResult) -> str:
    if not result.findings:
        return """
<div class="sec">
  <div class="sec-title">Findings</div>
  <p style="color:var(--muted)">No findings. Your governance posture is clean.</p>
</div>"""

    groups_html = []
    for sev in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW):
        sev_findings = [f for f in result.findings if f.severity == sev]
        if not sev_findings:
            continue
        sev_low = sev.value.lower()
        color = SEVERITY_COLORS[sev]
        dim_var = f"var(--{sev_low}-dim)"
        gid = f"fg-{sev_low}"

        cards = []
        for f in sev_findings:
            loc = ""
            if f.file and f.line:
                short = f.file if len(f.file) <= 60 else "..." + f.file[-57:]
                loc = f'<div class="f-loc">{_esc(short)}:{f.line}</div>'
            cards.append(f"""<div class="f-card" onclick="toggleFinding(this)">
  <div class="f-top">
    <span class="f-sev" style="background:{dim_var};color:{color}">{sev.value}</span>
    <span class="f-dim">{f.dimension}</span>
  </div>
  <div class="f-msg">{_esc(f.message)}</div>
  {loc}
  <div class="f-detail"><span class="f-rem">{_esc(f.remediation)}</span></div>
</div>""")

        groups_html.append(f"""<div style="margin-bottom:20px">
  <div class="fg-hdr" style="color:{color}" onclick="toggleGroup('{gid}')">
    <span id="{gid}-arrow" class="arrow">&#9654;</span>
    {sev.value} <span class="fg-cnt" style="background:{dim_var};color:{color}">{len(sev_findings)}</span>
  </div>
  <div id="{gid}" class="fg-body">{''.join(cards)}</div>
</div>""")

    return f"""
<div class="sec">
  <div class="sec-title">Findings ({len(result.findings)})</div>
  {''.join(groups_html)}
</div>"""


def _detected_tools(result: ScanResult) -> str:
    detected = [c for c in result.competitors if c.confidence != "low"]
    if not detected:
        return """
<div class="sec">
  <div class="sec-title">Governance Tools Detected</div>
  <p style="color:var(--muted)">No governance tools detected in this project.</p>
</div>"""

    cards = []
    for c in detected:
        conf_cls = "tc-conf-high" if c.confidence == "high" else "tc-conf-medium"
        signals_str = ", ".join(c.signals[:5]) if c.signals else ""
        str_tags = "".join(f'<span class="tc-tag tc-str">{_esc(s)}</span>' for s in c.strengths[:4])
        wk_tags = "".join(f'<span class="tc-tag tc-wk">{_esc(w)}</span>' for w in c.weaknesses[:4])
        cards.append(f"""<div class="tc">
  <div class="tc-top">
    <div>
      <span class="tc-name">{_esc(c.display_name)}</span>
      <span class="tc-cat" style="background:var(--medium-dim);color:var(--medium);margin-left:8px">{_esc(c.category)}</span>
    </div>
    <span class="tc-conf {conf_cls}">{c.confidence.upper()}</span>
  </div>
  {f'<div class="tc-signals">Signals: {_esc(signals_str)}</div>' if signals_str else ''}
  <div class="tc-tags">{str_tags}{wk_tags}</div>
</div>""")

    return f"""
<div class="sec">
  <div class="sec-title">Governance Tools Detected</div>
  {''.join(cards)}
</div>"""


def _remediation_actions(result: ScanResult) -> str:
    # Top 5 findings by severity
    priority = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
    sorted_f = sorted(result.findings, key=lambda f: priority.get(f.severity, 9))
    top5 = sorted_f[:5]
    if not top5:
        return ""

    items = []
    for i, f in enumerate(top5, 1):
        # Rough impact estimate based on severity
        est = {Severity.CRITICAL: 8, Severity.HIGH: 5, Severity.MEDIUM: 3, Severity.LOW: 1}.get(f.severity, 1)
        items.append(f"""<div class="rem-card">
  <div class="rem-num">{i}</div>
  <div class="rem-text">
    <strong>{_esc(f.message)}</strong><br>
    <span class="sub">{_esc(f.remediation)}</span>
  </div>
  <div class="rem-impact">~+{est} pts</div>
</div>""")

    # SharkRouter comparison card
    score = result.total_score
    sr_score = 87
    cmp_rows = []
    for group_name, dims in GROUPS.items():
        user_raw = sum((result.dimension_scores.get(d.id).raw if result.dimension_scores.get(d.id) else 0) for d in dims)
        user_max = sum((result.dimension_scores.get(d.id).max if result.dimension_scores.get(d.id) else d.max_score) for d in dims)
        user_pct = round(user_raw / user_max * 100) if user_max else 0
        # Estimate SharkRouter group pct (weighted toward high)
        sr_pcts = {"Core Governance": 95, "Advanced Controls": 90, "Ecosystem": 70, "Unique Capabilities": 85}
        sr_pct = sr_pcts.get(group_name, 80)
        delta = sr_pct - user_pct
        delta_cls = "cmp-pos" if delta > 0 else "cmp-neg"
        sign = "+" if delta > 0 else ""
        cmp_rows.append(f"""<div class="cmp-row">
  <span>{_esc(group_name)}</span>
  <span style="font-family:var(--mono);font-size:12px">{user_pct}% &rarr; {sr_pct}%
    <span class="cmp-delta {delta_cls}">{sign}{delta}%</span></span>
</div>""")

    return f"""
<div class="sec">
  <div class="sec-title">Top Remediation Actions</div>
  {''.join(items)}
  <div class="cmp-card">
    <div class="cmp-title">SHARKROUTER COMPARISON</div>
    <div class="cmp-row" style="font-weight:700">
      <span>Overall Score</span>
      <span style="font-family:var(--mono)">{score}/100 &rarr; {sr_score}/100
        <span class="cmp-delta cmp-pos">+{sr_score - score}</span></span>
    </div>
    {''.join(cmp_rows)}
    <a href="https://sharkrouter.ai" class="cmp-cta">See SharkRouter in Action &rarr;</a>
  </div>
</div>"""


def _market_table(result: ScanResult) -> str:
    # Sort by score descending; SharkRouter first
    sorted_reg = sorted(_MARKET_REGISTRY, key=lambda r: r[3], reverse=True)
    top7 = sorted_reg[:7]
    rest = sorted_reg[7:]
    rest_min = min(r[3] for r in rest) if rest else 0
    rest_max = max(r[3] for r in rest) if rest else 0

    rows = []
    for _id, name, cat, ws, _x, _y in top7:
        cls = ' class="sr-row"' if _id == "sharkrouter" else ""
        rows.append(f'<tr{cls}><td style="text-align:left;font-weight:{"700" if _id == "sharkrouter" else "400"}">{_esc(name)}</td><td>{ws}/100</td></tr>')
    if rest:
        rows.append(f'<tr><td style="text-align:left;color:var(--muted)">{len(rest)} more scored {rest_min}&ndash;{rest_max} pts</td><td style="color:var(--muted)">&hellip;</td></tr>')

    return f"""
<div class="sec">
  <div class="sec-title">Market Comparison</div>
  <div class="mkt-toggle" onclick="toggleMarket()">
    <span id="mkt-arrow" class="arrow">&#9654;</span> Show market comparison table
  </div>
  <div id="mkt-wrap" class="mkt-wrap">
    <table class="mkt-tbl">
      <tr><th style="text-align:left">Tool</th><th>Score</th></tr>
      {''.join(rows)}
    </table>
    <div style="font-size:10px;color:var(--muted);margin-top:8px">
      Methodology: <a href="https://github.com/SharkRouter/warden" style="color:var(--teal);text-decoration:none">SCORING.md</a>
    </div>
  </div>
</div>"""


def _heatmap(result: ScanResult) -> str:
    # Determine "YOU" position based on score + detected tools
    score = result.total_score
    # Estimate y from score (0-25=observe, 25-50=detect, 50-75=enforce, 75+=full)
    if score >= 75:
        you_y = _HM_Y[3]
    elif score >= 50:
        you_y = _HM_Y[2]
    elif score >= 25:
        you_y = _HM_Y[1]
    else:
        you_y = _HM_Y[0]
    # Estimate x from detected tool categories
    you_x = _HM_X[1]  # default: framework level

    detected_ids = {c.id for c in result.competitors if c.confidence != "low"}

    # Build competitor bubbles
    bubbles = []
    for _id, name, _cat, ws, gx, gy in _MARKET_REGISTRY:
        px = _HM_X[gx] + hash(name) % 40 - 20  # jitter
        py = _HM_Y[gy] + hash(name) % 30 - 15
        if _id == "sharkrouter":
            # SharkRouter: large green pulsing at fixed position
            bubbles.append(
                '<circle cx="607" cy="45" r="32" fill="rgba(0,188,212,.18)" stroke="var(--teal)" stroke-width="2" class="hm-pulse"/>'
                '<text x="607" y="50" text-anchor="middle" fill="var(--teal)" font-family="var(--mono)" font-size="9" font-weight="700">SharkRouter</text>'
            )
        elif _id in detected_ids:
            # Detected: slightly larger, brighter
            bubbles.append(
                f'<circle cx="{px}" cy="{py}" r="16" fill="rgba(245,197,24,.15)" stroke="var(--medium)" stroke-width="1.5"/>'
                f'<text x="{px}" y="{py + 4}" text-anchor="middle" fill="var(--medium)" font-family="var(--mono)" font-size="7">{_esc(name[:12])}</text>'
            )
        else:
            # Registry: small dim
            r = max(6, ws // 5)
            bubbles.append(
                f'<circle cx="{px}" cy="{py}" r="{r}" fill="rgba(100,116,139,.15)" stroke="rgba(100,116,139,.3)" stroke-width="1"/>'
                f'<text x="{px}" y="{py + 3}" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="6">{_esc(name[:10])}</text>'
            )

    # YOU marker
    bubbles.append(
        f'<circle cx="{you_x}" cy="{you_y}" r="14" fill="rgba(255,59,59,.2)" stroke="var(--critical)" stroke-width="2"/>'
        f'<text x="{you_x}" y="{you_y + 4}" text-anchor="middle" fill="var(--critical)" font-family="var(--mono)" font-size="9" font-weight="700">YOU</text>'
    )

    return f"""
<div class="sec">
  <div class="sec-title">Market Positioning</div>
  <div class="hm-wrap">
    <svg viewBox="0 0 900 520" width="100%" style="max-width:900px">
      <!-- background -->
      <rect width="900" height="520" fill="var(--surface2)" rx="8"/>

      <!-- grid lines -->
      <line x1="225" y1="20" x2="225" y2="440" stroke="var(--border)" stroke-dasharray="6,4"/>
      <line x1="405" y1="20" x2="405" y2="440" stroke="var(--border)" stroke-dasharray="6,4"/>
      <line x1="585" y1="20" x2="585" y2="440" stroke="var(--border)" stroke-dasharray="6,4"/>
      <line x1="45" y1="120" x2="855" y2="120" stroke="var(--border)" stroke-dasharray="6,4"/>
      <line x1="45" y1="225" x2="855" y2="225" stroke="var(--border)" stroke-dasharray="6,4"/>
      <line x1="45" y1="330" x2="855" y2="330" stroke="var(--border)" stroke-dasharray="6,4"/>

      <!-- quadrant labels -->
      <text x="160" y="50" text-anchor="middle" fill="rgba(255,59,59,.3)" font-family="var(--mono)" font-size="9" font-weight="700">STRUCTURALLY</text>
      <text x="160" y="62" text-anchor="middle" fill="rgba(255,59,59,.3)" font-family="var(--mono)" font-size="9" font-weight="700">IMPOSSIBLE</text>
      <text x="720" y="50" text-anchor="middle" fill="rgba(0,188,212,.3)" font-family="var(--mono)" font-size="9" font-weight="700">SHARKROUTER</text>
      <text x="720" y="62" text-anchor="middle" fill="rgba(0,188,212,.3)" font-family="var(--mono)" font-size="9" font-weight="700">TERRITORY</text>
      <text x="160" y="410" text-anchor="middle" fill="rgba(245,197,24,.3)" font-family="var(--mono)" font-size="9" font-weight="700">THE WORKAROUND</text>
      <text x="160" y="422" text-anchor="middle" fill="rgba(245,197,24,.3)" font-family="var(--mono)" font-size="9" font-weight="700">ECONOMY</text>
      <text x="720" y="410" text-anchor="middle" fill="rgba(100,116,139,.3)" font-family="var(--mono)" font-size="9" font-weight="700">CLOUD POSTURE</text>
      <text x="720" y="422" text-anchor="middle" fill="rgba(100,116,139,.3)" font-family="var(--mono)" font-size="9" font-weight="700">/ NHI</text>

      <!-- X axis labels -->
      <text x="112" y="475" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="9">PROMPT LAYER</text>
      <text x="292" y="475" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="9">AGENT FRAMEWORK</text>
      <text x="472" y="475" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="9">TOOL-CALL GATEWAY</text>
      <text x="652" y="475" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="9">INFRA / CLOUD</text>

      <!-- Y axis labels -->
      <text x="20" y="385" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="8" transform="rotate(-90 20 385)">OBSERVE</text>
      <text x="20" y="280" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="8" transform="rotate(-90 20 280)">DETECT</text>
      <text x="20" y="175" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="8" transform="rotate(-90 20 175)">ENFORCE</text>
      <text x="20" y="70" text-anchor="middle" fill="var(--muted)" font-family="var(--mono)" font-size="8" transform="rotate(-90 20 70)">FULL</text>

      <!-- bubbles -->
      {''.join(bubbles)}

      <!-- border -->
      <rect x="40" y="20" width="820" height="440" fill="none" stroke="var(--border)" rx="4"/>
    </svg>
  </div>
</div>"""


def _email_form(result: ScanResult) -> str:
    crits = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
    import json
    data_json = json.dumps({
        "score": result.total_score,
        "level": result.level.value,
        "total_findings": len(result.findings),
        "critical_count": crits,
        "warden_version": __version__,
        "scoring_model": __scoring_model__,
    })

    return f"""
<div class="sec">
  <div class="email-sec">
    <div class="email-left">
      <div style="font-size:18px;font-weight:700;margin-bottom:8px">Get this report by email</div>
      <div style="font-size:13px;color:var(--muted)">
        We found <strong style="color:var(--critical)">{crits} critical</strong> findings.
        Get a copy of this report with remediation guidance delivered to your inbox.
      </div>
      <div class="email-cols">
        <div class="email-col">
          <h4 style="color:var(--low)">&#10003; WE SEND</h4>
          <ul>
            <li>Governance score</li>
            <li>Tool count</li>
            <li>Frameworks detected</li>
            <li>Full report PDF</li>
          </ul>
        </div>
        <div class="email-col">
          <h4 style="color:var(--critical)">&#10007; WE NEVER SEND</h4>
          <ul>
            <li>API keys or secrets</li>
            <li>Log file content</li>
            <li>File paths</li>
            <li>PII / personal data</li>
          </ul>
        </div>
      </div>
    </div>
    <div class="email-right">
      <input type="email" id="warden-email" class="email-input" placeholder="you@company.com">
      <button class="email-btn" onclick="submitEmail(this)">SEND REPORT &rarr;</button>
      <div class="email-note">Prefer to keep it local? Report saved at ./warden_report.html</div>
    </div>
  </div>
  <script type="application/json" id="warden-data">{data_json}</script>
</div>"""


def _footer() -> str:
    return f"""
<div class="ftr">
  Generated by Warden v{__version__} &middot; Scoring Model v{__scoring_model__} &middot; MIT License<br>
  <a href="https://github.com/SharkRouter/warden">github.com/SharkRouter/warden</a><br>
  This report was generated locally. No data was transmitted.<br>
  <a href="https://sharkrouter.ai" class="ftr-cta">See What 87/100 Looks Like &rarr;</a>
</div>"""


def _pct_color(pct: int) -> str:
    """Return bar fill color based on percentage."""
    if pct >= 80:
        return "var(--teal)"
    if pct >= 60:
        return "var(--low)"
    if pct >= 35:
        return "var(--medium)"
    if pct > 0:
        return "var(--high)"
    return "var(--critical)"


def _esc(text: str) -> str:
    """HTML-escape text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
