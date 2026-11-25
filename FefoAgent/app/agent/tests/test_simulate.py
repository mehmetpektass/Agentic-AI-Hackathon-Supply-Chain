"""Tests for fefo_core.simulate (loss waterfall)."""
from __future__ import annotations

from pathlib import Path

import pytest

from fefo_core.pipeline import load_snapshot
from fefo_core.simulate import simulate
from schemas import validate_simulation

GENERATED = Path(__file__).resolve().parents[1] / "data"
LOT = "LOT-SKU-001-3"
WATERFALL = [{"type": "FEFO_PRIORITY"},
             {"type": "DEALER_OFFER", "params": {"discount_pct": 10}},
             {"type": "CAMPAIGN", "params": {"discount_pct": 15}}]


@pytest.fixture(scope="module")
def snap():
    return load_snapshot(GENERATED, "2026-11-25")


def _find(snap, pred):
    prods = {p["sku_id"]: p for p in snap.tables.products}
    return next(i for i in snap.risk_items if pred(i, prods[i["sku_id"]]))


def test_waterfall_matches_reference(snap):
    out = simulate(snap, LOT, WATERFALL)
    assert validate_simulation(out) == []
    assert [s["action"] for s in out["steps"]] == [a["type"] for a in WATERFALL]
    got = [out["baseline_loss_try"]] + [s["loss_after_try"] for s in out["steps"]]
    for g, ref in zip(got, [40242, 15121, 14211, 8565]):
        assert g == pytest.approx(ref, rel=0.01)
    assert got == sorted(got, reverse=True)
    assert all(s["feasible"] for s in out["steps"])
    assert out["final_loss_try"] == got[-1]
    assert out["steps"][0]["action_cost_try"] == 0
    for s in out["steps"][1:]:
        assert s["action_cost_try"] > 0
    prev = out["baseline_loss_try"]
    for s in out["steps"]:
        assert s["net_benefit_try"] == pytest.approx(prev - s["loss_after_try"]
                                                     - s["action_cost_try"], abs=0.02)
        prev = s["loss_after_try"]
    assert out["steps"][0]["policy_refs"] and out["steps"][0]["kg_saved"] > 0


def test_step_order_preserved_and_cumulative(snap):
    swapped = [WATERFALL[2], WATERFALL[0]]
    out = simulate(snap, LOT, swapped)
    assert [s["action"] for s in out["steps"]] == ["CAMPAIGN", "FEFO_PRIORITY"]
    alone = simulate(snap, LOT, [WATERFALL[2]])
    assert out["steps"][0]["loss_after_try"] == alone["steps"][0]["loss_after_try"]
    assert out["final_loss_try"] < alone["final_loss_try"]


def test_discount_above_limit_infeasible(snap):
    lim = snap.params["max_discount_pct_by_role"]["ticari"]
    out = simulate(snap, LOT, [{"type": "DEALER_OFFER",
                                "params": {"discount_pct": lim["DEALER_OFFER"] + 1}}])
    s = out["steps"][0]
    assert s["feasible"] is False and s["infeasible_reason"]
    assert s["loss_after_try"] == out["baseline_loss_try"] and s["units_saved"] == 0
    assert out["final_loss_try"] == out["baseline_loss_try"]
    ok = simulate(snap, LOT, [{"type": "DEALER_OFFER",
                               "params": {"discount_pct": lim["DEALER_OFFER"]}}])
    assert ok["steps"][0]["feasible"] is True
    assert simulate(snap, LOT, [{"type": "CAMPAIGN", "params": {}}])["steps"][0]["feasible"] is False
    depo = simulate(snap, LOT, [{"type": "CAMPAIGN", "params": {"discount_pct": 5}}], role="depo")
    assert depo["steps"][0]["feasible"] is False


def test_donation_kg_saved(snap):
    item = _find(snap, lambda i, p: i["at_risk_units"]["expected"] > 0 and i["days_to_expiry"] >= 1)
    prod = next(p for p in snap.tables.products if p["sku_id"] == item["sku_id"])
    n = item["at_risk_units"]["expected"]
    out = simulate(snap, item["lot_id"], [{"type": "DONATION", "params": {}}])
    s = out["steps"][0]
    assert s["feasible"] and s["units_saved"] == n
    assert s["kg_saved"] == pytest.approx(n * prod["unit_weight_kg"], abs=0.01)
    assert s["loss_after_try"] == out["baseline_loss_try"]
    assert s["net_benefit_try"] == 0
    too_many = simulate(snap, item["lot_id"], [{"type": "DONATION", "params": {"units": n + 1}}])
    assert too_many["steps"][0]["feasible"] is False


def test_supplier_return_rules(snap):
    item = _find(snap, lambda i, p: p["supplier_return_allowed"] and i["days_to_expiry"]
                 >= snap.params["supplier_return_min_days_to_expiry"]
                 and i["at_risk_units"]["expected"] > 0)
    prod = next(p for p in snap.tables.products if p["sku_id"] == item["sku_id"])
    n = item["at_risk_units"]["expected"]
    out = simulate(snap, item["lot_id"], [{"type": "SUPPLIER_RETURN", "params": {"units": n}}])
    s = out["steps"][0]
    credit = n * prod["unit_cost_try"] * snap.params["supplier_return_credit_pct"]
    assert s["feasible"]
    assert out["baseline_loss_try"] - s["loss_after_try"] == pytest.approx(credit, abs=0.02)
    assert s["net_benefit_try"] == pytest.approx(credit, abs=0.02)

    not_allowed = _find(snap, lambda i, p: not p["supplier_return_allowed"]
                        and i["at_risk_units"]["expected"] > 0)
    r = simulate(snap, not_allowed["lot_id"], [{"type": "SUPPLIER_RETURN"}])["steps"][0]
    assert r["feasible"] is False and r["loss_after_try"] > 0

    snap.params["supplier_return_min_days_to_expiry"] += 1000  # force day rule
    try:
        r = simulate(snap, item["lot_id"], [{"type": "SUPPLIER_RETURN"}])["steps"][0]
        assert r["feasible"] is False and "gün" in r["infeasible_reason"]
    finally:
        snap.params["supplier_return_min_days_to_expiry"] -= 1000


def test_errors(snap):
    assert simulate(snap, "YOK", WATERFALL)["error"]["code"] == "LOT_NOT_FOUND"
    assert simulate(snap, LOT, [])["error"]["code"] == "INVALID_ARGUMENT"
    assert simulate(snap, LOT, [{"type": "X"}])["error"]["code"] == "INVALID_ARGUMENT"
