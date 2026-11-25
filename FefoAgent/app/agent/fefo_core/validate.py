"""Consistency checks of TEAM_PLAN section 3.12 on a ``RawTables``.

``run(tables)`` returns a list of ``ValidationIssue(file, row, rule)``; an
empty list means valid. ``row`` is the file line number (header = 1, first
data row = 2), or 0 for file-level issues. ``ValidationError`` carries the
issue list for callers that prefer to raise.

Checks that need the generator (same-seed reproducibility, "non-scenario SKUs
come out risk free") are not part of this module. The "shipment <= stock on
that date" rule is checked as far as the data allows: a shipment must come
from a lot of the same SKU, must not predate the lot's receipt, and must meet
the dealer's ``min_days_on_receipt``. Lots that are no longer in the snapshot
(sold out) have no known expiry, so only their ID and SKU are checked.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from .loader import RawTables

CATEGORIES = ("COLD", "DRY")
DEALER_TYPES = ("CHAIN", "TRADITIONAL")
REQUIRED_PARAMS = (
    "elasticity",
    "max_discount_pct_by_role",
    "donation_min_days_to_expiry",
    "supplier_return_min_days_to_expiry",
    "supplier_return_credit_pct",
    "forecast_low_confidence_wape",
    "risk_level_thresholds_try",
)


@dataclass(frozen=True)
class ValidationIssue:
    file: str
    row: int
    rule: str

    def __str__(self) -> str:
        return f"{self.file} row {self.row}: {self.rule}"


class ValidationError(Exception):
    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__("; ".join(str(i) for i in issues[:20]))


def _dupes(rows, key, file, rule, out):
    seen = set()
    for i, r in enumerate(rows):
        k = key(r)
        if k in seen:
            out.append(ValidationIssue(file, i + 2, rule))
        seen.add(k)


def run(tables: RawTables) -> list[ValidationIssue]:
    out: list[ValidationIssue] = []
    add = lambda f, i, rule: out.append(ValidationIssue(f, i + 2, rule))  # noqa: E731

    # --- reference tables ---------------------------------------------------
    products = {}
    for i, p in enumerate(tables.products):
        products[p["sku_id"]] = p
        if p["category"] not in CATEGORIES:
            add("products.csv", i, "UNKNOWN_CATEGORY")
        if p["shelf_life_days"] <= 0:
            add("products.csv", i, "NON_POSITIVE_SHELF_LIFE")
        if p["unit_cost_try"] <= 0 or p["unit_weight_kg"] <= 0:
            add("products.csv", i, "NON_POSITIVE_VALUE")
        if p["unit_price_try"] <= p["unit_cost_try"]:
            add("products.csv", i, "PRICE_NOT_ABOVE_COST")
    _dupes(tables.products, lambda r: r["sku_id"], "products.csv", "DUPLICATE_ID", out)

    dealers = {}
    for i, d in enumerate(tables.dealers):
        dealers[d["dealer_id"]] = d
        if d["dealer_type"] not in DEALER_TYPES:
            add("dealers.csv", i, "UNKNOWN_DEALER_TYPE")
    _dupes(tables.dealers, lambda r: r["dealer_id"], "dealers.csv", "DUPLICATE_ID", out)

    rules: dict[tuple[str, str], dict] = {}
    for i, r in enumerate(tables.dealer_rules):
        if r["dealer_id"] not in dealers:
            add("dealer_rules.csv", i, "UNKNOWN_DEALER")
        if r["category"] not in CATEGORIES:
            add("dealer_rules.csv", i, "UNKNOWN_CATEGORY")
        if r["shelf_pull_days"] < 0 or r["min_days_on_receipt"] < 0:
            add("dealer_rules.csv", i, "NEGATIVE_VALUE")
        if r["min_days_on_receipt"] < r["shelf_pull_days"] + 2:
            add("dealer_rules.csv", i, "MIN_DAYS_BELOW_PULL_PLUS_2")
        rules[(r["dealer_id"], r["category"])] = r
    _dupes(tables.dealer_rules, lambda r: (r["dealer_id"], r["category"]),
           "dealer_rules.csv", "DUPLICATE_DEALER_CATEGORY", out)
    for dealer_id in dealers:
        for cat in CATEGORIES:
            if (dealer_id, cat) not in rules:
                out.append(ValidationIssue("dealer_rules.csv", 0,
                                           f"MISSING_RULE:{dealer_id}:{cat}"))

    # --- inventory -----------------------------------------------------------
    inv: dict[str, dict] = {}
    for i, r in enumerate(tables.inventory_snapshot):
        inv[r["lot_id"]] = r
        sku = products.get(r["sku_id"])
        if sku is None:
            add("inventory_snapshot.csv", i, "UNKNOWN_SKU")
        if not r["lot_id"].startswith(f"LOT-{r['sku_id']}-"):
            add("inventory_snapshot.csv", i, "LOT_SKU_MISMATCH")
        if r["qty_units"] <= 0:
            add("inventory_snapshot.csv", i, "NON_POSITIVE_QTY")
        if sku is not None and r["expiry_date"] != r["received_date"] + timedelta(
                days=sku["shelf_life_days"]):
            add("inventory_snapshot.csv", i, "EXPIRY_INCONSISTENT_WITH_SHELF_LIFE")
    _dupes(tables.inventory_snapshot, lambda r: r["lot_id"],
           "inventory_snapshot.csv", "DUPLICATE_ID", out)

    # --- inbound plan (optional) --------------------------------------------
    for i, r in enumerate(tables.inbound_plan):
        if r["sku_id"] not in products:
            add("inbound_plan.csv", i, "UNKNOWN_SKU")
        if not r["lot_id"].startswith(f"LOT-{r['sku_id']}-"):
            add("inbound_plan.csv", i, "LOT_SKU_MISMATCH")
        if r["lot_id"] in inv:
            add("inbound_plan.csv", i, "LOT_ALREADY_IN_STOCK")
        if r["qty_units"] <= 0:
            add("inbound_plan.csv", i, "NON_POSITIVE_QTY")
        if r["expiry_date"] <= r["expected_date"]:
            add("inbound_plan.csv", i, "EXPIRY_NOT_AFTER_EXPECTED_DATE")
    _dupes(tables.inbound_plan, lambda r: r["lot_id"], "inbound_plan.csv", "DUPLICATE_ID", out)

    # --- shipments -----------------------------------------------------------
    for i, s in enumerate(tables.shipments):
        sku = products.get(s["sku_id"])
        dealer_ok = s["dealer_id"] in dealers
        if sku is None:
            add("shipments.csv", i, "UNKNOWN_SKU")
        if not dealer_ok:
            add("shipments.csv", i, "UNKNOWN_DEALER")
        if s["qty_units"] <= 0:
            add("shipments.csv", i, "NON_POSITIVE_QTY")
        if not s["lot_id"].startswith(f"LOT-{s['sku_id']}-"):
            add("shipments.csv", i, "LOT_SKU_MISMATCH")
        lot = inv.get(s["lot_id"])
        if lot is not None and sku is not None and dealer_ok:
            if s["date"] < lot["received_date"]:
                add("shipments.csv", i, "SHIPPED_BEFORE_RECEIVED")
            rule = rules.get((s["dealer_id"], sku["category"]))
            if rule is not None and (lot["expiry_date"] - s["date"]).days < rule["min_days_on_receipt"]:
                add("shipments.csv", i, "LOT_NOT_ELIGIBLE_FOR_DEALER")
            if s["date"] >= lot["expiry_date"]:
                add("shipments.csv", i, "SHIPPED_AFTER_EXPIRY")

    # --- calendar ------------------------------------------------------------
    for i, c in enumerate(tables.calendar):
        for sku_id in c["campaign_sku_ids"] + c["stockout_sku_ids"]:
            if sku_id not in products:
                add("calendar.csv", i, "UNKNOWN_SKU")
    _dupes(tables.calendar, lambda r: r["date"], "calendar.csv", "DUPLICATE_DATE", out)

    # --- params --------------------------------------------------------------
    for key in REQUIRED_PARAMS:
        if key not in tables.params:
            out.append(ValidationIssue("params.json", 0, f"MISSING_PARAM:{key}"))

    return out
