"""Self-contained HTML report generation.

CRITICAL: No external requests. All CSS and layout are embedded.
Air-gapped environments work perfectly — system font stack only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from warden import __scoring_model__, __version__
from warden.models import ScanResult, ScoreLevel, Severity
from warden.scoring.dimensions import DIMENSIONS_BY_ID, GROUPS

SEVERITY_COLORS = {
    Severity.CRITICAL: "#EF4444",
    Severity.HIGH: "#F59E0B",
    Severity.MEDIUM: "#3B82F6",
    Severity.LOW: "#6B7280",
}

LEVEL_COLORS = {
    ScoreLevel.GOVERNED: "#22C55E",
    ScoreLevel.PARTIAL: "#F59E0B",
    ScoreLevel.AT_RISK: "#F59E0B",
    ScoreLevel.UNGOVERNED: "#EF4444",
}

LEVEL_CSS_CLASS = {
    ScoreLevel.GOVERNED: "level-governed",
    ScoreLevel.PARTIAL: "level-partial",
    ScoreLevel.AT_RISK: "level-at-risk",
    ScoreLevel.UNGOVERNED: "level-ungoverned",
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
        _benchmark_bar(result),
        _dimension_section(result),
        _findings_section(result),
        _trap_defense_box(result),
        _top_actions(result),
        _detected_tools(result),
        _market_table(result),
        _scan_stats(result, timestamp),
        _footer(timestamp),
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
<div class="container">
{''.join(sections)}
</div>
{_js()}
</body>
</html>"""


def _css() -> str:
    return """<style>
:root {
  --bg: #0A0D16;
  --surface: #111827;
  --surface2: #1A2235;
  --border: rgba(255,255,255,0.06);
  --text: #E2E8F0;
  --text-muted: #64748B;
  --teal: #00ACC1;
  --teal-dim: rgba(0,172,193,0.15);
  --red: #EF4444;
  --red-dim: rgba(239,68,68,0.12);
  --amber: #F59E0B;
  --amber-dim: rgba(245,158,11,0.12);
  --green: #22C55E;
  --green-dim: rgba(34,197,94,0.12);
  --blue: #3B82F6;
  --blue-dim: rgba(59,130,246,0.12);
  --mono: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  --sans: 'DM Sans', -apple-system, 'Segoe UI', sans-serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--sans); background: var(--bg); color: var(--text); line-height: 1.6; }
.container { max-width: 1100px; margin: 0 auto; padding: 0 24px; }

/* HEADER */
.header { padding: 40px 0 32px; border-bottom: 1px solid var(--border); }
.header-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.logo { font-family: var(--mono); font-size: 14px; font-weight: 700; color: var(--teal); letter-spacing: 2px; }
.timestamp { font-family: var(--mono); font-size: 11px; color: var(--text-muted); }

/* SCORE HERO */
.score-hero { display: flex; align-items: center; gap: 48px; }
.score-ring { position: relative; width: 180px; height: 180px; flex-shrink: 0; }
.score-ring svg { transform: rotate(-90deg); }
.score-ring .bg-ring { fill: none; stroke: #1E293B; stroke-width: 8; }
.score-ring .fg-ring { fill: none; stroke-width: 8; stroke-linecap: round; }
.score-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.score-number { font-family: var(--mono); font-size: 52px; font-weight: 700; }
.score-max { font-family: var(--mono); font-size: 14px; color: var(--text-muted); }
.score-details h2 { font-size: 20px; margin-bottom: 8px; }
.score-details .level { font-family: var(--mono); font-size: 13px; font-weight: 700; padding: 4px 12px; border-radius: 4px; display: inline-block; margin-bottom: 12px; }
.level-ungoverned { background: var(--red-dim); color: var(--red); }
.level-at-risk { background: var(--amber-dim); color: var(--amber); }
.level-partial { background: var(--amber-dim); color: var(--amber); }
.level-governed { background: var(--green-dim); color: var(--green); }
.score-meta { font-size: 13px; color: var(--text-muted); line-height: 2; }
.score-meta strong { color: var(--text); }

/* SECTIONS */
.section { padding: 32px 0; border-bottom: 1px solid var(--border); }
.section-title { font-size: 14px; font-weight: 600; margin-bottom: 16px; color: var(--text-muted); letter-spacing: 1px; text-transform: uppercase; }

/* BENCHMARK */
.bench-row { margin-bottom: 8px; }
.bench-label { font-family: var(--mono); font-size: 11px; color: var(--text-muted); margin-bottom: 4px; display: flex; justify-content: space-between; }
.bench-bar { position: relative; height: 32px; background: #1E293B; border-radius: 6px; overflow: hidden; }
.bench-fill { height: 100%; border-radius: 6px; display: flex; align-items: center; padding-left: 12px; font-family: var(--mono); font-size: 12px; font-weight: 600; color: #000; min-width: 30px; }

/* DIMENSIONS */
.dim-tier-label { font-family: var(--mono); font-size: 11px; color: var(--teal); letter-spacing: 2px; margin: 20px 0 8px; padding: 4px 0; border-bottom: 1px solid var(--border); }
.dim-row { display: grid; grid-template-columns: 30px 1fr 60px 200px 80px; align-items: center; gap: 8px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }
.dim-id { font-family: var(--mono); font-size: 11px; color: var(--text-muted); }
.dim-name { font-size: 13px; }
.dim-score { font-family: var(--mono); font-size: 12px; text-align: right; }
.dim-bar-bg { height: 6px; background: #1E293B; border-radius: 3px; overflow: hidden; }
.dim-bar-fill { height: 100%; border-radius: 3px; }
.dim-rating { font-family: var(--mono); font-size: 10px; font-weight: 600; }
.rating-full { color: var(--teal); }
.rating-good { color: var(--green); }
.rating-partial { color: var(--amber); }
.rating-missing { color: #6B7280; }
.rating-critical { color: var(--red); }

/* FINDINGS */
.finding-group { margin-bottom: 24px; }
.finding-group-header { font-family: var(--mono); font-size: 12px; font-weight: 700; letter-spacing: 1px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; cursor: pointer; }
.finding-count { padding: 2px 8px; border-radius: 10px; font-size: 11px; }
.sev-critical .finding-count { background: var(--red-dim); color: var(--red); }
.sev-high .finding-count { background: var(--amber-dim); color: var(--amber); }
.sev-medium .finding-count { background: var(--blue-dim); color: var(--blue); }
.sev-low .finding-count { background: rgba(107,114,128,0.12); color: #6B7280; }
.finding-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; margin-bottom: 6px; cursor: pointer; transition: border-color 0.2s; }
.finding-card:hover { border-color: rgba(255,255,255,0.12); }
.finding-card .title { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
.finding-card .location { font-family: var(--mono); font-size: 11px; color: var(--teal); }
.finding-card .dim-tag { font-family: var(--mono); font-size: 10px; color: var(--text-muted); background: var(--surface2); padding: 2px 6px; border-radius: 3px; float: right; }
.finding-card .detail { font-size: 12px; color: var(--text-muted); margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); display: none; }
.finding-card.expanded .detail { display: block; }
.finding-card .detail .remediation { color: var(--teal); }
.finding-card .detail .compliance { color: var(--text-muted); font-style: italic; font-size: 11px; margin-top: 4px; }
.findings-collapse { display: none; }
.findings-collapse.open { display: block; }
.toggle-arrow { transition: transform 0.2s; display: inline-block; }
.toggle-arrow.open { transform: rotate(90deg); }

/* ACTION CARDS */
.action-card { background: var(--surface); border: 1px solid var(--border); border-left: 3px solid var(--teal); border-radius: 8px; padding: 16px 20px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
.action-number { font-family: var(--mono); font-size: 24px; font-weight: 700; color: var(--teal); margin-right: 16px; }
.action-text { font-size: 14px; }
.action-text .sub { color: var(--text-muted); font-size: 12px; }
.action-impact { font-family: var(--mono); font-size: 12px; color: var(--green); white-space: nowrap; }

/* TRAP */
.trap-box { border: 2px solid var(--red); background: rgba(239,68,68,0.03); border-radius: 8px; padding: 1.5rem; margin: 32px 0; }
.trap-box h3 { color: var(--red); margin-bottom: 12px; }
.trap-check { margin: 0.3rem 0; }

/* GOV TOOLS */
.tool-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
.tool-name { font-weight: 600; }
.tool-category { font-family: var(--mono); font-size: 11px; color: var(--amber); background: var(--amber-dim); padding: 2px 8px; border-radius: 4px; }
.tool-score { font-family: var(--mono); font-size: 12px; color: var(--text-muted); }

/* MARKET TABLE */
.market-toggle { cursor: pointer; color: var(--teal); font-size: 13px; font-family: var(--mono); margin-bottom: 12px; }
.market-table-wrap { display: none; overflow-x: auto; }
.market-table-wrap.open { display: block; }
table { width: 100%; border-collapse: collapse; font-size: 0.7rem; }
th, td { padding: 0.3rem 0.4rem; border: 1px solid var(--border); text-align: center; }
th { background: #1E293B; color: var(--teal); }

/* STATS */
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; text-align: center; }
.stat-value { font-family: var(--mono); font-size: 28px; font-weight: 700; color: var(--teal); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* FOOTER */
.footer { padding: 32px 0; text-align: center; }
.footer-text { font-size: 12px; color: var(--text-muted); line-height: 2; }
.footer-cta { display: inline-block; margin-top: 16px; background: linear-gradient(135deg, var(--teal), #0097A7); color: #000; padding: 12px 28px; border-radius: 8px; font-weight: 700; font-size: 14px; text-decoration: none; }

@media (max-width: 768px) {
  .score-hero { flex-direction: column; text-align: center; }
  .dim-row { grid-template-columns: 30px 1fr 50px 100px; }
  .dim-rating { display: none; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>"""


def _js() -> str:
    return """<script>
function toggleFinding(el){el.classList.toggle('expanded')}
function toggleGroup(id){
  var c=document.getElementById(id);
  var a=document.getElementById(id+'-arrow');
  if(c){c.classList.toggle('open');if(a)a.classList.toggle('open')}
}
function toggleMarket(){
  var w=document.getElementById('market-wrap');
  if(w)w.classList.toggle('open');
}
</script>"""


def _header(result: ScanResult, timestamp: str) -> str:
    score = result.total_score
    level = result.level
    level_color = LEVEL_COLORS.get(level, "#333")
    level_class = LEVEL_CSS_CLASS.get(level, "")

    # SVG ring calculation
    radius = 78
    circumference = 2 * 3.14159 * radius  # ~490
    offset = circumference - (score / 100) * circumference

    # Gradient based on score
    if score >= 80:
        grad_start, grad_end = "#22C55E", "#00ACC1"
    elif score >= 60:
        grad_start, grad_end = "#F59E0B", "#22C55E"
    elif score >= 33:
        grad_start, grad_end = "#EF4444", "#F59E0B"
    else:
        grad_start, grad_end = "#EF4444", "#EF4444"

    critical_count = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
    high_count = sum(1 for f in result.findings if f.severity == Severity.HIGH)

    # Project name from path
    project_name = Path(result.target_path).name

    return f"""
<div class="header">
  <div class="header-top">
    <div class="logo">WARDEN</div>
    <div class="timestamp">Scanned: {timestamp} &middot; Warden v{__version__}</div>
  </div>
  <div class="score-hero">
    <div class="score-ring">
      <svg width="180" height="180" viewBox="0 0 180 180">
        <circle class="bg-ring" cx="90" cy="90" r="{radius}"/>
        <circle class="fg-ring" cx="90" cy="90" r="{radius}"
          stroke="url(#scoreGrad)"
          stroke-dasharray="{circumference:.0f}"
          stroke-dashoffset="{offset:.0f}"/>
        <defs>
          <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="{grad_start}"/>
            <stop offset="100%" stop-color="{grad_end}"/>
          </linearGradient>
        </defs>
      </svg>
      <div class="score-center">
        <div class="score-number" style="color:{level_color}">{score}</div>
        <div class="score-max">/100</div>
      </div>
    </div>
    <div class="score-details">
      <h2>Governance Assessment</h2>
      <div class="level {level_class}">{level.value}</div>
      <div class="score-meta">
        <strong>Project:</strong> {_escape(project_name)}<br>
        <strong>Path:</strong> <span style="font-family:var(--mono);font-size:12px">{_escape(result.target_path)}</span><br>
        <strong>Total Findings:</strong> {len(result.findings)}<br>
        <strong>Critical:</strong> {critical_count} &middot;
        <strong>High:</strong> {high_count}<br>
        <strong>Scoring Model:</strong> v{__scoring_model__} (17 dimensions)
      </div>
    </div>
  </div>
</div>"""


def _benchmark_bar(result: ScanResult) -> str:
    score = result.total_score

    # Market average from the 17-vendor data
    market_avg = 28

    # Find closest competitor
    closest_name = "Zenity"
    closest_score = 48

    def _bar(label: str, value: int, color: str) -> str:
        return f"""<div class="bench-row">
  <div class="bench-label"><span>{_escape(label)}</span><span>{value}/100</span></div>
  <div class="bench-bar"><div class="bench-fill" style="width:{value}%;background:{color}">{value}</div></div>
</div>"""

    # Color for current score
    if score >= 80:
        score_color = "linear-gradient(90deg, #22C55E, #00ACC1)"
    elif score >= 60:
        score_color = "linear-gradient(90deg, #F59E0B, #22C55E)"
    else:
        score_color = "linear-gradient(90deg, #EF4444, #F59E0B)"

    project_name = Path(result.target_path).name
    return f"""
<div class="section">
  <div class="section-title">Market Benchmark</div>
  {_bar(project_name, score, score_color)}
  {_bar("Market Average (17 vendors)", market_avg, "#475569")}
  {_bar(f"Closest Competitor ({closest_name})", closest_score, "#F59E0B")}
  {_bar("SharkRouter Gateway", 91, "linear-gradient(90deg, #00ACC1, #22C55E)")}
</div>"""


def _dimension_section(result: ScanResult) -> str:
    rows = []
    for group_name, dims in GROUPS.items():
        rows.append(f'<div class="dim-tier-label">{_escape(group_name)}</div>')
        for dim in dims:
            ds = result.dimension_scores.get(dim.id)
            if not ds:
                continue
            pct = ds.pct

            # Color + rating
            if pct >= 90:
                color, rating_class, rating_text = "var(--teal)", "rating-full", "FULL"
            elif pct >= 70:
                color, rating_class, rating_text = "var(--green)", "rating-good", "GOOD"
            elif pct >= 40:
                color, rating_class, rating_text = "var(--amber)", "rating-partial", "PARTIAL"
            elif pct > 0:
                color, rating_class, rating_text = "var(--red)", "rating-critical", "WEAK"
            else:
                color, rating_class, rating_text = "var(--red)", "rating-missing", "MISSING"

            icon = "&check;" if pct >= 70 else "&cir;" if pct >= 40 else "&cross;"
            rows.append(f"""<div class="dim-row">
  <div class="dim-id">{dim.id}</div>
  <div class="dim-name">{_escape(dim.name)}</div>
  <div class="dim-score">{ds.raw}/{ds.max}</div>
  <div class="dim-bar-bg"><div class="dim-bar-fill" style="width:{pct}%;background:{color}"></div></div>
  <div class="dim-rating {rating_class}">{icon} {rating_text}</div>
</div>""")

    return f"""
<div class="section">
  <div class="section-title">17 Dimension Scores</div>
  {''.join(rows)}
</div>"""


def _findings_section(result: ScanResult) -> str:
    if not result.findings:
        return '<div class="section"><div class="section-title">Findings</div><p>No findings.</p></div>'

    groups = []
    for severity in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW):
        sev_findings = [f for f in result.findings if f.severity == severity]
        if not sev_findings:
            continue

        sev_lower = severity.value.lower()
        sev_class = f"sev-{sev_lower}"
        color = SEVERITY_COLORS[severity]
        group_id = f"findings-{sev_lower}"

        # Build finding cards — show first 10 inline, rest hidden
        cards = []
        for i, f in enumerate(sev_findings):
            compliance_parts = []
            if f.compliance.eu_ai_act:
                compliance_parts.append(f"EU AI Act {f.compliance.eu_ai_act}")
            if f.compliance.owasp_llm:
                compliance_parts.append(f"OWASP {f.compliance.owasp_llm}")
            if f.compliance.mitre_atlas:
                compliance_parts.append(f"ATLAS {f.compliance.mitre_atlas}")
            compliance_str = " &middot; ".join(compliance_parts)

            location = ""
            if f.file and f.line:
                # Shorten path for display
                short = f.file
                if len(short) > 60:
                    short = "..." + short[-57:]
                location = f'<div class="location">{_escape(short)}:{f.line}</div>'

            compliance_div = ""
            if compliance_str:
                compliance_div = f'<div class="compliance">{compliance_str}</div>'

            cards.append(f"""<div class="finding-card" onclick="toggleFinding(this)">
  <div class="dim-tag">{f.dimension}</div>
  <div class="title" style="color:{color}">{_escape(f.message)}</div>
  {location}
  <div class="detail">
    <div class="remediation">{_escape(f.remediation)}</div>
    {compliance_div}
  </div>
</div>""")

        # Show first 5 always, rest collapsed
        visible_count = 5
        visible = "\n".join(cards[:visible_count])
        hidden = ""
        if len(cards) > visible_count:
            remaining = len(cards) - visible_count
            hidden_cards = "\n".join(cards[visible_count:])
            hidden = f"""<div id="{group_id}-more" class="findings-collapse">
  {hidden_cards}
</div>
<div class="market-toggle" onclick="toggleGroup('{group_id}-more')" style="margin-top:8px">
  <span id="{group_id}-more-arrow" class="toggle-arrow">&#9654;</span> Show {remaining} more {severity.value} findings
</div>"""

        groups.append(f"""<div class="finding-group {sev_class}">
  <div class="finding-group-header" style="color:{color}" onclick="toggleGroup('{group_id}')">
    <span id="{group_id}-arrow" class="toggle-arrow open">&#9654;</span>
    {severity.value} <span class="finding-count">{len(sev_findings)}</span>
  </div>
  <div id="{group_id}" class="findings-collapse open">
    {visible}
    {hidden}
  </div>
</div>""")

    total = len(result.findings)
    return f"""
<div class="section">
  <div class="section-title">Findings ({total})</div>
  {''.join(groups)}
</div>"""


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
            rows.append(f'<div class="trap-check" style="color:var(--green)">&#10003; {name}</div>')
        else:
            color = SEVERITY_COLORS.get(Severity(sev), "#999")
            stat_str = f" &mdash; {stat}" if stat else ""
            rows.append(f'<div class="trap-check" style="color:{color}">&#10007; {name}{stat_str}</div>')

    citation = ""
    if d17.raw == 0:
        citation = (
            '<div style="color:var(--text-muted);font-size:12px;font-style:italic;'
            'margin:12px 0;padding:8px;background:var(--red-dim);border-radius:4px">'
            '&#9888; Your environment is exposed to 6 trap types with '
            'documented 80%+ attack success rates.<br>'
            '<cite>Franklin, Toma&scaron;ev, Jacobs, Leibo, Osindero. '
            '&ldquo;AI Agent Traps.&rdquo; Google DeepMind, March 2026.'
            '</cite></div>'
        )

    return f"""
<div class="trap-box">
  <h3>D17: Adversarial Resilience &mdash; {d17.raw} / {d17.max}</h3>
  {citation}
  {''.join(rows)}
</div>"""


def _top_actions(result: ScanResult) -> str:
    """Top 3 recommendations by point impact."""
    gaps: list[tuple[str, int, str, str]] = []
    for dim_id, ds in result.dimension_scores.items():
        gap = ds.max - ds.raw
        if gap > 0:
            dim = DIMENSIONS_BY_ID.get(dim_id)
            if dim:
                gaps.append((dim_id, gap, dim.name, dim.description))

    gaps.sort(key=lambda x: x[1], reverse=True)
    top = gaps[:3]
    if not top:
        return ""

    running_score = result.total_score
    items = []
    for i, (did, gap, name, desc) in enumerate(top, 1):
        # Estimate rough score improvement (gap is raw points, score is normalized)
        est_pts = max(1, gap * 100 // 235)
        running_score += est_pts
        items.append(f"""<div class="action-card">
  <div style="display:flex;align-items:center">
    <div class="action-number">{i}</div>
    <div class="action-text">
      <strong>{did}: {_escape(name)}</strong><br>
      <span class="sub">{_escape(desc)}</span>
    </div>
  </div>
  <div class="action-impact">+{est_pts} pts &rarr; ~{min(running_score, 100)}/100</div>
</div>""")

    return f"""
<div class="section">
  <div class="section-title">Top Remediation Actions</div>
  {''.join(items)}
  <div style="margin-top:12px;color:var(--text-muted);font-size:12px">
    Your actual governance posture may be higher &mdash; Warden scores
    conservatively based on detected patterns.
  </div>
</div>"""


def _detected_tools(result: ScanResult) -> str:
    # Only show detected competitors (not full registry)
    detected = [c for c in result.competitors if c.confidence != "low"]

    if not detected:
        return """
<div class="section">
  <div class="section-title">Governance Tools Detected</div>
  <p style="color:var(--text-muted)">No governance tools detected in this project.</p>
</div>"""

    cards = []
    for c in detected:
        cards.append(f"""<div class="tool-card">
  <div>
    <div class="tool-name">{_escape(c.display_name)}</div>
    <div style="font-size:12px;color:var(--text-muted);margin-top:2px">
      {_escape(', '.join(c.strengths[:2]))}
    </div>
  </div>
  <div style="display:flex;gap:12px;align-items:center">
    <div class="tool-category">{_escape(c.category)}</div>
    <div class="tool-score">{c.warden_score}/100</div>
  </div>
</div>""")

    return f"""
<div class="section">
  <div class="section-title">Governance Tools Detected</div>
  {''.join(cards)}
</div>"""


def _market_table(result: ScanResult) -> str:
    """Full 17x17 market comparison — collapsible."""
    market_data = [
        ("SharkRouter", "Full gateway", [100, 100, 100, 90, 100, 100, 100, 100, 100, 67, 40, 70, 50, 90, 100, 90, 90], 91),
        ("Zenity", "Agent gov.", [56, 60, 65, 40, 70, 40, 47, 27, 50, 53, 90, 70, 20, 80, 10, 20, 10], 48),
        ("Wiz", "Cloud AI-SPM", [40, 40, 50, 75, 60, 60, 13, 13, 40, 27, 100, 50, 20, 90, 0, 30, 10], 41),
        ("Oasis", "NHI access", [32, 50, 40, 80, 50, 40, 20, 53, 30, 20, 70, 30, 20, 70, 0, 20, 0], 38),
        ("Lasso/Noma", "Agent mon.", [28, 40, 35, 25, 50, 60, 20, 20, 35, 40, 40, 50, 10, 40, 0, 10, 10], 30),
        ("Kong", "API gateway", [16, 15, 40, 30, 50, 40, 13, 7, 15, 33, 80, 70, 10, 70, 0, 0, 0], 27),
        ("Robust/Cisco", "AI firewall", [12, 35, 25, 25, 40, 60, 13, 7, 25, 40, 60, 40, 10, 80, 0, 10, 10], 26),
        ("Rubrik", "Data+agents", [12, 20, 15, 25, 50, 20, 13, 13, 25, 13, 60, 30, 100, 70, 20, 10, 0], 26),
        ("Portkey", "LLM gateway", [20, 20, 25, 20, 40, 80, 13, 7, 15, 33, 60, 100, 10, 30, 0, 0, 0], 24),
        ("Pangea/CS", "Prompt layer", [8, 15, 15, 25, 50, 40, 0, 0, 15, 73, 60, 30, 10, 80, 0, 20, 0], 23),
        ("NeuralTrust", "LLM gateway", [16, 30, 25, 20, 40, 40, 13, 7, 25, 47, 30, 50, 10, 30, 0, 10, 10], 23),
        ("Knostic", "Agent mon.", [20, 25, 25, 20, 30, 40, 20, 13, 25, 33, 30, 40, 10, 30, 0, 10, 0], 22),
        ("Prompt Sec", "Prompt layer", [8, 25, 15, 15, 30, 40, 7, 0, 20, 87, 40, 40, 0, 50, 0, 10, 0], 21),
        ("CF/Envoy", "Proxy", [8, 10, 25, 20, 40, 20, 0, 0, 15, 27, 90, 50, 0, 80, 0, 0, 0], 20),
        ("mcp-scan", "Vuln scanner", [32, 20, 10, 25, 20, 40, 0, 0, 15, 20, 50, 20, 0, 60, 0, 0, 10], 18),
        ("Lakera", "Prompt layer", [4, 10, 10, 10, 20, 20, 0, 0, 10, 73, 30, 20, 0, 40, 0, 0, 0], 13),
        ("aiFWall", "Prompt FW", [8, 15, 15, 10, 20, 20, 7, 0, 15, 33, 20, 20, 0, 20, 0, 0, 0], 11),
    ]

    dim_headers = "".join(f"<th>D{i}</th>" for i in range(1, 18))
    rows = []
    for name, cat, scores, total in market_data:
        cells = "".join(
            f'<td style="color:{"var(--green)" if s >= 80 else "var(--amber)" if s >= 50 else "var(--red)" if s > 0 else "var(--text-muted)"}">{s}%</td>'
            for s in scores
        )
        rows.append(
            f"<tr><td style='text-align:left'>{_escape(name)}</td>"
            f"<td>{cat}</td>{cells}<td><strong>{total}</strong></td></tr>"
        )

    return f"""
<div class="section">
  <div class="section-title">Market Comparison</div>
  <div class="market-toggle" onclick="toggleMarket()">
    &#9654; Show full 17-vendor &times; 17-dimension comparison table
  </div>
  <div id="market-wrap" class="market-table-wrap">
    <table>
      <tr><th>Vendor</th><th>Category</th>{dim_headers}<th>/100</th></tr>
      {''.join(rows)}
    </table>
  </div>
</div>"""


def _scan_stats(result: ScanResult, timestamp: str) -> str:
    total_findings = len(result.findings)
    unique_files = len({f.file for f in result.findings if f.file})
    dims_scored = sum(1 for d in result.dimension_scores.values() if d.raw > 0)

    return f"""
<div class="section">
  <div class="section-title">Scan Statistics</div>
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value">{total_findings}</div>
      <div class="stat-label">Findings</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{unique_files}</div>
      <div class="stat-label">Files with Findings</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{dims_scored}/17</div>
      <div class="stat-label">Dimensions Active</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">7</div>
      <div class="stat-label">Scan Layers</div>
    </div>
  </div>
</div>"""


def _footer(timestamp: str) -> str:
    return f"""
<div class="footer">
  <div class="footer-text">
    Generated by Warden v{__version__} &middot; Scoring Model v{__scoring_model__}<br>
    {timestamp} &middot; This report was generated locally. No data was transmitted.<br>
    <cite>Adversarial resilience: Franklin, Toma&scaron;ev, Jacobs, Leibo, Osindero.
    &ldquo;AI Agent Traps.&rdquo; Google DeepMind, March 2026.</cite>
  </div>
  <a href="https://sharkrouter.ai" class="footer-cta">
    See What 91/100 Looks Like &rarr;
  </a>
  <div style="margin-top:12px">
    <a href="https://github.com/SharkRouter/warden" style="color:var(--teal);font-size:12px">
      github.com/SharkRouter/warden
    </a>
  </div>
</div>"""


def _escape(text: str) -> str:
    """HTML-escape text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
