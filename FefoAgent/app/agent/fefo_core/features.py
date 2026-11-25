"""Feature building from ``RawTables`` (pure stdlib, no file access).

``build(tables, as_of_date)`` derives per-SKU demand features. Windows are
relative to ``as_of_date`` (same definitions as ``data-gen/generate.py``):

* history days: ``as_of - 30`` .. ``as_of - 1`` (30 days, ``as_of`` itself excluded)
* last 7 days: the last 7 history days (``as_of - 7`` .. ``as_of - 1``)
* previous 21 days: the 21 days before those (``as_of - 28`` .. ``as_of - 8``)

Shipment rows outside the history window are ignored. Days without shipment
rows count as 0 units. Shares are fractions (0.25 = 25 %), not percents.
Weekday keys use ``WEEKDAYS`` (Mon..Sun).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .loader import RawTables

HISTORY_DAYS = 30
RECENT_DAYS = 7
PREV_DAYS = 21
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
REGULAR_DEALER_SHARE = 0.05  # 30-day share at or above this = regular dealer
CHAIN_TYPE = "CHAIN"


@dataclass(frozen=True)
class OrderingDealer:
    dealer_id: str
    last_order_date: date
    days_since_last_order: int
    share_30d: float
    regular: bool  # 30-day share >= 5 %


@dataclass
class Features:
    as_of_date: date
    history_days: list[date] = field(default_factory=list)  # oldest first
    # sku_id -> [(day, units)] ordered by date, one entry per history day
    daily_series: dict[str, list[tuple[date, int]]] = field(default_factory=dict)
    # sku_id -> {dealer_id: share}; only dealers with units in the window
    dealer_share_7d: dict[str, dict[str, float]] = field(default_factory=dict)
    dealer_share_30d: dict[str, dict[str, float]] = field(default_factory=dict)
    # category -> {"Mon": factor, ..., "Sun": factor}
    weekday_factors: dict[str, dict[str, float]] = field(default_factory=dict)
    trend_pct: dict[str, float] = field(default_factory=dict)
    avg_7d: dict[str, float] = field(default_factory=dict)
    # sku_id -> {dealer_id: OrderingDealer}; dealers with a shipment in 30 days
    ordering_dealers: dict[str, dict[str, OrderingDealer]] = field(default_factory=dict)
    # lot_id -> flag, for every in-stock lot (inventory_snapshot)
    fifo_violation: dict[str, bool] = field(default_factory=dict)
    # sku_id -> {lot_id: share of units shipped in the last 7 days}
    lot_mix_7d: dict[str, dict[str, float]] = field(default_factory=dict)
    chain_share_30d: dict[str, float] = field(default_factory=dict)


def _as_date(v: date | str) -> date:
    return v if isinstance(v, date) else date.fromisoformat(v)


def _shares(units: dict[str, int]) -> dict[str, float]:
    total = sum(units.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in units.items() if v > 0}


def build(tables: RawTables, as_of_date: date | str) -> Features:
    as_of = _as_date(as_of_date)
    hist = [as_of - timedelta(days=HISTORY_DAYS - i) for i in range(HISTORY_DAYS)]
    hist_set = set(hist)
    last7 = set(hist[-RECENT_DAYS:])
    prev21 = hist[-(RECENT_DAYS + PREV_DAYS):-RECENT_DAYS]

    skus = [p["sku_id"] for p in tables.products]
    cat = {p["sku_id"]: p["category"] for p in tables.products}
    dealer_type = {d["dealer_id"]: d["dealer_type"] for d in tables.dealers}
    min_days = {(r["dealer_id"], r["category"]): r["min_days_on_receipt"]
                for r in tables.dealer_rules}

    f = Features(as_of_date=as_of, history_days=hist)

    daily: dict[str, dict[date, int]] = {s: {d: 0 for d in hist} for s in skus}
    d30: dict[str, dict[str, int]] = {s: {} for s in skus}
    d7: dict[str, dict[str, int]] = {s: {} for s in skus}
    lot7: dict[str, dict[str, int]] = {s: {} for s in skus}
    last_order: dict[str, dict[str, date]] = {s: {} for s in skus}
    for r in tables.shipments:
        d, s = r["date"], r["sku_id"]
        if d not in hist_set or s not in daily:
            continue
        q, dealer = r["qty_units"], r["dealer_id"]
        daily[s][d] += q
        d30[s][dealer] = d30[s].get(dealer, 0) + q
        if d in last7:
            d7[s][dealer] = d7[s].get(dealer, 0) + q
            lot7[s][r["lot_id"]] = lot7[s].get(r["lot_id"], 0) + q
        if dealer not in last_order[s] or d > last_order[s][dealer]:
            last_order[s][dealer] = d

    for s in skus:
        f.daily_series[s] = [(d, daily[s][d]) for d in hist]
        f.dealer_share_30d[s] = _shares(d30[s])
        f.dealer_share_7d[s] = _shares(d7[s])
        f.lot_mix_7d[s] = _shares(lot7[s])
        f.chain_share_30d[s] = sum(
            v for k, v in f.dealer_share_30d[s].items() if dealer_type.get(k) == CHAIN_TYPE
        )
        avg7 = sum(daily[s][d] for d in hist[-RECENT_DAYS:]) / RECENT_DAYS
        avg21 = sum(daily[s][d] for d in prev21) / PREV_DAYS
        f.avg_7d[s] = avg7
        f.trend_pct[s] = (avg7 / avg21 - 1.0) * 100.0 if avg21 > 0 else 0.0
        f.ordering_dealers[s] = {
            dealer: OrderingDealer(
                dealer_id=dealer,
                last_order_date=last,
                days_since_last_order=(as_of - last).days,
                share_30d=f.dealer_share_30d[s].get(dealer, 0.0),
                regular=f.dealer_share_30d[s].get(dealer, 0.0) >= REGULAR_DEALER_SHARE,
            )
            for dealer, last in last_order[s].items()
        }

    # Weekday factor per category: mean units on that weekday / mean over all days.
    cat_daily: dict[str, dict[date, int]] = {}
    for s in skus:
        tot = cat_daily.setdefault(cat[s], {d: 0 for d in hist})
        for d in hist:
            tot[d] += daily[s][d]
    for c, vals in cat_daily.items():
        mean_all = sum(vals.values()) / len(hist)
        factors: dict[str, float] = {}
        for wd, name in enumerate(WEEKDAYS):
            xs = [vals[d] for d in hist if d.weekday() == wd]
            factors[name] = (sum(xs) / len(xs) / mean_all) if xs and mean_all > 0 else 1.0
        f.weekday_factors[c] = factors

    # FIFO violation per in-stock lot.
    lots = {r["lot_id"]: r for r in tables.inventory_snapshot}
    recent = [r for r in tables.shipments if r["date"] in last7]
    for lot_id, lot in lots.items():
        sku = lot["sku_id"]
        flag = False
        for r in recent:
            if r["sku_id"] != sku or r["lot_id"] == lot_id:
                continue
            shipped = lots.get(r["lot_id"])
            if shipped is None or shipped["expiry_date"] <= lot["expiry_date"]:
                continue  # unknown lot (not in stock) or not fresher
            need = min_days.get((r["dealer_id"], cat.get(sku)))
            if need is None:
                continue
            left = (lot["expiry_date"] - r["date"]).days
            if lot["received_date"] <= r["date"] and left >= need:
                flag = True
                break
        f.fifo_violation[lot_id] = flag
    return f
