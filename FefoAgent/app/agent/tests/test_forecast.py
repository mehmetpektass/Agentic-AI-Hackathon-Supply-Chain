"""Tests for fefo_core.forecast (WEEKDAY_AVG_4W)."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from fefo_core.features import build
from fefo_core.forecast import (
    METHOD, Band, backtest_wape, build_forecasts, confidence_for,
    forecast_day, forecast_sku, forecast_window,
)
from fefo_core.loader import load_tables

APP_DIR = Path(__file__).resolve().parents[1]
FIXTURE = APP_DIR / "tests" / "fixtures" / "data"
GENERATED = APP_DIR / "data"


def make_series(values, end=date(2026, 11, 25)):
    """30-day series ending at ``end`` (inclusive) from a list or function of index."""
    start = end - timedelta(days=29)
    days = [start + timedelta(days=i) for i in range(30)]
    vals = [values(i) for i in range(30)] if callable(values) else list(values)
    return list(zip(days, vals))


def test_fixture_sku001_flat_weekly_pattern():
    f = build(load_tables(FIXTURE), date(2026, 11, 26))
    res = build_forecasts(f, load_tables(FIXTURE).params)["SKU-001"]
    assert res.method == "WEEKDAY_AVG_4W" == METHOD
    assert res.wape == pytest.approx(0.0)
    assert res.confidence == "HIGH"
    # Next Thursday 2026-11-26: last 4 Thursdays all 13 in the fixture.
    assert res.day(date(2026, 11, 26)) == Band(13.0, 13.0, 13.0)
    assert res.day(date(2026, 11, 29)) == Band(0.0, 0.0, 0.0)  # Sunday
    assert res.window(date(2026, 11, 26), 7).expected == pytest.approx(92)


def test_single_day_known_values():
    # Weekly pattern with increasing level: week k adds k to the weekday base.
    series = make_series(lambda i: 10 + i // 7 * 2 + i % 7)
    day = date(2026, 11, 26)  # future day
    vals = [u for d, u in series if d.weekday() == day.weekday()][-4:]
    b = forecast_day(series, day)
    assert b == Band(min(vals), sum(vals) / 4, max(vals))
    assert b.low < b.expected < b.high


def test_future_days_beyond_history_use_last_four_occurrences():
    series = make_series(lambda i: i)
    d1, d2 = date(2026, 12, 3), date(2026, 12, 24)  # same weekday as 2026-11-26
    assert forecast_day(series, d1) == forecast_day(series, d2)


def test_window_sums_per_day_bands():
    series = make_series(lambda i: 5 + (i % 7) * 3)
    start = date(2026, 11, 26)
    days = [start + timedelta(days=i) for i in range(5)]
    w = forecast_window(series, start, 5)
    assert w.low == sum(forecast_day(series, d).low for d in days)
    assert w.expected == pytest.approx(sum(forecast_day(series, d).expected for d in days))
    assert w.high == sum(forecast_day(series, d).high for d in days)
    assert forecast_window(series, start, 0) == Band(0.0, 0.0, 0.0)


def test_exact_wape_with_known_series():
    # Constant 10 except the last day (Wed 2026-11-25) which is 20.
    series = make_series(lambda i: 20 if i == 29 else 10)
    # Backtest days: all forecast 10 exactly except 11-25: actual 20, forecast 10.
    # sum|err| = 10; sum actual = 6 * 10 + 20 = 80.
    assert backtest_wape(series) == pytest.approx(10 / 80)


def test_early_backtest_day_uses_three_values():
    series = make_series(lambda i: 10)
    first_test_day = series[-7][0]
    prior = [d for d, _ in series if d < first_test_day and d.weekday() == first_test_day.weekday()]
    assert len(prior) == 3
    # Make those three values 3, 6, 9 (mean 6) and verify the forecast uses only them.
    vals = {d: v for d, v in zip(prior, (3, 6, 9))}
    series = [(d, vals.get(d, u)) for d, u in series]
    assert forecast_day(series, first_test_day) == Band(3.0, 6.0, 9.0)


def test_zero_demand_sku():
    series = make_series(lambda i: 0)
    res = forecast_sku("SKU-Z", series, 0.4)
    assert res.wape == 0.0
    assert res.confidence == "HIGH"
    assert res.day(date(2026, 11, 26)) == Band(0.0, 0.0, 0.0)


def test_zero_actuals_with_nonzero_forecast_gives_wape_one():
    # Zero in the last 7 days but demand earlier on the same weekdays.
    series = make_series(lambda i: 0 if i >= 23 else 8)
    assert backtest_wape(series) == 1.0


def test_confidence_thresholds():
    assert confidence_for(0.41, 0.4) == "LOW"
    assert confidence_for(0.4, 0.4) == "MEDIUM"
    assert confidence_for(0.21, 0.4) == "MEDIUM"
    assert confidence_for(0.2, 0.4) == "HIGH"


def test_deterministic():
    series = make_series(lambda i: (i * 7) % 11)
    assert forecast_sku("S", series, 0.4) == forecast_sku("S", list(series), 0.4)


def test_generated_data_confidence():
    tables = load_tables(GENERATED)
    f = build(tables, date(2026, 11, 25))
    res = build_forecasts(f, tables.params)
    assert res["SKU-007"].confidence == "LOW"
    assert res["SKU-008"].confidence != "LOW"
    for sku, r in res.items():
        if sku != "SKU-007":
            assert r.confidence != "LOW", (sku, r.wape)
