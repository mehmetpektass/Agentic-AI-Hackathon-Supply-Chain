"""Demand forecast: one method, ``WEEKDAY_AVG_4W`` (pure stdlib, no file access).

For a target day ``d`` the forecast uses the last 4 values in history on the
same weekday as ``d`` and dated before ``d``. For future days (after history)
that is the last 4 occurrences of the weekday in history. ``low`` is the min,
``expected`` the mean and ``high`` the max of those values. A window forecast
sums the per-day bands.

The backtest forecasts each of the last 7 history days from the earlier
same-weekday values (up to 4, 3 on the earliest days) and reports
``wape = sum|actual - expected| / sum(actual)``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .features import Features

METHOD = "WEEKDAY_AVG_4W"
WEEKS = 4
BACKTEST_DAYS = 7

LOW = "LOW"
MEDIUM = "MEDIUM"
HIGH = "HIGH"


@dataclass(frozen=True)
class Band:
    low: float
    expected: float
    high: float

    def __add__(self, other: "Band") -> "Band":
        return Band(self.low + other.low, self.expected + other.expected,
                    self.high + other.high)


ZERO_BAND = Band(0.0, 0.0, 0.0)


def forecast_day(series: list[tuple[date, int]], day: date) -> Band:
    """Band for ``day`` from the last 4 same-weekday values dated before ``day``."""
    vals = [u for d, u in series if d < day and d.weekday() == day.weekday()][-WEEKS:]
    if not vals:
        return ZERO_BAND
    return Band(float(min(vals)), sum(vals) / len(vals), float(max(vals)))


def forecast_window(series: list[tuple[date, int]], start: date, days: int) -> Band:
    """Sum of per-day bands over ``days`` days starting at ``start``."""
    total = ZERO_BAND
    for i in range(max(0, days)):
        total = total + forecast_day(series, start + timedelta(days=i))
    return total


def backtest_wape(series: list[tuple[date, int]]) -> float:
    """WAPE of the expected value over the last 7 history days."""
    num = den = 0.0
    all_zero = True
    for t, actual in series[-BACKTEST_DAYS:]:
        exp = forecast_day(series, t).expected
        num += abs(actual - exp)
        den += actual
        if exp != 0:
            all_zero = False
    if den == 0:
        return 0.0 if all_zero else 1.0
    return num / den


def confidence_for(wape: float, low_threshold: float) -> str:
    if wape > low_threshold:
        return LOW
    if wape > low_threshold / 2:
        return MEDIUM
    return HIGH


@dataclass(frozen=True)
class ForecastResult:
    sku_id: str
    method: str
    wape: float
    confidence: str
    series: tuple[tuple[date, int], ...] = field(repr=False, default=())

    def day(self, day: date) -> Band:
        return forecast_day(list(self.series), day)

    def window(self, start: date, days: int) -> Band:
        return forecast_window(list(self.series), start, days)


def forecast_sku(sku_id: str, series: list[tuple[date, int]],
                 low_confidence_wape: float) -> ForecastResult:
    wape = backtest_wape(series)
    return ForecastResult(sku_id, METHOD, wape, confidence_for(wape, low_confidence_wape),
                          tuple(series))


def build_forecasts(features: Features, params: dict) -> dict[str, ForecastResult]:
    """One ``ForecastResult`` per SKU in ``features.daily_series``."""
    t = params["forecast_low_confidence_wape"]
    return {s: forecast_sku(s, ser, t) for s, ser in features.daily_series.items()}
