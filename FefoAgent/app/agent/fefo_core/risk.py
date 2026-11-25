"""Lot expiry risk (pure stdlib, no file access).

Mirrors the reference model in ``data-gen/generate.py`` (``Model.demand``,
``Model.risk``, ``risk_level``, ``confidence``, ``reason_codes``):

* a dealer can take a lot on day ``x`` iff ``(expiry - x).days >= min_days_on_receipt``
  for the (dealer, category) pair;
* the sellable window is the number of days from ``as_of`` while at least one
  dealer is eligible;
* demand of the lot per band = sum over window days of
  ``forecast band(sku, day) * sum(30-day share of eligible dealers) * lot_mix_7d``;
* the ``low`` at-risk/loss band pairs with the HIGH demand band and vice versa,
  so ``low <= expected <= high`` for at-risk units and loss;
* ``at_risk = max(0, round(qty - demand))``, ``loss_try = at_risk * unit_price_try``
  rounded to 2 decimals.

Features report shares as fractions; the params thresholds
(``strict_dealer_share_pct``, ``demand_drop_trend_pct``) are percents.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .features import Features
from .forecast import ForecastResult, Band, forecast_day
from .loader import RawTables

MAX_WINDOW_DAYS = 500  # same safety bound as the reference model
REGULAR_DEALER_SHARE = 0.05

RISK_LOW, RISK_MEDIUM, RISK_HIGH = "LOW", "MEDIUM", "HIGH"


def _as_date(v: date | str) -> date:
    return v if isinstance(v, date) else date.fromisoformat(v)


def risk_level(loss_expected: float, params: dict) -> str:
    t = params["risk_level_thresholds_try"]
    if loss_expected >= t["high_min"]:
        return RISK_HIGH
    if loss_expected >= t["medium_min"]:
        return RISK_MEDIUM
    return RISK_LOW


class _Context:
    """Lookups built once per ``risk_all`` call."""

    def __init__(self, tables: RawTables, features: Features,
                 forecasts: dict[str, ForecastResult]) -> None:
        self.tables = tables
        self.features = features
        self.forecasts = forecasts
        self.params = tables.params
        self.product = {p["sku_id"]: p for p in tables.products}
        self.dealer_ids = sorted(d["dealer_id"] for d in tables.dealers)
        self.min_days = {(r["dealer_id"], r["category"]): r["min_days_on_receipt"]
                         for r in tables.dealer_rules}
        self._series = {s: list(f.series) for s, f in forecasts.items()}
        self._band_cache: dict[tuple[str, int], Band] = {}

    def band(self, sku: str, day: date) -> Band:
        # Days at or after as_of are all future: the band only depends on the weekday.
        key = (sku, day.weekday())
        b = self._band_cache.get(key)
        if b is None:
            b = forecast_day(self._series[sku], day)
            self._band_cache[key] = b
        return b

    def need(self, dealer: str, category: str) -> int | None:
        return self.min_days.get((dealer, category))


def build_context(tables: RawTables, features: Features,
                  forecasts: dict[str, ForecastResult]) -> _Context:
    """Public constructor for the lookups used by ``window_demand`` (used by simulate)."""
    return _Context(tables, features, forecasts)


def _window_demand(ctx: _Context, lot: dict, category: str, mix: float,
                   as_of: date, uplift: dict[str, float] | None = None,
                   only: frozenset[str] | None = None) -> tuple[int, Band]:
    """(window_days, demand band) for the lot over its sellable window.

    ``uplift`` maps dealer_id -> fractional demand increase (share * (1 + uplift)).
    ``only`` restricts the demand to a set of dealers (window is unchanged).
    """
    uplift = uplift or {}
    sku = lot["sku_id"]
    shares = ctx.features.dealer_share_30d.get(sku, {})
    needs = {d: ctx.need(d, category) for d in ctx.dealer_ids}
    needs = {d: n for d, n in needs.items() if n is not None}
    if not needs:
        return 0, Band(0.0, 0.0, 0.0)
    min_all = min(needs.values())
    low = exp = high = 0.0
    window = 0
    for off in range(MAX_WINDOW_DAYS):
        day = as_of + timedelta(days=off)
        left = (lot["expiry_date"] - day).days
        if left < min_all:
            break
        share = sum(shares.get(d, 0.0) * (1.0 + uplift.get(d, 0.0))
                    for d, n in needs.items()
                    if left >= n and (only is None or d in only))
        window += 1
        b = ctx.band(sku, day)
        low += b.low * share * mix
        exp += b.expected * share * mix
        high += b.high * share * mix
    return window, Band(low, exp, high)


def window_demand(ctx: _Context, lot: dict, mix: float, as_of: date,
                  uplift: dict[str, float] | None = None,
                  only: frozenset[str] | None = None) -> tuple[int, Band]:
    """Public wrapper of the window demand for a lot row of ``inventory_snapshot``."""
    category = ctx.product[lot["sku_id"]]["category"]
    return _window_demand(ctx, lot, category, mix, as_of, uplift, only)


def _reason_codes(ctx: _Context, lot: dict, category: str, window: int,
                  at_risk_low: int, at_risk_expected: int, days_left: int,
                  as_of: date) -> list[str]:
    p, f, sku = ctx.params, ctx.features, lot["sku_id"]
    codes: list[str] = []
    if f.fifo_violation.get(lot["lot_id"], False):
        codes.append("FIFO_VIOLATION")
    avg7 = f.avg_7d.get(sku, 0.0)
    if 0 < avg7 < p["slow_mover_daily_units"] and \
            lot["qty_units"] / avg7 > p["large_lot_days_of_cover"]:
        codes.append("SLOW_MOVER_LARGE_LOT")
    wf = f.weekday_factors.get(category, {})
    if category == "COLD" and wf.get("Sat", 1.0) < p["weekend_drop_factor"] \
            and wf.get("Sun", 1.0) < p["weekend_drop_factor"]:
        codes.append("SHORT_SHELF_LIFE")
    for od in f.ordering_dealers.get(sku, {}).values():
        if od.share_30d >= REGULAR_DEALER_SHARE \
                and od.days_since_last_order >= p["stopped_ordering_days"]:
            codes.append("DEALER_STOPPED_ORDERING")
            break
    if f.chain_share_30d.get(sku, 0.0) * 100 > p["strict_dealer_share_pct"]:
        codes.append("STRICT_DEALER_ONLY")
    if f.trend_pct.get(sku, 0.0) <= -p["demand_drop_trend_pct"]:
        codes.append("DEMAND_DROP_TREND")
    for row in ctx.tables.inbound_plan:
        if row["sku_id"] == sku and row["expiry_date"] > lot["expiry_date"] \
                and 0 <= (row["expected_date"] - as_of).days < window:
            codes.append("INBOUND_FRESH_LOT")
            break
    if (at_risk_low > 0 and days_left < min(p["donation_min_days_to_expiry"],
                                            p["supplier_return_min_days_to_expiry"])) \
            or (at_risk_expected > 0 and window == 0):
        codes.append("UNSAVEABLE")
    return codes


def _risk_item(ctx: _Context, lot: dict, as_of: date) -> dict[str, Any]:
    sku = lot["sku_id"]
    prod = ctx.product[sku]
    category = prod["category"]
    qty = lot["qty_units"]
    mix = ctx.features.lot_mix_7d.get(sku, {}).get(lot["lot_id"], 0.0)
    window, demand = _window_demand(ctx, lot, category, mix, as_of)
    # low at-risk pairs with HIGH demand, high at-risk with LOW demand
    at_risk = {
        "low": max(0, round(qty - demand.high)),
        "expected": max(0, round(qty - demand.expected)),
        "high": max(0, round(qty - demand.low)),
    }
    price = prod["unit_price_try"]
    loss = {k: round(v * price, 2) for k, v in at_risk.items()}
    days_left = (lot["expiry_date"] - as_of).days
    fc = ctx.forecasts[sku]
    return {
        "sku_id": sku,
        "sku_name": prod["sku_name"],
        "category": category,
        "lot_id": lot["lot_id"],
        "qty_units": qty,
        "expiry_date": lot["expiry_date"].isoformat(),
        "days_to_expiry": days_left,
        "location_bin": lot["location_bin"],
        "sellable_window_days": window,
        "forecast_units_in_window": {
            "low": round(demand.low, 2),
            "expected": round(demand.expected, 2),
            "high": round(demand.high, 2),
        },
        "at_risk_units": at_risk,
        "loss_try": loss,
        "risk_level": risk_level(loss["expected"], ctx.params),
        "reason_codes": _reason_codes(ctx, lot, category, window, at_risk["low"],
                                      at_risk["expected"], days_left, as_of),
        "forecast_confidence": fc.confidence,
        "wape": round(fc.wape, 4),
    }


def risk_all(tables: RawTables, features: Features,
             forecasts: dict[str, ForecastResult],
             as_of_date: date | str) -> list[dict[str, Any]]:
    """One ExpiryRiskItem per in-stock lot, sorted by expected loss (desc), then lot_id."""
    as_of = _as_date(as_of_date)
    ctx = _Context(tables, features, forecasts)
    items = [_risk_item(ctx, lot, as_of) for lot in tables.inventory_snapshot
             if lot["sku_id"] in ctx.product and lot["qty_units"] > 0]
    items.sort(key=lambda i: (-i["loss_try"]["expected"], i["lot_id"]))
    return items


def risky_items(items: list[dict[str, Any]],
                include_low_confidence: bool = False) -> list[dict[str, Any]]:
    """Lots with expected at-risk units > 0 (order kept).

    With ``include_low_confidence`` also keep lots whose forecast confidence is
    LOW and whose worst-case (``high``) at-risk units are > 0.
    """
    out = []
    for i in items:
        if i["at_risk_units"]["expected"] > 0:
            out.append(i)
        elif include_low_confidence and i["forecast_confidence"] == "LOW" \
                and i["at_risk_units"]["high"] > 0:
            out.append(i)
    return out
