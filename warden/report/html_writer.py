"""Self-contained HTML report generation.

CRITICAL: No external requests. All CSS, fonts, and icons are embedded.
IBM Plex Mono font is referenced via system font stack (no base64 blob needed
for initial version — air-gapped environments have the font or fall back to monospace).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from warden import __version__, __scoring_model__
from warden.models import ScanResult, Severity, ScoreLevel
from warden.scoring.dimensions import ALL_DIMENSIONS, GROUPS
from warden.scanner.competitors import COMPETITORS


SEVERITY_COLORS = {
    Severity.CRITICAL: "#e74c3c",
    Severity.HIGH: "#e67e22",
    Severity.MEDIUM: "#f1c40f",
    Severity.LOW: "#95a5a6",
}

LEVEL_COLORS = {
    ScoreLevel.GOVERNED: "#27ae60",
    ScoreLevel.PARTIAL: "#f39c12",
    ScoreLevel.AT_RISK: "#e67e22",
    ScoreLevel.UNGOVERNED: "#e74c3c",
}


def write_html_report(result: ScanResult, output_path: Path) -> None:
    """Write self-contained HTML report. No external requests."""
    html = _build_html(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def _build_html(result: ScanResult) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    level_color = LEVEL_COLORS.get(result.level, "#333")

    sections = [
        _css(),
        _header(result, timestamp, level_color),
        _dimension_bars(result),
        _findings_section(result),
        _trap_defense_box(result),
        _competitor_section(result),
        _market_table(result),
        _comparison_panel(result),
        _recommendations(result),
        _footer(timestamp),
    ]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Warden Governance Report — {result.total_score}/100</title>
{sections[0]}
</head>
<body>
{''.join(sections[1:])}
</body>
</html>"""


def _css() -> str:
    return """<style>
/* IBM Plex Mono system font stack — no external requests */
:root {
  --font-mono: 'IBM Plex Mono', 'Cascadia Code', 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  --bg: #0d1117;
  --bg-card: #161b22;
  --bg-bar: #21262d;
  --text: #c9d1d9;
  --text-dim: #8b949e;
  --border: #30363d;
  --accent: #58a6ff;
  --critical: #e74c3c;
  --high: #e67e22;
  --medium: #f1c40f;
  --low: #95a5a6;
  --green: #27ae60;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: var(--font-mono);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  max-width: 960px;
  margin: 0 auto;
  padding: 2rem 1rem;
}
.header { text-align: center; margin-bottom: 2rem; }
.score-big {
  font-size: 4rem;
  font-weight: 700;
  margin: 0.5rem 0;
}
.level-badge {
  display: inline-block;
  padding: 0.25rem 1rem;
  border-radius: 4px;
  font-weight: 700;
  font-size: 1.1rem;
}
.section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}
.section h2 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
  color: var(--accent);
}
.dim-row {
  display: flex;
  align-items: center;
  margin: 0.3rem 0;
  font-size: 0.85rem;
}
.dim-label { width: 220px; color: var(--text-dim); }
.dim-bar {
  flex: 1;
  height: 16px;
  background: var(--bg-bar);
  border-radius: 3px;
  overflow: hidden;
  margin: 0 0.5rem;
}
.dim-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s;
}
.dim-pct { width: 60px; text-align: right; font-size: 0.8rem; }
.group-label {
  font-size: 0.75rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-top: 1rem;
  margin-bottom: 0.3rem;
}
.finding {
  padding: 0.75rem;
  margin: 0.5rem 0;
  border-left: 3px solid;
  background: rgba(255,255,255,0.02);
  border-radius: 0 4px 4px 0;
  font-size: 0.85rem;
}
.finding .file { color: var(--text-dim); font-size: 0.75rem; }
.finding .compliance { color: var(--text-dim); font-size: 0.7rem; font-style: italic; }
.finding .remediation { color: var(--accent); font-size: 0.75rem; margin-top: 0.25rem; }
.trap-box {
  border: 2px solid var(--critical);
  background: rgba(231,76,60,0.05);
}
.trap-box .citation {
  color: var(--text-dim);
  font-size: 0.8rem;
  font-style: italic;
  margin: 0.5rem 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.7rem;
}
th, td {
  padding: 0.3rem 0.4rem;
  border: 1px solid var(--border);
  text-align: center;
}
th { background: var(--bg-bar); color: var(--accent); }
.footer {
  text-align: center;
  color: var(--text-dim);
  font-size: 0.75rem;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}
</style>"""


def _header(result: ScanResult, timestamp: str, level_color: str) -> str:
    return f"""
<div class="header">
  <div style="font-size:0.9rem;color:var(--text-dim)">Warden v{__version__} — AI Agent Governance Scanner</div>
  <div class="score-big" style="color:{level_color}">{result.total_score} / 100</div>
  <div class="level-badge" style="background:{level_color};color:#fff">{result.level.value}</div>
  <div style="margin-top:0.5rem;color:var(--text-dim);font-size:0.8rem">
    Scanned: {result.target_path}<br>{timestamp}
  </div>
</div>"""


def _dimension_bars(result: ScanResult) -> str:
    rows = []
    for group_name, dims in GROUPS.items():
        rows.append(f'<div class="group-label">{group_name}</div>')
        for dim in dims:
            ds = result.dimension_scores.get(dim.id)
            if not ds:
                continue
            pct = ds.pct
            color = "#27ae60" if pct >= 80 else "#f39c12" if pct >= 50 else "#e74c3c"
            rows.append(f"""<div class="dim-row">
  <span class="dim-label">{dim.id} {dim.name}</span>
  <div class="dim-bar"><div class="dim-fill" style="width:{pct}%;background:{color}"></div></div>
  <span class="dim-pct">{pct}% ({ds.raw}/{ds.max})</span>
</div>""")

    return f'<div class="section"><h2>17 Dimension Scores</h2>{"".join(rows)}</div>'


def _findings_section(result: ScanResult) -> str:
    if not result.findings:
        return '<div class="section"><h2>Findings</h2><p>No findings.</p></div>'

    items = []
    for severity in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW):
        sev_findings = [f for f in result.findings if f.severity == severity]
        if not sev_findings:
            continue
        color = SEVERITY_COLORS[severity]
        for f in sev_findings:
            compliance_parts = []
            if f.compliance.eu_ai_act:
                compliance_parts.append(f"EU AI Act {f.compliance.eu_ai_act}")
            if f.compliance.owasp_llm:
                compliance_parts.append(f"OWASP {f.compliance.owasp_llm}")
            if f.compliance.mitre_atlas:
                compliance_parts.append(f"ATLAS {f.compliance.mitre_atlas}")
            compliance_str = " · ".join(compliance_parts)

            file_str = f'<div class="file">{f.file}:{f.line}</div>' if f.file and f.line else ""
            compliance_div = f'<div class="compliance">{compliance_str}</div>' if compliance_str else ""

            items.append(f"""<div class="finding" style="border-color:{color}">
  <strong style="color:{color}">{severity.value}</strong> {_escape(f.message)}
  {file_str}{compliance_div}
  <div class="remediation">{_escape(f.remediation)}</div>
</div>""")

    count = len(result.findings)
    return f'<div class="section"><h2>Findings ({count})</h2>{"".join(items)}</div>'


def _trap_defense_box(result: ScanResult) -> str:
    d17 = result.dimension_scores.get("D17")
    if not d17:
        return ""

    td = result.trap_defense
    checks = [
        ("Content injection defense", td.content_injection, "CRITICAL", "86% attack success rate"),
        ("RAG poisoning protection", td.rag_poisoning, "CRITICAL", "<0.1% contamination = >80% success"),
        ("Behavioral trap detection", td.behavioral_traps, "HIGH", "10/10 M365 Copilot attacks"),
        ("Approval integrity verification", td.approval_integrity, "HIGH", "Approval fatigue exploitation"),
        ("Adversarial testing (OWASP)", td.adversarial_testing, "MEDIUM", ""),
        ("Tool-call attack simulation", td.tool_attack_simulation, "MEDIUM", ""),
        ("Multi-agent chaos engineering", td.chaos_engineering, "MEDIUM", ""),
        ("Before/after governance comparison", td.before_after_comparison, "MEDIUM", ""),
    ]

    rows = []
    for name, present, sev, stat in checks:
        if present:
            rows.append(f'<div style="color:var(--green);margin:0.3rem 0">&#10003; {name}</div>')
        else:
            color = SEVERITY_COLORS.get(Severity(sev), "#999")
            stat_str = f" — {stat}" if stat else ""
            rows.append(f'<div style="color:{color};margin:0.3rem 0">&#10007; {name}{stat_str}</div>')

    citation = ""
    if d17.raw == 0:
        citation = """<div class="citation">
  &#9888; Your environment is exposed to 6 trap types with documented 80%+ attack success rates.<br>
  <cite>Franklin, Toma&scaron;ev, Jacobs, Leibo, Osindero. &ldquo;AI Agent Traps.&rdquo; Google DeepMind, March 2026.</cite>
</div>"""

    return f"""<div class="section trap-box">
  <h2>D17: Adversarial Resilience — {d17.raw} / {d17.max}</h2>
  {citation}
  {"".join(rows)}
</div>"""


def _competitor_section(result: ScanResult) -> str:
    if not result.competitors:
        return '<div class="section"><h2>Governance Tools Detected</h2><p>None detected.</p></div>'

    rows = []
    for c in result.competitors:
        conf_color = {"high": "var(--green)", "medium": "var(--medium)", "low": "var(--text-dim)"}.get(c.confidence, "var(--text)")
        strengths = ", ".join(c.strengths[:3]) if c.strengths else "—"
        weaknesses = ", ".join(c.weaknesses[:2]) if c.weaknesses else "—"
        rows.append(f"""<tr>
  <td style="text-align:left">{_escape(c.display_name)}</td>
  <td>{c.category}</td>
  <td style="color:{conf_color}">{c.confidence}</td>
  <td>{c.warden_score}</td>
  <td style="text-align:left;font-size:0.65rem">{_escape(strengths)}</td>
  <td style="text-align:left;font-size:0.65rem">{_escape(weaknesses)}</td>
</tr>""")

    return f"""<div class="section">
  <h2>Governance Tools Detected</h2>
  <table>
    <tr><th>Tool</th><th>Category</th><th>Confidence</th><th>Score</th><th>Strengths</th><th>Weaknesses</th></tr>
    {"".join(rows)}
  </table>
</div>"""


def _market_table(result: ScanResult) -> str:
    """Full 17x17 market comparison table."""
    # Market scores from spec Section 6
    market_data = [
        ("SharkRouter", "Full gateway", [100,100,100,90,100,100,100,100,100,67,40,70,50,90,100,90,90], 91),
        ("Zenity", "Agent gov.", [56,60,65,40,70,40,47,27,50,53,90,70,20,80,10,20,10], 48),
        ("Wiz", "Cloud AI-SPM", [40,40,50,75,60,60,13,13,40,27,100,50,20,90,0,30,10], 41),
        ("Oasis", "NHI access", [32,50,40,80,50,40,20,53,30,20,70,30,20,70,0,20,0], 38),
        ("Lasso/Noma", "Agent monitor", [28,40,35,25,50,60,20,20,35,40,40,50,10,40,0,10,10], 30),
        ("Kong", "API gateway", [16,15,40,30,50,40,13,7,15,33,80,70,10,70,0,0,0], 27),
        ("Robust/Cisco", "AI firewall", [12,35,25,25,40,60,13,7,25,40,60,40,10,80,0,10,10], 26),
        ("Rubrik", "Data+agents", [12,20,15,25,50,20,13,13,25,13,60,30,100,70,20,10,0], 26),
        ("Portkey", "LLM gateway", [20,20,25,20,40,80,13,7,15,33,60,100,10,30,0,0,0], 24),
        ("Pangea/CS", "Prompt layer", [8,15,15,25,50,40,0,0,15,73,60,30,10,80,0,20,0], 23),
        ("NeuralTrust", "LLM gateway", [16,30,25,20,40,40,13,7,25,47,30,50,10,30,0,10,10], 23),
        ("Knostic", "Agent monitor", [20,25,25,20,30,40,20,13,25,33,30,40,10,30,0,10,0], 22),
        ("Prompt Sec", "Prompt layer", [8,25,15,15,30,40,7,0,20,87,40,40,0,50,0,10,0], 21),
        ("CF/Envoy", "Proxy", [8,10,25,20,40,20,0,0,15,27,90,50,0,80,0,0,0], 20),
        ("mcp-scan", "Vuln scanner", [32,20,10,25,20,40,0,0,15,20,50,20,0,60,0,0,10], 18),
        ("Lakera", "Prompt layer", [4,10,10,10,20,20,0,0,10,73,30,20,0,40,0,0,0], 13),
        ("aiFWall", "Prompt FW", [8,15,15,10,20,20,7,0,15,33,20,20,0,20,0,0,0], 11),
    ]

    dim_headers = "".join(f"<th>D{i}</th>" for i in range(1, 18))
    rows = []
    for name, cat, scores, total in market_data:
        cells = "".join(
            f'<td style="color:{"var(--green)" if s >= 80 else "var(--medium)" if s >= 50 else "var(--critical)" if s > 0 else "var(--text-dim)"}">{s}%</td>'
            for s in scores
        )
        rows.append(f"<tr><td style='text-align:left'>{_escape(name)}</td><td>{cat}</td>{cells}<td><strong>{total}</strong></td></tr>")

    return f"""<div class="section">
  <h2>Market Comparison (17 vendors x 17 dimensions)</h2>
  <div style="overflow-x:auto">
  <table>
    <tr><th>Vendor</th><th>Category</th>{dim_headers}<th>/100</th></tr>
    {"".join(rows)}
  </table>
  </div>
</div>"""


def _comparison_panel(result: ScanResult) -> str:
    """Show current score vs SharkRouter score with per-dimension delta."""
    shark_pcts = {
        "D1": 100, "D2": 100, "D3": 100, "D4": 90, "D5": 100, "D6": 100,
        "D7": 100, "D8": 100, "D9": 100, "D10": 67, "D11": 40, "D12": 70,
        "D13": 50, "D14": 90, "D15": 100, "D16": 90, "D17": 90,
    }

    rows = []
    for dim in ALL_DIMENSIONS:
        ds = result.dimension_scores.get(dim.id)
        if not ds:
            continue
        current_pct = ds.pct
        shark_pct = shark_pcts.get(dim.id, 0)
        delta = shark_pct - current_pct
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        delta_color = "var(--green)" if delta > 0 else "var(--text-dim)"
        rows.append(f"""<tr>
  <td style="text-align:left">{dim.id} {dim.name}</td>
  <td>{current_pct}%</td>
  <td>{shark_pct}%</td>
  <td style="color:{delta_color}">{delta_str}%</td>
</tr>""")

    return f"""<div class="section">
  <h2>Score Comparison: You vs SharkRouter</h2>
  <div style="text-align:center;margin-bottom:1rem">
    <span style="font-size:2rem;color:var(--critical)">{result.total_score}</span>
    <span style="color:var(--text-dim);margin:0 1rem">&#8594;</span>
    <span style="font-size:2rem;color:var(--green)">91</span>
  </div>
  <table>
    <tr><th>Dimension</th><th>Current</th><th>+ SharkRouter</th><th>Delta</th></tr>
    {"".join(rows)}
  </table>
</div>"""


def _recommendations(result: ScanResult) -> str:
    """Top 3 recommendations by point impact."""
    from warden.scoring.dimensions import DIMENSIONS_BY_ID

    gaps: list[tuple[str, int, str]] = []
    for dim_id, ds in result.dimension_scores.items():
        gap = ds.max - ds.raw
        if gap > 0:
            dim = DIMENSIONS_BY_ID.get(dim_id)
            if dim:
                gaps.append((dim_id, gap, dim.name))

    gaps.sort(key=lambda x: x[1], reverse=True)
    top = gaps[:3]

    if not top:
        return ""

    items = []
    for i, (did, gap, name) in enumerate(top, 1):
        items.append(f"""<div style="margin:0.5rem 0;padding:0.5rem;background:rgba(88,166,255,0.05);border-radius:4px">
  <strong>{i}. {did}: {name}</strong> — {gap} points available
</div>""")

    return f"""<div class="section">
  <h2>Top Recommendations</h2>
  {"".join(items)}
  <div style="margin-top:1rem;color:var(--text-dim);font-size:0.8rem">
    Your actual governance posture may be higher — Warden scores conservatively based on detected patterns.
  </div>
</div>"""


def _footer(timestamp: str) -> str:
    return f"""<div class="footer">
  Warden v{__version__} · Scoring Model v{__scoring_model__} · Generated {timestamp}<br>
  <cite>Adversarial resilience research: Franklin, Toma&scaron;ev, Jacobs, Leibo, Osindero.
  &ldquo;AI Agent Traps.&rdquo; Google DeepMind, March 2026.</cite><br>
  <a href="https://github.com/SharkRouter/warden" style="color:var(--accent)">github.com/SharkRouter/warden</a>
</div>"""


def _escape(text: str) -> str:
    """HTML-escape text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
