"""Tests for dimension definitions."""

from warden.scoring.dimensions import (
    ALL_DIMENSIONS,
    DIMENSIONS_BY_ID,
    GROUPS,
    TOTAL_RAW_MAX,
)


def test_17_dimensions():
    assert len(ALL_DIMENSIONS) == 17


def test_total_raw_max_is_235():
    assert TOTAL_RAW_MAX == 235


def test_group_core_governance_is_100():
    total = sum(d.max_score for d in GROUPS["Core Governance"])
    assert total == 100


def test_group_advanced_controls_is_50():
    total = sum(d.max_score for d in GROUPS["Advanced Controls"])
    assert total == 50


def test_group_ecosystem_is_55():
    total = sum(d.max_score for d in GROUPS["Ecosystem"])
    assert total == 55


def test_group_unique_capabilities_is_30():
    total = sum(d.max_score for d in GROUPS["Unique Capabilities"])
    assert total == 30


def test_all_groups_sum_to_235():
    total = sum(
        sum(d.max_score for d in dims)
        for dims in GROUPS.values()
    )
    assert total == 235


def test_dimension_ids_sequential():
    for i, dim in enumerate(ALL_DIMENSIONS, 1):
        assert dim.id == f"D{i}"


def test_dimensions_by_id_lookup():
    for dim in ALL_DIMENSIONS:
        assert DIMENSIONS_BY_ID[dim.id] is dim


def test_every_dimension_has_description():
    for dim in ALL_DIMENSIONS:
        assert dim.description, f"{dim.id} missing description"


def test_every_dimension_has_group():
    all_grouped = []
    for dims in GROUPS.values():
        all_grouped.extend(dims)
    assert set(d.id for d in all_grouped) == set(d.id for d in ALL_DIMENSIONS)
