"""Tests for fefo_core.risk (hand-computed fixture values + generated scenarios)."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pytest

from fefo_core.features import build
from fefo_core.forecast import build_forecasts
from fefo_core.loader import load_tables
from fefo_core.risk import risk_all, risk_level, risky_items
from schemas import REASON_CODES, RISK_ITEM_FIELDS

APP_DIR = Path(__file__).resolve().parents[1]
FIXTURE = APP_DIR / "tests" / "fixtures" / "data"
GENERATED = APP_DIR / "data"
SCENARIOS = APP_DIR.parents[1].parent / "data-gen" / "out" / "scenarios" / "scenarios.csv"


def _run(data_dir: Path, as_of: date):
    t = load_tables(data_dir)
    f = build(t, as_of)
    return risk_all(t, f, build_forecasts(f, t.params), as_of)


@pytest.fixture(scope="module")
def fixture_items():
    return {i["lot_id"]: i for i in _run(FIXTURE, date(2026, 11, 26))}


@pytest.fixture(scope="module")
def generated_items():
    return _run(GENERATED, date(2026, 11, 25))


def test_item_shape_matches_schema(fixture_items):
    for item in fixture_items.values():
        assert tuple(item) == RISK_ITEM_FIELDS
        assert set(item["reason_codes"]) <= set(REASON_CODES)


def test_fixture_lot_exact_values(fixture_items):
    # SKU-004 (DRY, price 12.00), lot 400 units expiring 2027-02-03, as_of Thu 2026-11-26.
    # Rules DRY: BAYI-01 min 45, BAYI-02 min 22 -> window = days with >= 22 left = 48.
    # Both dealers eligible while >= 45 left (25 days), then only BAYI-02
    # (30-day share 171/332). Weekday totals (all bands equal): Mon 11, Tue 13,
    # Wed 15, Thu 13, Fri 11, Sat 13, Sun 0. Lot mix = 1 (only lot shipped).
    # Demand = 394.795... -> at risk round(400 - 394.795) = 5, loss 5 * 12 = 60.
    i = fixture_items["LOT-SKU-004-2"]
    assert i["sellable_window_days"] == 48
    assert i["days_to_expiry"] == 69
    assert i["forecast_units_in_window"]["expected"] == pytest.approx(394.8, abs=0.01)
    assert i["at_risk_units"] == {"low": 5, "expected": 5, "high": 5}
    assert i["loss_try"] == {"low": 60.0, "expected": 60.0, "high": 60.0}
    assert i["risk_level"] == "LOW"
    assert i["reason_codes"] == []
    assert i["forecast_confidence"] == "HIGH"
    assert i["sku_name"] == "Bisküvi 200 g"
    assert i["location_bin"] == "A-02-1"


def test_lot_never_shipped_last_7_days_has_zero_mix(fixture_items):
    # LOT-SKU-002-3: 66 units, 19 days left, COLD min 5 -> window 15; mix 0 -> demand 0.
    i = fixture_items["LOT-SKU-002-3"]
    assert i["sellable_window_days"] == 15
    assert i["forecast_units_in_window"] == {"low": 0.0, "expected": 0.0, "high": 0.0}
    assert i["at_risk_units"]["expected"] == 66
    assert i["loss_try"]["expected"] == 66 * 28.0


def test_bands_ordered_and_sorted(fixture_items):
    items = list(fixture_items.values())
    for i in items:
        for key in ("at_risk_units", "loss_try"):
            assert i[key]["low"] <= i[key]["expected"] <= i[key]["high"]
    keys = [(-i["loss_try"]["expected"], i["lot_id"]) for i in items]
    assert keys == sorted(keys)


def test_risk_level_thresholds():
    p = {"risk_level_thresholds_try": {"medium_min": 2000, "high_min": 10000}}
    assert risk_level(1999.99, p) == "LOW"
    assert risk_level(2000, p) == "MEDIUM"
    assert risk_level(9999.99, p) == "MEDIUM"
    assert risk_level(10000, p) == "HIGH"


def test_risky_items_filter():
    mk = lambda e, h, c: {"at_risk_units": {"expected": e, "high": h}, "forecast_confidence": c}
    items = [mk(3, 5, "HIGH"), mk(0, 4, "LOW"), mk(0, 4, "HIGH"), mk(0, 0, "LOW")]
    assert risky_items(items) == [items[0]]
    assert risky_items(items, include_low_confidence=True) == [items[0], items[1]]


# ---------------------------------------------------------------- generated data

def test_generated_top_lot(generated_items):
    top = generated_items[0]
    assert top["lot_id"] == "LOT-SKU-001-3"
    assert top["loss_try"]["expected"] == pytest.approx(40242, rel=0.01)


def test_generated_scenarios(generated_items):
    by_lot = {i["lot_id"]: i for i in generated_items}
    risky = {i["lot_id"] for i in risky_items(generated_items)}
    with SCENARIOS.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 8
    for row in rows:
        item = by_lot[row["lot_id"]]
        if row["expected_reason_code"]:
            assert row["expected_reason_code"] in item["reason_codes"], row
            assert row["lot_id"] in risky, row
        if row["scenario"] == "CONTROL":
            assert item["at_risk_units"]["expected"] == 0
            assert row["lot_id"] not in risky
        if row["scenario"] == "LOW_CONFIDENCE":
            assert item["forecast_confidence"] == "LOW"
            assert item["loss_try"]["expected"] > 0
            assert row["lot_id"] in risky
