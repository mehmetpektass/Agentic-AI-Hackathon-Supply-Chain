"""Snapshot pipeline: load -> validate -> features -> forecast -> risk (pure stdlib).

``load_snapshot(data_dir, as_of_date)`` is the one call the MCP server makes at
start-up. ``sku_profile(snapshot, sku_id)`` returns the ``get_sku_profile``
tool shape (TEAM_PLAN 4.2) computed from the snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from . import features as features_mod
from . import forecast as forecast_mod
from . import risk as risk_mod
from . import validate as validate_mod
from .features import Features
from .forecast import ForecastResult
from .loader import RawTables, load_tables
from .validate import ValidationError

AVG_30D_DAYS = features_mod.HISTORY_DAYS


@dataclass
class Snapshot:
    as_of_date: date
    tables: RawTables
    features: Features
    forecasts: dict[str, ForecastResult]
    risk_items: list[dict[str, Any]]  # sorted by loss_try.expected desc
    params: dict[str, Any]
    by_lot: dict[str, dict[str, Any]] = field(default_factory=dict)
    by_sku: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    context: Any = field(default=None, repr=False)  # risk._Context, reused by simulate

    def lot(self, lot_id: str) -> dict[str, Any] | None:
        return self.by_lot.get(lot_id)

    def lots_of_sku(self, sku_id: str) -> list[dict[str, Any]]:
        return self.by_sku.get(sku_id, [])


def load_snapshot(data_dir: str | Path, as_of_date: date | str) -> Snapshot:
    as_of = as_of_date if isinstance(as_of_date, date) else date.fromisoformat(as_of_date)
    tables = load_tables(data_dir)
    issues = validate_mod.run(tables)
    if issues:
        raise ValidationError(issues)
    feats = features_mod.build(tables, as_of)
    forecasts = forecast_mod.build_forecasts(feats, tables.params)
    items = risk_mod.risk_all(tables, feats, forecasts, as_of)
    snap = Snapshot(as_of_date=as_of, tables=tables, features=feats, forecasts=forecasts,
                    risk_items=items, params=tables.params)
    for it in items:
        snap.by_lot[it["lot_id"]] = it
        snap.by_sku.setdefault(it["sku_id"], []).append(it)
    snap.context = risk_mod.build_context(tables, feats, forecasts)
    return snap


def sku_profile(snap: Snapshot, sku_id: str) -> dict[str, Any] | None:
    """``get_sku_profile`` output for ``sku_id``; None when the SKU is unknown."""
    prod = next((p for p in snap.tables.products if p["sku_id"] == sku_id), None)
    if prod is None:
        return None
    f, fc = snap.features, snap.forecasts[sku_id]
    category = prod["category"]
    series = f.daily_series[sku_id]
    avg_30d = sum(u for _, u in series) / AVG_30D_DAYS
    lots_items = snap.lots_of_sku(sku_id)

    last_shipped: dict[str, date] = {}
    for r in snap.tables.shipments:
        if r["sku_id"] == sku_id and (r["lot_id"] not in last_shipped
                                      or r["date"] > last_shipped[r["lot_id"]]):
            last_shipped[r["lot_id"]] = r["date"]
    lot_rows = sorted((r for r in snap.tables.inventory_snapshot if r["sku_id"] == sku_id),
                      key=lambda r: (r["expiry_date"], r["lot_id"]))
    lots = [{
        "lot_id": r["lot_id"],
        "qty_units": r["qty_units"],
        "expiry_date": r["expiry_date"].isoformat(),
        "location_bin": r["location_bin"],
        "last_shipped_date": (last_shipped[r["lot_id"]].isoformat()
                              if r["lot_id"] in last_shipped else None),
    } for r in lot_rows]

    min_days = {(r["dealer_id"], r["category"]): r["min_days_on_receipt"]
                for r in snap.tables.dealer_rules}
    dtype = {d["dealer_id"]: d["dealer_type"] for d in snap.tables.dealers}
    dealers = []
    for od in sorted(f.ordering_dealers.get(sku_id, {}).values(),
                     key=lambda o: (-o.share_30d, o.dealer_id)):
        need = min_days.get((od.dealer_id, category))
        eligible = [r["lot_id"] for r in lot_rows
                    if need is not None and (r["expiry_date"] - snap.as_of_date).days >= need]
        dealers.append({
            "dealer_id": od.dealer_id,
            "dealer_type": dtype.get(od.dealer_id, ""),
            "share_pct": round(od.share_30d * 100, 1),
            "avg_daily_units": round(od.share_30d * avg_30d, 2),
            "last_order_date": od.last_order_date.isoformat(),
            "days_since_last_order": od.days_since_last_order,
            "min_days_on_receipt": need,
            "eligible_for_lot_ids": eligible,
        })

    signals: list[str] = []
    for it in lots_items:
        for c in it["reason_codes"]:
            if c not in signals:
                signals.append(c)
    return {
        "sku": {"sku_id": sku_id, "sku_name": prod["sku_name"], "category": category},
        "daily_velocity": {"avg_7d": round(f.avg_7d[sku_id], 2),
                           "avg_30d": round(avg_30d, 2),
                           "trend_pct": round(f.trend_pct[sku_id], 1)},
        "weekday_factors": {k: round(v, 2) for k, v in f.weekday_factors[category].items()},
        "forecast_method": fc.method,
        "wape": round(fc.wape, 4),
        "lots": lots,
        "dealers": dealers,
        "signals": signals,
    }
