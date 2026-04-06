"""Rich-based terminal output for scan results."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from warden.models import ScanResult, Severity, ScoreLevel
from warden.scoring.dimensions import GROUPS


SEVERITY_COLORS = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW: "dim",
}

LEVEL_COLORS = {
    ScoreLevel.GOVERNED: "bold green",
    ScoreLevel.PARTIAL: "yellow",
    ScoreLevel.AT_RISK: "red",
    ScoreLevel.UNGOVERNED: "bold red",
}


def print_detailed(result: ScanResult, console: Console | None = None) -> None:
    """Print detailed scan results to terminal."""
    if console is None:
        console = Console()

    # Score header
    level_color = LEVEL_COLORS.get(result.level, "white")
    console.print()
    console.print(
        Panel(
            f"[{level_color}]{result.total_score} / 100 — {result.level.value}[/]",
            title="Governance Score",
            width=50,
        )
    )

    # Dimension breakdown
    console.print("\n[bold]Dimension Scores[/]")
    for group_name, dims in GROUPS.items():
        console.print(f"\n  [dim]{group_name}[/]")
        for dim in dims:
            ds = result.dimension_scores.get(dim.id)
            if ds:
                pct = ds.pct
                bar_filled = pct // 5
                bar_empty = 20 - bar_filled
                color = "green" if pct >= 80 else "yellow" if pct >= 50 else "red"
                bar = f"[{color}]{'█' * bar_filled}[/][dim]{'░' * bar_empty}[/]"
                console.print(f"    {dim.id:4} {dim.name:25} {bar} {pct:3}% ({ds.raw}/{ds.max})")

    # Top findings
    if result.findings:
        console.print(f"\n[bold]Findings ({len(result.findings)} total)[/]\n")
        # Group by severity
        for severity in (Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW):
            sev_findings = [f for f in result.findings if f.severity == severity]
            if not sev_findings:
                continue
            color = SEVERITY_COLORS[severity]
            console.print(f"  [{color}]{severity.value} ({len(sev_findings)})[/]")
            for finding in sev_findings[:5]:  # Show top 5 per severity
                console.print(f"    [{color}]✗[/] {finding.message}")
                if finding.file and finding.line:
                    console.print(f"      {finding.file}:{finding.line}")
            if len(sev_findings) > 5:
                console.print(f"    ... and {len(sev_findings) - 5} more")

    # Competitors
    if result.competitors:
        console.print("\n[bold]Governance Tools Detected[/]\n")
        table = Table(show_header=True)
        table.add_column("Tool", style="cyan")
        table.add_column("Category")
        table.add_column("Confidence")
        table.add_column("Score", justify="right")
        for comp in result.competitors:
            conf_color = {"high": "green", "medium": "yellow", "low": "dim"}.get(comp.confidence, "white")
            table.add_row(
                comp.display_name,
                comp.category,
                f"[{conf_color}]{comp.confidence}[/]",
                str(comp.warden_score),
            )
        console.print(table)

    # D17 trap defense warning
    d17 = result.dimension_scores.get("D17")
    if d17 and d17.raw == 0:
        console.print()
        console.print(Panel(
            "[bold red]Your environment is exposed to 6 trap types with\n"
            "documented 80%+ attack success rates.[/]\n\n"
            "[dim]Franklin, Tomašev, Jacobs, Leibo, Osindero.\n"
            '"AI Agent Traps." Google DeepMind, March 2026.[/]',
            title="D17: Adversarial Resilience — 0/10",
            border_style="red",
        ))
