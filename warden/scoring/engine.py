"""Scoring engine: raw dimension scores -> normalized /100 score."""

from __future__ import annotations

from warden.models import DimensionScore, ScoreLevel, ScanResult
from warden.scoring.dimensions import ALL_DIMENSIONS, TOTAL_RAW_MAX, DIMENSIONS_BY_ID


def get_score_level(score: int) -> ScoreLevel:
    """Determine governance level from normalized /100 score."""
    if score >= 80:
        return ScoreLevel.GOVERNED
    elif score >= 60:
        return ScoreLevel.PARTIAL
    elif score >= 33:
        return ScoreLevel.AT_RISK
    else:
        return ScoreLevel.UNGOVERNED


def normalize_score(raw_total: int) -> int:
    """Convert raw score (/235) to normalized score (/100)."""
    return round(raw_total / TOTAL_RAW_MAX * 100)


def calculate_scores(raw_scores: dict[str, int]) -> tuple[dict[str, DimensionScore], int, ScoreLevel]:
    """Calculate dimension scores and total from raw scores.

    Args:
        raw_scores: Dict mapping dimension ID (e.g. "D1") to raw score.
                    Missing dimensions default to 0.

    Returns:
        Tuple of (dimension_scores dict, total_normalized, score_level).
    """
    dimension_scores: dict[str, DimensionScore] = {}
    raw_total = 0

    for dim in ALL_DIMENSIONS:
        raw = min(raw_scores.get(dim.id, 0), dim.max_score)  # Cap at max
        raw = max(raw, 0)  # Floor at 0
        dimension_scores[dim.id] = DimensionScore(
            name=dim.name,
            raw=raw,
            max=dim.max_score,
        )
        raw_total += raw

    total = normalize_score(raw_total)
    level = get_score_level(total)

    return dimension_scores, total, level


def apply_scores(result: ScanResult, raw_scores: dict[str, int]) -> None:
    """Apply calculated scores to a ScanResult in-place."""
    result.dimension_scores, result.total_score, result.level = calculate_scores(raw_scores)
