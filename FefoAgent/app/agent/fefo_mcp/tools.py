"""fefo_mcp tool'ları: fefo_core Snapshot'ı üzerinde çalışır. print yok, loglar stderr'e.

Hatalar dict olarak döner, raise edilmez. Snapshot import anında bir kez kurulur.
"""
import hashlib
import logging
import threading
from datetime import date
from pathlib import Path

from config import DEFAULT_AS_OF_DATE
from fefo_core.pipeline import Snapshot, load_snapshot, sku_profile
from fefo_core.risk import risky_items
from fefo_core.simulate import simulate

from . import report

DRAFT_HEADER = "TASLAK — gönderilmedi"
DISCOUNT_ACTIONS = ("DEALER_OFFER", "CAMPAIGN")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_EXTRA_SNAPSHOTS = 8
logger = logging.getLogger("fefo_mcp")

_SNAPSHOT: Snapshot = load_snapshot(DATA_DIR, DEFAULT_AS_OF_DATE)  # başlangıçta bir kez
_EXTRA: dict[str, Snapshot] = {}  # farklı as_of_date başına önbellek (sınırlı)
_LOCK = threading.Lock()


def _err(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _snapshot_for(as_of_date: str | None) -> Snapshot | dict:
    """Varsayılan tarih için başlangıç snapshot'ı; diğer tarihler için sınırlı önbellekli yeniden hesap."""
    if as_of_date is None or as_of_date == _SNAPSHOT.as_of_date.isoformat():
        return _SNAPSHOT
    try:
        day = date.fromisoformat(as_of_date).isoformat()
    except (TypeError, ValueError):
        return _err("INVALID_ARGUMENT", "as_of_date YYYY-MM-DD biçiminde olmalı")
    if day == _SNAPSHOT.as_of_date.isoformat():
        return _SNAPSHOT
    with _LOCK:
        snap = _EXTRA.get(day)
        if snap is None:
            try:
                snap = load_snapshot(DATA_DIR, day)
            except Exception as exc:
                logger.error("as_of_date=%s hesaplanamadı: %s", day, type(exc).__name__)
                return _err("INVALID_ARGUMENT", f"as_of_date {day} için veri hesaplanamadı")
            if len(_EXTRA) >= MAX_EXTRA_SNAPSHOTS:
                _EXTRA.pop(next(iter(_EXTRA)))
            _EXTRA[day] = snap
        return snap


def get_expiry_risks(as_of_date: str | None = None, category: str | None = None,
                     min_loss_try: float = 0, top_n: int = 10) -> dict:
    if category not in (None, "COLD", "DRY"):
        return _err("INVALID_ARGUMENT", "category COLD veya DRY olmalı")
    if top_n < 1:
        return _err("INVALID_ARGUMENT", "top_n en az 1 olmalı")
    snap = _snapshot_for(as_of_date)
    if isinstance(snap, dict):
        return snap
    items = risky_items(snap.risk_items, include_low_confidence=True)
    if category:
        items = [i for i in items if i["category"] == category]
    items = [i for i in items if i["loss_try"]["expected"] >= min_loss_try]
    items = sorted(items, key=lambda i: i["loss_try"]["expected"], reverse=True)[:top_n]
    return {"as_of_date": snap.as_of_date.isoformat(),
            "total_expected_loss_try": round(sum(i["loss_try"]["expected"] for i in items), 2),
            "items": items}


def get_sku_profile(sku_id: str, as_of_date: str | None = None) -> dict:
    snap = _snapshot_for(as_of_date)
    if isinstance(snap, dict):
        return snap
    profile = sku_profile(snap, sku_id)
    if profile is None:
        return _err("SKU_NOT_FOUND", f"{sku_id} bulunamadı")
    return profile


def simulate_actions(lot_id: str, actions: list[dict], as_of_date: str | None = None) -> dict:
    snap = _snapshot_for(as_of_date)
    if isinstance(snap, dict):
        return snap
    return simulate(snap, lot_id, actions)  # role: varsayılan (stub'da rol yok)


def create_action_drafts(lot_id: str, approved_actions: list[dict],
                         approver_actor_id: str) -> dict:
    if _SNAPSHOT.lot(lot_id) is None:
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
    snap = _snapshot_for(as_of_date)
    if isinstance(snap, dict):
        return snap
    return report.generate_report_file(report_type, format, lot_id, decision_id,
                                       summary_text, snap)
