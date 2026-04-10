"""JSON report generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from warden import __scoring_model__, __version__
from warden.models import ScanResult


def write_json_report(result: ScanResult, output_path: Path) -> None:
    """Write machine-readable JSON report with scoring_version field."""
    report = {
        "version": __version__,
        "scoring_model": f"v{__scoring_model__}",
        "scoring_version": __scoring_model__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_path": result.target_path,
        "file_counts": result.file_counts,
        # True when zero files in a supported language were indexed. Downstream
        # tools should treat the score as a coverage failure, not a governance
        # verdict, when this flag is set.
        "coverage_warning": (
            sum(result.file_counts.values()) == 0 if result.file_counts else False
        ),
        "score": {
            "total": result.total_score,
            "max": 100,
            "level": result.level.value,
            "raw_total": sum(ds.raw for ds in result.dimension_scores.values()),
            "raw_max": 235,
            "dimensions": {
                dim_id: {
                    "name": ds.name,
                    "raw": ds.raw,
                    "max": ds.max,
                    "pct": ds.pct,
                }
                for dim_id, ds in result.dimension_scores.items()
            },
        },
        "findings": [
            {
                "layer": f.layer,
                "scanner": f.scanner,
                "file": f.file,
                "line": f.line,
                "severity": f.severity.value,
                "dimension": f.dimension,
                "message": f.message,
                "remediation": f.remediation,
                "compliance": {
                    k: v for k, v in {
                        "eu_ai_act": f.compliance.eu_ai_act,
                        "owasp_llm": f.compliance.owasp_llm,
                        "mitre_atlas": f.compliance.mitre_atlas,
                    }.items() if v
                },
            }
            for f in result.findings
        ],
        "competitors_detected": [
            {
                "id": c.id,
                "display_name": c.display_name,
                "category": c.category,
                "confidence": c.confidence,
                "score": c.warden_score,
                "signals": c.signals,
                "signal_layers": c.signal_layers,
                "strengths": c.strengths,
                "weaknesses": c.weaknesses,
            }
            for c in result.competitors
        ],
        "gtm_signal": result.gtm_signal,
        "trap_defense": {
            "content_injection": result.trap_defense.content_injection,
            "rag_poisoning": result.trap_defense.rag_poisoning,
            "behavioral_traps": result.trap_defense.behavioral_traps,
            "approval_integrity": result.trap_defense.approval_integrity,
            "adversarial_testing": result.trap_defense.adversarial_testing,
            "tool_attack_simulation": result.trap_defense.tool_attack_simulation,
            "chaos_engineering": result.trap_defense.chaos_engineering,
            "before_after_comparison": result.trap_defense.before_after_comparison,
            "deepmind_citation": result.trap_defense.deepmind_citation,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
