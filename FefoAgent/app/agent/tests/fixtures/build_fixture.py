"""Builds the small shared test fixture under ``tests/fixtures/data/``.

Run ``python build_fixture.py`` to regenerate. Deterministic, stdlib only.
2 dealers, 4 SKUs (2 COLD, 2 DRY), 35 days of shipments, as_of_date 2026-11-26
(shipments 2026-10-22 .. 2026-11-25). Valid by construction.
"""

from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from pathlib import Path

AS_OF = date(2026, 11, 26)
DAYS = 35
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"

PRODUCTS = [
    ("SKU-001", "Süzme Yoğurt 1 kg", "COLD", 14, "30.00", "45.00", "1.000", "SUP-01", "false"),
    ("SKU-002", "Tam Yağlı Süt 1 L", "COLD", 21, "20.00", "28.00", "1.030", "SUP-01", "true"),
    ("SKU-003", "Makarna 500 g", "DRY", 120, "10.00", "15.00", "0.500", "SUP-02", "true"),
    ("SKU-004", "Bisküvi 200 g", "DRY", 90, "8.00", "12.00", "0.200", "SUP-02", "false"),
]
DEALERS = [
    ("BAYI-01", "Bayi-01 Merkez", "Marmara", "CHAIN"),
    ("BAYI-02", "Bayi-02 Çarşı", "Ege", "TRADITIONAL"),
]
DEALER_RULES = [
    ("BAYI-01", "COLD", 4, 6), ("BAYI-01", "DRY", 30, 45),
    ("BAYI-02", "COLD", 3, 5), ("BAYI-02", "DRY", 20, 22),
]
# sku -> received dates of in-stock lots (lot n = index + 2; lot 1 is sold out)
IN_STOCK = {
    "SKU-001": [date(2026, 11, 18), date(2026, 11, 24)],
    "SKU-002": [date(2026, 11, 18), date(2026, 11, 24)],
    "SKU-003": [date(2026, 11, 5)],
    "SKU-004": [date(2026, 11, 5)],
}
QTY = {"SKU-001": 120, "SKU-002": 200, "SKU-003": 600, "SKU-004": 800}
BASE = {"SKU-001": 6, "SKU-002": 10, "SKU-003": 4, "SKU-004": 5}
PARAMS = {
    "elasticity": {"COLD": 1.5, "DRY": 1.2},
    "max_discount_pct_by_role": {"ticari": {"DEALER_OFFER": 20, "CAMPAIGN": 25}},
    "donation_min_days_to_expiry": 1,
    "supplier_return_min_days_to_expiry": 4,
    "supplier_return_credit_pct": 0.6,
    "forecast_low_confidence_wape": 0.4,
    "risk_level_thresholds_try": {"medium_min": 2000, "high_min": 10000},
    "slow_mover_daily_units": 8,
    "large_lot_days_of_cover": 20,
    "weekend_drop_factor": 0.85,
    "stopped_ordering_days": 7,
    "strict_dealer_share_pct": 70,
    "demand_drop_trend_pct": 20,
}


def _write(path: Path, header: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def build(out_dir: Path = DATA_DIR) -> Path:
    raw = out_dir / "raw"
    shelf = {p[0]: p[3] for p in PRODUCTS}

    _write(raw / "products.csv",
           ["sku_id", "sku_name", "category", "shelf_life_days", "unit_cost_try",
            "unit_price_try", "unit_weight_kg", "supplier_id", "supplier_return_allowed"],
           PRODUCTS)
    _write(raw / "dealers.csv", ["dealer_id", "dealer_name", "region", "dealer_type"], DEALERS)
    _write(raw / "dealer_rules.csv",
           ["dealer_id", "category", "shelf_pull_days", "min_days_on_receipt"], DEALER_RULES)

    lots = {}  # sku -> list of (lot_id, received)
    inventory = []
    for sku, recs in IN_STOCK.items():
        lots[sku] = []
        for n, rec in enumerate(recs, start=2):
            lot_id = f"LOT-{sku}-{n}"
            lots[sku].append((lot_id, rec))
            inventory.append((sku, lot_id, QTY[sku] // n, (rec + timedelta(days=shelf[sku])).isoformat(),
                              rec.isoformat(), f"A-0{n}-1"))
    _write(raw / "inventory_snapshot.csv",
           ["sku_id", "lot_id", "qty_units", "expiry_date", "received_date", "location_bin"],
           inventory)

    ships = []
    for k in range(DAYS):
        d = AS_OF - timedelta(days=DAYS - k)
        for dealer_i, (dealer_id, *_rest) in enumerate(DEALERS):
            for sku, base in BASE.items():
                qty = base + (d.weekday() + dealer_i + int(sku[-1])) % 4
                if d.weekday() == 6:  # no Sunday deliveries
                    continue
                # oldest in-stock lot already received on d, else the sold-out lot 1
                avail = [lid for lid, rec in lots[sku] if rec <= d]
                lot_id = avail[0] if avail else f"LOT-{sku}-1"
                ships.append((d.isoformat(), dealer_id, sku, lot_id, qty))
    _write(raw / "shipments.csv", ["date", "dealer_id", "sku_id", "lot_id", "qty_units"], ships)

    _write(raw / "inbound_plan.csv",
           ["expected_date", "sku_id", "lot_id", "qty_units", "expiry_date"],
           [((AS_OF + timedelta(days=2)).isoformat(), "SKU-001", "LOT-SKU-001-4", 150,
             (AS_OF + timedelta(days=16)).isoformat())])

    cal = []
    for k in range(DAYS):
        d = AS_OF - timedelta(days=DAYS - k)
        camp = d == date(2026, 11, 10)
        cal.append((d.isoformat(), "true" if camp else "false", "SKU-003" if camp else "",
                    "SKU-002" if d == date(2026, 11, 3) else ""))
    _write(raw / "calendar.csv",
           ["date", "is_campaign_day", "campaign_sku_ids", "stockout_sku_ids"], cal)

    cfg = out_dir / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "params.json").write_text(json.dumps(PARAMS, indent=2) + "\n", encoding="utf-8")
    return out_dir


if __name__ == "__main__":
    build()
