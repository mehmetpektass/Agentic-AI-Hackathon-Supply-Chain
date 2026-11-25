"""Tests for fefo_core.loader and fefo_core.validate on the small shared fixture."""

from __future__ import annotations

import copy
import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest

from fefo_core.loader import LoadError, load_tables
from fefo_core.validate import ValidationError, ValidationIssue, run

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "data"
APP_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def good():
    return load_tables(FIXTURE)


def _rules(issues):
    return {(i.file, i.row, i.rule) for i in issues}


def test_fixture_is_valid_and_typed(good):
    assert run(good) == []
    assert len(good.dealers) == 2 and len(good.products) == 4
    assert isinstance(good.shipments[0]["date"], date)
    assert isinstance(good.shipments[0]["qty_units"], int)
    assert isinstance(good.products[0]["unit_cost_try"], float)
    assert good.calendar[0]["campaign_sku_ids"] == []
    assert good.params["forecast_low_confidence_wape"] == 0.4
    assert len({s["date"] for s in good.shipments}) >= 30


def test_inbound_plan_is_optional(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "d")
    (tmp_path / "d" / "raw" / "inbound_plan.csv").unlink()
    t = load_tables(tmp_path / "d")
    assert t.inbound_plan == []
    assert run(t) == []


def test_missing_required_file_and_bad_value(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "d")
    (tmp_path / "d" / "raw" / "dealers.csv").unlink()
    with pytest.raises(FileNotFoundError):
        load_tables(tmp_path / "d")
    shutil.copy(FIXTURE / "raw" / "dealers.csv", tmp_path / "d" / "raw" / "dealers.csv")
    p = tmp_path / "d" / "raw" / "shipments.csv"
    p.write_text(p.read_text().replace(",5\n", ",x\n", 1), encoding="utf-8")
    with pytest.raises(LoadError):
        load_tables(tmp_path / "d")


# (name, mutator(tables), expected (file, row, rule)). Row = list index + 2.
def _m(fn):
    return fn


def _bad_cases():
    cases = []

    def case(name, file, row, rule):
        def deco(fn):
            cases.append((name, fn, (file, row, rule)))
            return fn
        return deco

    @case("unknown_sku_shipment", "shipments.csv", 2, "UNKNOWN_SKU")
    def _(t): t.shipments[0]["sku_id"] = "SKU-999"

    @case("unknown_dealer_shipment", "shipments.csv", 2, "UNKNOWN_DEALER")
    def _(t): t.shipments[0]["dealer_id"] = "BAYI-99"

    @case("unknown_sku_inventory", "inventory_snapshot.csv", 2, "UNKNOWN_SKU")
    def _(t): t.inventory_snapshot[0]["sku_id"] = "SKU-999"

    @case("unknown_dealer_rule", "dealer_rules.csv", 2, "UNKNOWN_DEALER")
    def _(t): t.dealer_rules[0]["dealer_id"] = "BAYI-99"

    @case("unknown_sku_calendar", "calendar.csv", 2, "UNKNOWN_SKU")
    def _(t): t.calendar[0]["campaign_sku_ids"] = ["SKU-999"]

    @case("lot_sku_mismatch", "shipments.csv", 2, "LOT_SKU_MISMATCH")
    def _(t): t.shipments[0]["lot_id"] = "LOT-SKU-002-1"

    @case("non_positive_shipment_qty", "shipments.csv", 2, "NON_POSITIVE_QTY")
    def _(t): t.shipments[0]["qty_units"] = 0

    @case("negative_inventory_qty", "inventory_snapshot.csv", 2, "NON_POSITIVE_QTY")
    def _(t): t.inventory_snapshot[0]["qty_units"] = -5

    @case("expiry_inconsistent", "inventory_snapshot.csv", 2, "EXPIRY_INCONSISTENT_WITH_SHELF_LIFE")
    def _(t): t.inventory_snapshot[0]["expiry_date"] += timedelta(days=3)

    @case("price_not_above_cost", "products.csv", 2, "PRICE_NOT_ABOVE_COST")
    def _(t): t.products[0]["unit_price_try"] = t.products[0]["unit_cost_try"]

    @case("min_days_below_pull_plus_2", "dealer_rules.csv", 2, "MIN_DAYS_BELOW_PULL_PLUS_2")
    def _(t): t.dealer_rules[0]["min_days_on_receipt"] = t.dealer_rules[0]["shelf_pull_days"] + 1

    @case("shipped_before_received", "shipments.csv", None, "SHIPPED_BEFORE_RECEIVED")
    def _(t):
        i = next(i for i, s in enumerate(t.shipments) if s["lot_id"] == "LOT-SKU-003-2")
        t.shipments[i]["date"] = date(2026, 11, 1)
        t._row = i + 2

    @case("lot_not_eligible_for_dealer", "shipments.csv", None, "LOT_NOT_ELIGIBLE_FOR_DEALER")
    def _(t):
        # a COLD lot with 4 days left is below BAYI-01 min_days_on_receipt (6)
        lot = next(r for r in t.inventory_snapshot if r["lot_id"] == "LOT-SKU-001-2")
        i = next(i for i, s in enumerate(t.shipments)
                 if s["lot_id"] == "LOT-SKU-001-2" and s["dealer_id"] == "BAYI-01")
        t.shipments[i]["date"] = lot["expiry_date"] - timedelta(days=4)
        t._row = i + 2

    @case("duplicate_sku", "products.csv", 3, "DUPLICATE_ID")
    def _(t): t.products[1]["sku_id"] = t.products[0]["sku_id"]

    @case("missing_dealer_rule", "dealer_rules.csv", 0, "MISSING_RULE:BAYI-02:DRY")
    def _(t): t.dealer_rules.pop()

    @case("inbound_expiry_before_expected", "inbound_plan.csv", 2, "EXPIRY_NOT_AFTER_EXPECTED_DATE")
    def _(t): t.inbound_plan[0]["expiry_date"] = t.inbound_plan[0]["expected_date"]

    @case("duplicate_calendar_date", "calendar.csv", 3, "DUPLICATE_DATE")
    def _(t): t.calendar[1]["date"] = t.calendar[0]["date"]

    @case("missing_param", "params.json", 0, "MISSING_PARAM:elasticity")
    def _(t): del t.params["elasticity"]

    return cases


@pytest.mark.parametrize("name,mutate,expected", _bad_cases(), ids=lambda v: v if isinstance(v, str) else "")
def test_known_bad_variant(good, name, mutate, expected):
    t = copy.deepcopy(good)
    mutate(t)
    file, row, rule = expected
    if row is None:
        row = t._row
    issues = run(t)
    assert ValidationIssue(file, row, rule) in issues, issues




def test_validation_error_carries_issues():
    issues = [ValidationIssue("shipments.csv", 2, "UNKNOWN_SKU")]
    err = ValidationError(issues)
    assert err.issues == issues
    assert "shipments.csv row 2: UNKNOWN_SKU" in str(err)


def test_real_generated_data_has_no_issues():
    for cand in (APP_DIR / "data", APP_DIR.parents[2] / "data-gen" / "out"):
        if (cand / "raw" / "products.csv").is_file():
            assert run(load_tables(cand)) == []
            return
    pytest.skip("no generated data found")
