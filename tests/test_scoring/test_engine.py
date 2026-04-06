"""Tests for scoring engine."""

from warden.scoring.engine import get_score_level, normalize_score, calculate_scores, apply_scores
from warden.models import ScoreLevel, ScanResult


def test_score_level_governed():
    assert get_score_level(80) == ScoreLevel.GOVERNED
    assert get_score_level(100) == ScoreLevel.GOVERNED
    assert get_score_level(91) == ScoreLevel.GOVERNED


def test_score_level_partial():
    assert get_score_level(60) == ScoreLevel.PARTIAL
    assert get_score_level(79) == ScoreLevel.PARTIAL


def test_score_level_at_risk():
    assert get_score_level(33) == ScoreLevel.AT_RISK
    assert get_score_level(59) == ScoreLevel.AT_RISK


def test_score_level_ungoverned():
    assert get_score_level(0) == ScoreLevel.UNGOVERNED
    assert get_score_level(32) == ScoreLevel.UNGOVERNED


def test_normalize_zero():
    assert normalize_score(0) == 0


def test_normalize_max():
    assert normalize_score(235) == 100


def test_normalize_half():
    # 117.5 / 235 = 50%
    assert normalize_score(118) == 50  # round(118/235*100) = round(50.21) = 50


def test_calculate_scores_all_zero():
    dim_scores, total, level = calculate_scores({})
    assert total == 0
    assert level == ScoreLevel.UNGOVERNED
    assert len(dim_scores) == 17
    for ds in dim_scores.values():
        assert ds.raw == 0


def test_calculate_scores_all_max():
    from warden.scoring.dimensions import ALL_DIMENSIONS
    raw = {d.id: d.max_score for d in ALL_DIMENSIONS}
    dim_scores, total, level = calculate_scores(raw)
    assert total == 100
    assert level == ScoreLevel.GOVERNED


def test_calculate_scores_caps_at_max():
    """Scores above dimension max are capped."""
    dim_scores, _, _ = calculate_scores({"D1": 999})
    assert dim_scores["D1"].raw == 25  # D1 max is 25


def test_calculate_scores_floors_at_zero():
    """Negative scores are floored at 0."""
    dim_scores, _, _ = calculate_scores({"D1": -5})
    assert dim_scores["D1"].raw == 0


def test_dimension_score_pct():
    dim_scores, _, _ = calculate_scores({"D1": 12})
    assert dim_scores["D1"].pct == 48  # round(12/25*100)


def test_apply_scores_mutates_result():
    result = ScanResult(target_path="/test")
    apply_scores(result, {"D1": 25, "D2": 20})
    assert result.total_score > 0
    assert result.dimension_scores["D1"].raw == 25
    assert result.dimension_scores["D2"].raw == 20


def test_sharkrouter_score_91():
    """SharkRouter's own score per the spec should be ~91/100."""
    from warden.scoring.dimensions import ALL_DIMENSIONS
    # From market scores table: SharkRouter percentages
    pcts = {
        "D1": 100, "D2": 100, "D3": 100, "D4": 90, "D5": 100, "D6": 100,
        "D7": 100, "D8": 100, "D9": 100,
        "D10": 67, "D11": 40, "D12": 70, "D13": 50, "D14": 90,
        "D15": 100, "D16": 90, "D17": 90,
    }
    from warden.scoring.dimensions import DIMENSIONS_BY_ID
    raw = {}
    for did, pct in pcts.items():
        raw[did] = round(DIMENSIONS_BY_ID[did].max_score * pct / 100)

    _, total, level = calculate_scores(raw)
    # Spec says 91 but rounding from percentages→raw→normalized gives 90-91
    assert total in (90, 91), f"Expected 90-91, got {total}"
    assert level == ScoreLevel.GOVERNED
