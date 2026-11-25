"""Tests for fefo_core.features on the shared fixture (as_of 2026-11-26).

Fixture facts (see tests/fixtures/build_fixture.py): 2 dealers (BAYI-01 CHAIN,
BAYI-02 TRADITIONAL), shipments every day except Sunday. History for
as_of 2026-11-26 is 2026-10-27 (Tue) .. 2026-11-25 (Wed). SKU-001 daily totals
per weekday: Mon 15, Tue 17, Wed 15, Thu 13, Fri 15, Sat 17, Sun 0 (92 per week).
"""
from __future__ import annotations

import copy
from datetime import date
from pathlib import Path

import pytest

from fefo_core.features import build
from fefo_core.loader import load_tables

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "data"
APP_DIR = Path(__file__).resolve().parents[1]
AS_OF = date(2026, 11, 26)


@pytest.fixture(scope="module")
def base():
    return load_tables(FIXTURE)


@pytest.fixture()
def tables(base):
    return copy.deepcopy(base)


@pytest.fixture(scope="module")
def feats(base):
    return build(base, AS_OF)


def test_history_window_and_daily_series(feats):
    assert feats.history_days[0] == date(2026, 10, 27)
    assert feats.history_days[-1] == date(2026, 11, 25)
    assert len(feats.history_days) == 30
    series = feats.daily_series["SKU-001"]
    assert [d for d, _ in series] == feats.history_days  # ordered by date
    units = dict(series)
    assert units[date(2026, 10, 27)] == 17  # Tue: 8 + 9
    assert units[date(2026, 11, 25)] == 15  # Wed: 9 + 6
    assert units[date(2026, 11, 1)] == 0  # Sunday: no rows, filled with 0
    assert sum(units.values()) == 400  # 4 x 92 + 17 + 15


def test_missing_day_is_zero_when_rows_removed(tables):
    tables.shipments = [r for r in tables.shipments
                        if not (r["sku_id"] == "SKU-001" and r["date"] == date(2026, 11, 10))]
    f = build(tables, AS_OF)
    assert dict(f.daily_series["SKU-001"])[date(2026, 11, 10)] == 0
    assert len(f.daily_series["SKU-001"]) == 30


def test_shares_chain_and_avg(feats):
    assert feats.dealer_share_30d["SKU-001"]["BAYI-01"] == pytest.approx(197 / 400)
    assert feats.dealer_share_30d["SKU-001"]["BAYI-02"] == pytest.approx(203 / 400)
    assert feats.dealer_share_7d["SKU-001"]["BAYI-01"] == pytest.approx(45 / 92)
    assert feats.chain_share_30d["SKU-001"] == pytest.approx(197 / 400)
    assert feats.avg_7d["SKU-001"] == pytest.approx(92 / 7)
    assert sum(feats.dealer_share_30d["SKU-003"].values()) == pytest.approx(1.0)


def test_weekday_factors_per_category(feats):
    cold = feats.weekday_factors["COLD"]
    # COLD daily totals: Mon 40, Tue 40 (x5 days), Wed 36 (x5), Thu 36, Fri 40, Sat 40, Sun 0.
    # Sum over 30 days = 1004, so the mean over all days is 1004 / 30.
    assert cold["Mon"] == pytest.approx(40 * 30 / 1004)
    assert cold["Wed"] == pytest.approx(36 * 30 / 1004)
    assert cold["Sun"] == 0.0
    assert set(cold) == {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
    assert set(feats.weekday_factors) == {"COLD", "DRY"}


def test_trend_zero_on_flat_weekly_pattern_and_doubling(feats, tables):
    assert feats.trend_pct["SKU-001"] == pytest.approx(0.0)
    # Double the last 7 history days (2026-11-19 .. 2026-11-25): avg_7d doubles.
    for r in tables.shipments:
        if r["sku_id"] == "SKU-001" and date(2026, 11, 19) <= r["date"] <= date(2026, 11, 25):
            r["qty_units"] *= 2
    f = build(tables, AS_OF)
    assert f.avg_7d["SKU-001"] == pytest.approx(184 / 7)
    assert f.trend_pct["SKU-001"] == pytest.approx(100.0)  # prev 21 days = 3 x 92 / 21


def test_trend_zero_when_previous_window_empty(tables):
    tables.shipments = [r for r in tables.shipments
                        if not (r["sku_id"] == "SKU-001" and r["date"] < date(2026, 11, 19))]
    assert build(tables, AS_OF).trend_pct["SKU-001"] == 0.0


def test_as_of_date_shifts_windows(base):
    f = build(base, "2026-11-25")  # string accepted; history = 10-26 .. 11-24
    assert f.as_of_date == date(2026, 11, 25)
    assert f.history_days[0] == date(2026, 10, 26)
    assert f.history_days[-1] == date(2026, 11, 24)
    assert dict(f.daily_series["SKU-001"])[date(2026, 11, 24)] == 17  # Tue
    assert date(2026, 11, 25) not in dict(f.daily_series["SKU-001"])
    # last 7 = 11-18 .. 11-24 (Wed..Tue): 15+13+15+17+0+15+17 = 92.
    last7 = [u for _, u in f.daily_series["SKU-001"][-7:]]
    assert sum(last7) == 92
    assert f.avg_7d["SKU-001"] == pytest.approx(92 / 7)
    assert f.ordering_dealers["SKU-001"]["BAYI-01"].days_since_last_order == 1


def test_ordering_dealers_stopped_and_regular(base, tables):
    f = build(base, AS_OF)
    od = f.ordering_dealers["SKU-001"]["BAYI-02"]
    assert od.last_order_date == date(2026, 11, 25)
    assert od.days_since_last_order == 1 and od.regular
    # BAYI-02 stops ordering SKU-001 after 2026-11-14 (11-15 is a Sunday).
    tables.shipments = [r for r in tables.shipments
                        if not (r["sku_id"] == "SKU-001" and r["dealer_id"] == "BAYI-02"
                                and r["date"] > date(2026, 11, 14))]
    od = build(tables, AS_OF).ordering_dealers["SKU-001"]["BAYI-02"]
    assert od.last_order_date == date(2026, 11, 14)
    assert od.days_since_last_order == 12


def test_small_dealer_is_not_regular(tables):
    # BAYI-02 keeps a single 1-unit order: 1 / (197 + 1) < 5 %.
    keep = date(2026, 11, 20)
    tables.shipments = [r for r in tables.shipments
                        if not (r["sku_id"] == "SKU-001" and r["dealer_id"] == "BAYI-02"
                                and r["date"] != keep)]
    for r in tables.shipments:
        if r["sku_id"] == "SKU-001" and r["dealer_id"] == "BAYI-02":
            r["qty_units"] = 1
    od = build(tables, AS_OF).ordering_dealers["SKU-001"]["BAYI-02"]
    assert od.share_30d == pytest.approx(1 / 198)
    assert od.regular is False


def test_dealer_without_orders_is_absent(tables):
    tables.shipments = [r for r in tables.shipments
                        if not (r["sku_id"] == "SKU-004" and r["dealer_id"] == "BAYI-02")]
    f = build(tables, AS_OF)
    assert "BAYI-02" not in f.ordering_dealers["SKU-004"]
    assert "BAYI-02" not in f.dealer_share_30d["SKU-004"]


def _ship_from(tables, day, dealer, sku, lot_id):
    n = 0
    for r in tables.shipments:
        if r["date"] == day and r["dealer_id"] == dealer and r["sku_id"] == sku:
            r["lot_id"] = lot_id
            n += 1
    assert n == 1


def test_fifo_flag_false_on_fixture_and_lot_mix(feats):
    assert set(feats.fifo_violation) == {
        "LOT-SKU-001-2", "LOT-SKU-001-3", "LOT-SKU-002-2", "LOT-SKU-002-3",
        "LOT-SKU-003-2", "LOT-SKU-004-2"}
    assert not any(feats.fifo_violation.values())
    assert feats.lot_mix_7d["SKU-001"] == {"LOT-SKU-001-2": 1.0}


def test_fifo_flag_and_lot_mix_when_fresher_lot_is_shipped(tables):
    # 2026-11-24 BAYI-01 SKU-001 (8 units: 6 + (1+0+1)%4) ships from the fresher
    # LOT-SKU-001-3 (exp 2026-12-08) while LOT-SKU-001-2 (exp 2026-12-02, received 11-18)
    # has 8 days left and BAYI-01 needs 6.
    _ship_from(tables, date(2026, 11, 24), "BAYI-01", "SKU-001", "LOT-SKU-001-3")
    f = build(tables, AS_OF)
    assert f.fifo_violation["LOT-SKU-001-2"] is True
    assert f.fifo_violation["LOT-SKU-001-3"] is False
    assert f.fifo_violation["LOT-SKU-002-2"] is False
    # Lot mix: 8 of 92 units now from lot 3.
    assert f.lot_mix_7d["SKU-001"]["LOT-SKU-001-3"] == pytest.approx(8 / 92)
    assert f.lot_mix_7d["SKU-001"]["LOT-SKU-001-2"] == pytest.approx(84 / 92)


def test_fifo_flag_needs_eligibility_and_recency(tables):
    _ship_from(tables, date(2026, 11, 24), "BAYI-01", "SKU-001", "LOT-SKU-001-3")
    # Older lot not eligible for the dealer (needs 9 days, has 8): no violation.
    strict = copy.deepcopy(tables)
    for r in strict.dealer_rules:
        if r["dealer_id"] == "BAYI-01" and r["category"] == "COLD":
            r["min_days_on_receipt"] = 9
    assert build(strict, AS_OF).fifo_violation["LOT-SKU-001-2"] is False
    # The older lot was not yet received on the shipment day: no violation.
    late = copy.deepcopy(tables)
    for r in late.inventory_snapshot:
        if r["lot_id"] == "LOT-SKU-001-2":
            r["received_date"] = date(2026, 11, 25)
    assert build(late, AS_OF).fifo_violation["LOT-SKU-001-2"] is False
    # With as_of 2026-12-05 the shipment is older than 7 days: no violation.
    assert build(tables, date(2026, 12, 5)).fifo_violation["LOT-SKU-001-2"] is False


def test_generated_data_fifo_and_chain_share():
    t = load_tables(APP_DIR / "data")
    f = build(t, "2026-11-25")
    flagged = sorted(k for k, v in f.fifo_violation.items() if v)
    assert flagged == ["LOT-SKU-001-3"]
    assert f.chain_share_30d["SKU-003"] > 0.70
    assert len(f.fifo_violation) == len(t.inventory_snapshot)
