"""Loss waterfall simulation (TEAM_PLAN 4.3), pure stdlib.

Mirrors ``simulate()`` in ``data-gen/generate.py``. Baseline: expected demand,
30-day dealer shares, eligibility rule and the lot mix of the last 7 days.
Steps apply in the given order and cumulatively:

* ``FEFO_PRIORITY``: lot mix becomes 1.0 (the lot is sold first).
* ``DEALER_OFFER``: demand of the chosen dealers (default: the 2 eligible
  dealers with the highest 30-day share) rises by ``elasticity * discount_pct / 100``.
* ``CAMPAIGN``: same uplift for every dealer eligible today.
* ``DONATION``: moves at-risk units to ``kg_saved``; TRY loss is unchanged.
* ``SUPPLIER_RETURN``: ``units * unit_cost_try * supplier_return_credit_pct``
  reduces the loss.

Loss after a step = loss from the window demand (``max(0, round(qty - demand))
* unit_price``) minus the supplier-return recoveries so far (never below 0).
``action_cost_try`` of a discount step = units sold to the discounted dealers in
the window (capped by the lot quantity) * unit price * discount_pct / 100.
``kg_saved`` = units kept out of waste * ``unit_weight_kg`` (0 for returns).
An infeasible step changes nothing and carries ``infeasible_reason``.
"""

from __future__ import annotations

from typing import Any

from .pipeline import Snapshot
from .risk import window_demand

ACTION_TYPES = ("FEFO_PRIORITY", "DEALER_OFFER", "CAMPAIGN", "DONATION", "SUPPLIER_RETURN")
DISCOUNT_ACTIONS = ("DEALER_OFFER", "CAMPAIGN")
DEFAULT_ROLE = "ticari"  # the only role with discount limits in params.json
POLICY_REFS = {"FEFO_PRIORITY": ["POL-1.1", "POL-1.2"], "DEALER_OFFER": ["POL-2.1"],
               "CAMPAIGN": ["POL-2.2"], "DONATION": ["POL-3.1"],
               "SUPPLIER_RETURN": ["POL-3.2"]}
TOP_DEALERS = 2


def _err(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _num(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def simulate(snap: Snapshot, lot_id: str, actions: list[dict],
             role: str | None = None) -> dict[str, Any]:
    item = snap.lot(lot_id)
    if item is None:
        return _err("LOT_NOT_FOUND", f"{lot_id} bulunamadı")
    if not isinstance(actions, list) or not actions:
        return _err("INVALID_ARGUMENT", "actions boş olamaz")
    for a in actions:
        if not isinstance(a, dict) or a.get("type") not in ACTION_TYPES:
            t = a.get("type") if isinstance(a, dict) else a
            return _err("INVALID_ARGUMENT", f"bilinmeyen aksiyon tipi: {t}")

    ctx, params, as_of = snap.context, snap.params, snap.as_of_date
    lot = next(r for r in snap.tables.inventory_snapshot if r["lot_id"] == lot_id)
    sku = lot["sku_id"]
    prod = ctx.product[sku]
    category, price, qty = prod["category"], prod["unit_price_try"], lot["qty_units"]
    days_left = item["days_to_expiry"]
    elasticity = params["elasticity"][category]
    role = role or DEFAULT_ROLE
    limits = (params.get("max_discount_pct_by_role") or {}).get(role) or {}
    shares = snap.features.dealer_share_30d.get(sku, {})
    eligible_today = [d for d in ctx.dealer_ids
                      if ctx.need(d, category) is not None and days_left >= ctx.need(d, category)]

    mix = snap.features.lot_mix_7d.get(sku, {}).get(lot_id, 0.0)
    uplift: dict[str, float] = {}
    recovered = 0.0
    removed_units = 0  # donated + returned units

    def state() -> tuple[float, int]:
        """(loss_try, at-risk units still unsold) from the cumulative state."""
        _, d = window_demand(ctx, lot, mix, as_of, uplift)
        at_risk = max(0, round(qty - d.expected))
        return max(0.0, at_risk * price - recovered), max(0, at_risk - removed_units)

    baseline, pool = state()
    current, steps = baseline, []
    for act in actions:
        a_type, p = act["type"], (act.get("params") or {})
        step: dict[str, Any] = {"action": a_type, "params": p, "feasible": True,
                                "units_saved": 0, "loss_after_try": round(current, 2),
                                "action_cost_try": 0.0, "net_benefit_try": 0.0,
                                "kg_saved": 0.0, "policy_refs": POLICY_REFS[a_type]}
        reason = None
        cost, units, kg = 0.0, 0, 0.0
        new_loss, new_pool = current, pool

        if a_type == "FEFO_PRIORITY":
            mix = 1.0
            new_loss, new_pool = state()
            units = pool - new_pool
        elif a_type in DISCOUNT_ACTIONS:
            pct = p.get("discount_pct")
            if not _num(pct) or not 0 < pct <= 100:
                reason = "discount_pct gerekli (0-100 arası sayı)"
            elif a_type not in limits:
                reason = f"{role} rolü {a_type} için indirim onaylayamaz"
            elif pct > limits[a_type]:
                reason = f"discount_pct {pct} > {role} limiti {limits[a_type]} ({a_type})"
            else:
                if a_type == "CAMPAIGN":
                    targets = eligible_today
                elif p.get("dealer_ids"):
                    ids = p["dealer_ids"]
                    targets = [d for d in ids if d in eligible_today]
                    if not targets:
                        reason = "dealer_ids içinde uygun bayi yok"
                else:
                    targets = sorted(eligible_today, key=lambda d: (-shares.get(d, 0.0), d)
                                     )[:TOP_DEALERS]
                if reason is None and not targets:
                    reason = "uygun bayi yok"
                if reason is None:
                    for d in targets:
                        uplift[d] = uplift.get(d, 0.0) + elasticity * pct / 100
                    new_loss, new_pool = state()
                    units = pool - new_pool
                    _, tot = window_demand(ctx, lot, mix, as_of, uplift)
                    _, disc = window_demand(ctx, lot, mix, as_of, uplift, frozenset(targets))
                    sold = disc.expected * (min(1.0, qty / tot.expected) if tot.expected else 0)
                    cost = sold * price * pct / 100
        elif a_type == "DONATION":
            need = params["donation_min_days_to_expiry"]
            n = p.get("units", pool)
            if days_left < need:
                reason = f"SKT'ye {days_left} gün kalmış, bağış için en az {need} gün gerekli"
            elif not _num(n) or n <= 0 or n != int(n):
                reason = "bağışlanacak adet yok"
            elif n > pool:
                reason = f"units {int(n)} > kalan riskli adet {pool}"
            else:
                units = int(n)
                removed_units += units
                new_pool = pool - units
                kg = units * prod["unit_weight_kg"]
        else:  # SUPPLIER_RETURN
            need = params["supplier_return_min_days_to_expiry"]
            n = p.get("units", pool)
            if not prod["supplier_return_allowed"]:
                reason = "ürün tedarikçi iadesine uygun değil"
            elif days_left < need:
                reason = f"SKT'ye {days_left} gün kalmış, iade için en az {need} gün gerekli"
            elif not _num(n) or n <= 0 or n != int(n):
                reason = "iade edilecek adet yok"
            elif n > pool:
                reason = f"units {int(n)} > kalan riskli adet {pool}"
            else:
                units = int(n)
                credit = units * prod["unit_cost_try"] * params["supplier_return_credit_pct"]
                recovered += credit
                removed_units += units
                new_loss = max(0.0, current - credit)
                new_pool = pool - units

        if reason is not None:
            step.update(feasible=False, infeasible_reason=reason)
        else:
            if a_type in ("FEFO_PRIORITY",) + DISCOUNT_ACTIONS:
                kg = units * prod["unit_weight_kg"]
            step.update(units_saved=units, loss_after_try=round(new_loss, 2),
                        action_cost_try=round(cost, 2),
                        net_benefit_try=round(current - new_loss - cost, 2),
                        kg_saved=round(kg, 2))
            current, pool = new_loss, new_pool
        steps.append(step)

    return {"lot_id": lot_id, "baseline_loss_try": round(baseline, 2), "steps": steps,
            "final_loss_try": round(current, 2),
            "total_net_benefit_try": round(sum(s["net_benefit_try"] for s in steps), 2)}
