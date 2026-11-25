"""Role_Hook: create_action_drafts çağrısını Actor_Id rolüne ve indirim limitlerine göre denetler."""
import logging
import re
from dataclasses import dataclass
from typing import Any

import config

logger = logging.getLogger("fefo_agent.role_hook")

ACTOR_ID_RE = re.compile(r"^[a-z]+-[A-Za-z0-9-]+$")
VALID_ROLES = ("depo", "ticari")
ALWAYS_ALLOWED = ("FEFO_PRIORITY", "DONATION", "SUPPLIER_RETURN")
DISCOUNT_ACTIONS = ("DEALER_OFFER", "CAMPAIGN")
GUARDED_TOOL = "create_action_drafts"
MSG_NEEDS_COMMERCIAL = "bu aksiyon için ticari onayı gerekir"
MSG_ROLE_UNKNOWN = "rol belirlenemedi: actorId <rol>-<isim> biçiminde ve rol depo veya ticari olmalı"
MSG_BAD_PCT = "indirim yüzdesi eksik veya geçersiz (0-100 arası sayı olmalı)"


@dataclass
class Decision:
    allowed: bool
    message: str = ""
    reason: str = ""


def role_of(actor_id: Any) -> str | None:
    """Geçerli Actor_Id ve geçerli rol ise rolü, aksi halde None döner."""
    if not isinstance(actor_id, str) or not ACTOR_ID_RE.match(actor_id):
        return None
    role = actor_id.split("-", 1)[0]
    return role if role in VALID_ROLES else None


def _valid_pct(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 100


def evaluate(actor_id: Any, approved_actions: Any, limits: dict) -> Decision:
    role = role_of(actor_id)
    if role is None:
        return Decision(False, MSG_ROLE_UNKNOWN, "rol_belirsiz")
    if not isinstance(approved_actions, list) or not approved_actions:
        return Decision(False, "approved_actions boş veya geçersiz", "aksiyon_yok")
    for action in approved_actions:
        a_type = action.get("type") if isinstance(action, dict) else None
        if a_type in ALWAYS_ALLOWED:
            continue
        if a_type not in DISCOUNT_ACTIONS:
            return Decision(False, f"bilinmeyen aksiyon tipi: {a_type}", "aksiyon_bilinmiyor")
        if role != "ticari":
            return Decision(False, MSG_NEEDS_COMMERCIAL, f"rol_yetkisiz:{a_type}")
        pct = (action.get("params") or {}).get("discount_pct")
        if not _valid_pct(pct):
            return Decision(False, MSG_BAD_PCT, f"discount_pct_gecersiz:{a_type}")
        limit = (limits.get(role) or {}).get(a_type)
        if not isinstance(limit, (int, float)) or pct > limit:
            return Decision(False, MSG_NEEDS_COMMERCIAL, f"limit_asimi_veya_tanimsiz:{a_type}")
    return Decision(True)


class RoleHook:
    """Strands HookProvider. Agent, actorId başına oluşturulduğu için Actor_Id sabittir."""

    def __init__(self, actor_id: str):
        self.actor_id = actor_id

    def register_hooks(self, registry, **kwargs) -> None:
        from strands.hooks import BeforeToolCallEvent
        registry.add_callback(BeforeToolCallEvent, self.before_tool_call)

    def before_tool_call(self, event) -> None:
        tool_use = event.tool_use
        if tool_use.get("name") != GUARDED_TOOL:
            return
        tool_input = tool_use.get("input") or {}
        decision = evaluate(self.actor_id, tool_input.get("approved_actions"),
                            config.load_max_discount_pct_by_role())
        types = [a.get("type") for a in tool_input.get("approved_actions") or []
                 if isinstance(a, dict)]
        logger.info("role_hook karar=%s rol=%s actor=%s tool=%s aksiyonlar=%s neden=%s",
                    "izin" if decision.allowed else "ret", role_of(self.actor_id),
                    self.actor_id, GUARDED_TOOL, types, decision.reason or "-")
        if not decision.allowed:
            event.cancel_tool = decision.message
            return
        tool_input["approver_actor_id"] = self.actor_id  # doğrulanmış Actor_Id
        tool_use["input"] = tool_input
