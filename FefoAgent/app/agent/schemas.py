"""Tool_Contract şemaları ve doğrulama fonksiyonları."""
from typing import Any, Literal, TypedDict

Category = Literal["COLD", "DRY"]
Audience = ("WAREHOUSE", "COMMERCIAL", "SUPPLIER", "DEALER", "DONATION_PARTNER")
ActionType = ("FEFO_PRIORITY", "DEALER_OFFER", "CAMPAIGN", "DONATION", "SUPPLIER_RETURN")


class Range(TypedDict):
    low: float
    expected: float
    high: float


class ExpiryRiskItem(TypedDict):
    sku_id: str
    sku_name: str
    category: Category
    lot_id: str
    qty_units: int
    expiry_date: str
    days_to_expiry: int
    location_bin: str
    sellable_window_days: int
    forecast_units_in_window: Range
    at_risk_units: Range
    loss_try: Range
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reason_codes: list[str]
    forecast_confidence: Literal["HIGH", "MEDIUM", "LOW"]
    wape: float


class ToolErrorBody(TypedDict):
    code: str
    message: str


class ToolError(TypedDict):
    error: ToolErrorBody


RISK_ITEM_FIELDS = tuple(ExpiryRiskItem.__annotations__)
SKU_PROFILE_FIELDS = ("sku", "daily_velocity", "weekday_factors", "forecast_method",
                      "wape", "lots", "dealers", "signals")
LOT_FIELDS = ("lot_id", "qty_units", "expiry_date", "location_bin", "last_shipped_date")
DEALER_FIELDS = ("dealer_id", "dealer_type", "share_pct", "avg_daily_units", "last_order_date",
                 "days_since_last_order", "min_days_on_receipt", "eligible_for_lot_ids")
STEP_FIELDS = ("action", "params", "feasible", "units_saved", "loss_after_try",
               "action_cost_try", "net_benefit_try", "kg_saved", "policy_refs")
REPORT_FIELDS = ("file_id", "file_name", "format", "s3_key", "download_url",
                 "expires_in_sec", "size_bytes")


def tool_error(code: str, message: str) -> ToolError:
    return {"error": {"code": code, "message": message}}


def is_tool_error(data: Any) -> bool:
    return (isinstance(data, dict) and isinstance(data.get("error"), dict)
            and {"code", "message"} <= set(data["error"]))


def _missing(obj: Any, fields: tuple[str, ...], where: str) -> list[str]:
    if not isinstance(obj, dict):
        return [f"{where}: nesne değil"]
    return [f"{where}: '{f}' eksik" for f in fields if f not in obj]


def _range_errors(obj: dict, name: str, where: str) -> list[str]:
    return _missing(obj.get(name), ("low", "expected", "high"), f"{where}.{name}")


def validate_expiry_risks(data: Any) -> list[str]:
    errs = _missing(data, ("as_of_date", "total_expected_loss_try", "items"), "get_expiry_risks")
    if errs:
        return errs
    prev = None
    for i, item in enumerate(data["items"]):
        where = f"items[{i}]"
        item_errs = _missing(item, RISK_ITEM_FIELDS, where)
        errs += item_errs
        if item_errs:
            continue
        for rng in ("forecast_units_in_window", "at_risk_units", "loss_try"):
            errs += _range_errors(item, rng, where)
        cur = item["loss_try"].get("expected", 0)
        if prev is not None and cur > prev:
            errs.append(f"{where}: loss_try.expected azalan sırada değil")
        prev = cur
    return errs


def validate_sku_profile(data: Any) -> list[str]:
    errs = _missing(data, SKU_PROFILE_FIELDS, "get_sku_profile")
    if errs:
        return errs
    errs += _missing(data["daily_velocity"], ("avg_7d", "avg_30d", "trend_pct"), "daily_velocity")
    errs += _missing(data["weekday_factors"],
                     ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"), "weekday_factors")
    for i, lot in enumerate(data["lots"]):
        errs += _missing(lot, LOT_FIELDS, f"lots[{i}]")
    for i, dealer in enumerate(data["dealers"]):
        errs += _missing(dealer, DEALER_FIELDS, f"dealers[{i}]")
    return errs


def validate_simulation(data: Any) -> list[str]:
    errs = _missing(data, ("lot_id", "baseline_loss_try", "steps", "final_loss_try",
                           "total_net_benefit_try"), "simulate_actions")
    if errs:
        return errs
    for i, step in enumerate(data["steps"]):
        errs += _missing(step, STEP_FIELDS, f"steps[{i}]")
    return errs


def validate_drafts(data: Any) -> list[str]:
    errs = _missing(data, ("decision_id", "status", "drafts", "summary"), "create_action_drafts")
    if errs:
        return errs
    if data["status"] != "DRAFT":
        errs.append("status DRAFT olmalı")
    for i, d in enumerate(data["drafts"]):
        errs += _missing(d, ("audience", "subject", "body"), f"drafts[{i}]")
        if isinstance(d, dict):
            if d.get("audience") not in Audience:
                errs.append(f"drafts[{i}]: audience geçersiz")
            if not str(d.get("body", "")).startswith("TASLAK — gönderilmedi"):
                errs.append(f"drafts[{i}]: body 'TASLAK — gönderilmedi' ile başlamıyor")
    errs += _missing(data["summary"], ("final_loss_try", "total_net_benefit_try", "kg_saved"),
                     "summary")
    return errs


def validate_report(data: Any) -> list[str]:
    return _missing(data, REPORT_FIELDS, "generate_report_file")
