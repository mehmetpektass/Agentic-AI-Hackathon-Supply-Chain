"""Stub tool'ları: Tool_Contract'a uyan sabit, deterministik yanıtlar. print yok, loglar stderr'e."""
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

DEFAULT_AS_OF_DATE = "2026-11-25"
DRAFT_HEADER = "TASLAK — gönderilmedi"
FIXTURES = Path(__file__).parent / "fixtures"
logger = logging.getLogger("fefo_mcp_stub")

# Sabit stub etkisi: aksiyon başına mevcut kaybın azalan oranı ve sabit aksiyon maliyeti (₺)
ACTION_EFFECT = {
    "FEFO_PRIORITY": (0.30, 0.0),
    "DEALER_OFFER": (0.35, 150.0),
    "CAMPAIGN": (0.30, 250.0),
    "DONATION": (0.20, 50.0),
    "SUPPLIER_RETURN": (0.15, 100.0),
}
DISCOUNT_ACTIONS = ("DEALER_OFFER", "CAMPAIGN")
POLICY_REFS = {"FEFO_PRIORITY": ["POL-1.1"], "DEALER_OFFER": ["POL-2.1"], "CAMPAIGN": ["POL-2.2"],
               "DONATION": ["POL-3.1"], "SUPPLIER_RETURN": ["POL-3.2"]}


def _err(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _find_lot(lot_id: str) -> dict | None:
    return next((i for i in _load("expiry_risks.json") if i["lot_id"] == lot_id), None)


def get_expiry_risks(as_of_date: str | None = None, category: str | None = None,
                     min_loss_try: float = 0, top_n: int = 10) -> dict:
    if category not in (None, "COLD", "DRY"):
        return _err("INVALID_ARGUMENT", "category COLD veya DRY olmalı")
    if top_n < 1:
        return _err("INVALID_ARGUMENT", "top_n en az 1 olmalı")
    items = _load("expiry_risks.json")
    if category:
        items = [i for i in items if i["category"] == category]
    items = [i for i in items if i["loss_try"]["expected"] >= min_loss_try]
    items = sorted(items, key=lambda i: i["loss_try"]["expected"], reverse=True)[:top_n]
    return {"as_of_date": as_of_date or DEFAULT_AS_OF_DATE,
            "total_expected_loss_try": round(sum(i["loss_try"]["expected"] for i in items), 2),
            "items": items}


def get_sku_profile(sku_id: str, as_of_date: str | None = None) -> dict:
    profile = _load("sku_profiles.json").get(sku_id)
    if profile is None:
        return _err("SKU_NOT_FOUND", f"{sku_id} bulunamadı")
    return profile


def simulate_actions(lot_id: str, actions: list[dict], as_of_date: str | None = None) -> dict:
    lot = _find_lot(lot_id)
    if lot is None:
        return _err("LOT_NOT_FOUND", f"{lot_id} bulunamadı")
    if not actions:
        return _err("INVALID_ARGUMENT", "actions boş olamaz")
    baseline = float(lot["loss_try"]["expected"])
    current, steps = baseline, []
    at_risk = float(lot["at_risk_units"]["expected"])
    for act in actions:
        a_type = act.get("type") if isinstance(act, dict) else None
        params = (act.get("params") or {}) if isinstance(act, dict) else {}
        if a_type not in ACTION_EFFECT:
            return _err("INVALID_ARGUMENT", f"bilinmeyen aksiyon tipi: {a_type}")
        step = {"action": a_type, "params": params, "feasible": True, "units_saved": 0,
                "loss_after_try": current, "action_cost_try": 0.0, "net_benefit_try": 0.0,
                "kg_saved": 0.0, "policy_refs": POLICY_REFS[a_type]}
        if a_type in DISCOUNT_ACTIONS and not isinstance(params.get("discount_pct"), (int, float)):
            step.update(feasible=False, infeasible_reason="discount_pct gerekli")
        else:
            ratio, cost = ACTION_EFFECT[a_type]
            after = round(current * (1 - ratio), 2)
            saved_units = int(round(at_risk * ratio))
            step.update(units_saved=saved_units, loss_after_try=after, action_cost_try=cost,
                        net_benefit_try=round(current - after - cost, 2),
                        kg_saved=round(saved_units * 1.0, 2))
            current, at_risk = after, at_risk - saved_units
        steps.append(step)
    return {"lot_id": lot_id, "baseline_loss_try": baseline, "steps": steps,
            "final_loss_try": current,
            "total_net_benefit_try": round(sum(s["net_benefit_try"] for s in steps), 2)}


def create_action_drafts(lot_id: str, approved_actions: list[dict],
                         approver_actor_id: str) -> dict:
    if _find_lot(lot_id) is None:
        return _err("LOT_NOT_FOUND", f"{lot_id} bulunamadı")
    if not approved_actions or not approver_actor_id:
        return _err("INVALID_ARGUMENT", "approved_actions ve approver_actor_id gerekli")
    sim = simulate_actions(lot_id, approved_actions)
    if "error" in sim:
        return sim
    types = {a["type"] for a in approved_actions}
    audiences = [("WAREHOUSE", "Depo aksiyon planı")]
    if types & set(DISCOUNT_ACTIONS):
        audiences.append(("COMMERCIAL", "Ticari ekip: indirim ve kampanya"))
    if "SUPPLIER_RETURN" in types:
        audiences.append(("SUPPLIER", "Tedarikçi iade talebi"))
    if "DONATION" in types:
        audiences.append(("DONATION_PARTNER", "Bağış talebi"))
    drafts = [{"audience": a, "subject": f"{s} ({lot_id})",
               "body": f"{DRAFT_HEADER}\n\n{lot_id} için onaylanan aksiyonlar: {', '.join(sorted(types))}."}
              for a, s in audiences]
    digest = hashlib.sha1(f"{lot_id}{sorted(types)}".encode()).hexdigest()[:8]
    return {"decision_id": f"DEC-{digest}", "status": "DRAFT", "drafts": drafts,
            "summary": {"final_loss_try": sim["final_loss_try"],
                        "total_net_benefit_try": sim["total_net_benefit_try"],
                        "kg_saved": round(sum(s["kg_saved"] for s in sim["steps"]), 2)}}


def generate_report_file(report_type: str, format: str, lot_id: str | None = None,
                         decision_id: str | None = None, summary_text: str | None = None,
                         as_of_date: str | None = None) -> dict:
    if report_type not in ("DAILY_RISK", "LOT_ACTION_PLAN", "RISK_TABLE"):
        return _err("INVALID_ARGUMENT", "report_type geçersiz")
    if format not in ("pdf", "xlsx"):
        return _err("INVALID_ARGUMENT", "format pdf veya xlsx olmalı")
    if report_type == "LOT_ACTION_PLAN" and not lot_id:
        return _err("INVALID_ARGUMENT", "LOT_ACTION_PLAN için lot_id gerekli")
    day = as_of_date or DEFAULT_AS_OF_DATE
    file_id = hashlib.sha1(f"{report_type}{format}{lot_id}{day}".encode()).hexdigest()[:12]
    names = {"DAILY_RISK": "FEFO_Gunluk_Risk", "LOT_ACTION_PLAN": "FEFO_Lot_Aksiyon_Plani",
             "RISK_TABLE": "FEFO_Risk_Tablosu"}
    key = f"reports/{day}/{file_id}.{format}"
    return {"file_id": file_id, "file_name": f"{names[report_type]}_{day}.{format}",
            "format": format, "s3_key": key,
            "download_url": f"https://stub.invalid/{key}", "expires_in_sec": 3600,
            "size_bytes": 0}
