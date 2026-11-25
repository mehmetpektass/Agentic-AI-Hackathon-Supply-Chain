#!/usr/bin/env python3
"""Deterministic synthetic data generator for the FEFO agent (TEAM_PLAN sections 3.1-3.12).

Python standard library only. Fixed seed. Output only under data-gen/out/:
    raw/        products, dealers, dealer_rules, shipments, inventory_snapshot, inbound_plan, calendar
    config/     params.json
    policy/     policy.md, process_guide.md (short placeholders, L owns the real text)
    scenarios/  scenarios.csv (ground truth, never synced to the agent package)
    DATA_ASSUMPTIONS.md

Run:  python data-gen/generate.py
Nothing is ever written to the repo-level data/ directory.
"""
from __future__ import annotations

import csv
import json
import random
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

SEED = 20261125
AS_OF = date(2026, 11, 25)
START = AS_OF - timedelta(days=30)  # first history day; last history day is AS_OF - 1
HIST = [START + timedelta(days=i) for i in range(30)]
OUT = Path(__file__).resolve().parent / "out"

# --------------------------------------------------------------------------------------
# Parameters (written to config/params.json). Values chosen by the data generator.
# --------------------------------------------------------------------------------------
PARAMS = {
    "elasticity": {"COLD": 1.5, "DRY": 1.2},
    "max_discount_pct_by_role": {"ticari": {"DEALER_OFFER": 20, "CAMPAIGN": 25}},
    "donation_min_days_to_expiry": 1,
    "supplier_return_min_days_to_expiry": 4,
    "supplier_return_credit_pct": 0.6,
    "forecast_low_confidence_wape": 0.40,
    "risk_level_thresholds_try": {"medium_min": 2000, "high_min": 10000},
    "slow_mover_daily_units": 8,
    "large_lot_days_of_cover": 20,
    "weekend_drop_factor": 0.85,
    "stopped_ordering_days": 7,
    "strict_dealer_share_pct": 70,
    "demand_drop_trend_pct": 20,
}

# --------------------------------------------------------------------------------------
# Dealers and acceptance rules
# --------------------------------------------------------------------------------------
DEALERS = [
    ("BAYI-01", "Bayi-01 Kadıköy", "Marmara", "CHAIN"),
    ("BAYI-02", "Bayi-02 Çarşı", "Ege", "CHAIN"),
    ("BAYI-03", "Bayi-03 Merkez", "İç Anadolu", "CHAIN"),
    ("BAYI-04", "Bayi-04 Sahil", "Akdeniz", "CHAIN"),
    ("BAYI-05", "Bayi-05 Pazar", "Marmara", "TRADITIONAL"),
    ("BAYI-06", "Bayi-06 Sanayi", "Ege", "TRADITIONAL"),
    ("BAYI-07", "Bayi-07 Terminal", "İç Anadolu", "TRADITIONAL"),
    ("BAYI-08", "Bayi-08 Liman", "Karadeniz", "TRADITIONAL"),
    ("BAYI-09", "Bayi-09 Kampüs", "Güneydoğu", "TRADITIONAL"),
    ("BAYI-10", "Bayi-10 Köy Yolu", "Akdeniz", "TRADITIONAL"),
]
DEALER_IDS = [d[0] for d in DEALERS]
DEALER_TYPE = {d[0]: d[3] for d in DEALERS}
CHAIN_IDS = [d for d in DEALER_IDS if DEALER_TYPE[d] == "CHAIN"]
# dealer -> (cold_pull, cold_min, dry_pull, dry_min); invariant: min >= pull + 2
RULES = {
    "BAYI-01": (4, 6, 30, 45),
    "BAYI-02": (4, 6, 30, 45),
    "BAYI-03": (5, 7, 35, 50),
    "BAYI-04": (4, 6, 30, 45),
    "BAYI-05": (1, 3, 10, 20),
    "BAYI-06": (1, 3, 10, 20),
    "BAYI-07": (2, 4, 12, 22),
    "BAYI-08": (1, 3, 10, 20),
    "BAYI-09": (1, 3, 10, 20),
    "BAYI-10": (1, 3, 10, 21),
}
MIN_DAYS = {d: {"COLD": r[1], "DRY": r[3]} for d, r in RULES.items()}
BASE_W = {"BAYI-01": 0.12, "BAYI-02": 0.11, "BAYI-03": 0.09, "BAYI-04": 0.08,
          "BAYI-05": 0.12, "BAYI-06": 0.10, "BAYI-07": 0.08, "BAYI-08": 0.10,
          "BAYI-09": 0.09, "BAYI-10": 0.11}

# Weekday factors used to generate demand (Mon..Sun, mean 1.0 per category)
WDF = {
    "COLD": [1.15, 1.12, 1.10, 1.12, 1.15, 0.78, 0.58],
    "DRY": [1.03, 1.03, 1.00, 1.00, 1.07, 0.97, 0.90],
}

# --------------------------------------------------------------------------------------
# Products: (sku, name, category, shelf_life_days, unit_cost, margin, weight_kg, daily_units, supplier, return_ok)
# daily_units is the generator's mean total demand per day across dealers (before weekday factor).
# --------------------------------------------------------------------------------------
PRODUCTS = [
    ("SKU-001", "Süzme Yoğurt 1 kg", "COLD", 21, 33.0, 1.45, 1.0, 100, "SUP-01", False),
    ("SKU-002", "Tam Yağlı Süt 1 L", "COLD", 16, 22.0, 1.40, 1.03, 120, "SUP-01", False),
    ("SKU-003", "Probiyotik Ayran 6'lı Paket", "COLD", 18, 52.0, 1.42, 1.5, 70, "SUP-02", False),
    ("SKU-004", "Beyaz Peynir 500 g", "COLD", 21, 88.0, 1.38, 0.5, 60, "SUP-02", True),
    ("SKU-005", "Kaşar Peyniri 400 g", "COLD", 21, 96.0, 1.40, 0.4, 50, "SUP-02", True),
    ("SKU-006", "Tereyağı 250 g", "COLD", 21, 78.0, 1.38, 0.25, 55, "SUP-03", True),
    ("SKU-007", "Kefir 500 ml", "COLD", 17, 18.0, 1.50, 0.52, 70, "SUP-01", False),
    ("SKU-008", "Dilimli Hindi Füme 150 g", "COLD", 20, 40.0, 1.45, 0.15, 60, "SUP-04", True),
    ("SKU-009", "Hazır Humus 200 g", "COLD", 16, 24.0, 1.45, 0.2, 55, "SUP-04", True),
    ("SKU-010", "Taze Krema 200 ml", "COLD", 18, 30.0, 1.40, 0.2, 45, "SUP-01", False),
    ("SKU-011", "Sade Tavuk Sosis 350 g", "COLD", 21, 46.0, 1.40, 0.35, 50, "SUP-05", True),
    ("SKU-012", "Taze Meyve Suyu 1 L", "COLD", 15, 28.0, 1.45, 1.05, 65, "SUP-05", False),
    ("SKU-013", "Çikolatalı Bisküvi 300 g", "DRY", 180, 17.0, 1.40, 0.3, 40, "SUP-06", True),
    ("SKU-014", "Üzüm Pekmezi 700 g", "DRY", 95, 44.0, 1.40, 0.95, 6.8, "SUP-06", True),
    ("SKU-015", "Pilavlık Pirinç 2,5 kg", "DRY", 365, 118.0, 1.25, 2.5, 38, "SUP-07", True),
    ("SKU-016", "İnce Bulgur 1 kg", "DRY", 300, 24.0, 1.30, 1.0, 45, "SUP-07", True),
    ("SKU-017", "Spagetti Makarna 500 g", "DRY", 365, 14.0, 1.35, 0.5, 70, "SUP-08", True),
    ("SKU-018", "Kırmızı Mercimek 1 kg", "DRY", 365, 52.0, 1.30, 1.0, 40, "SUP-07", True),
    ("SKU-019", "Kuru Nohut 1 kg", "DRY", 365, 58.0, 1.30, 1.0, 30, "SUP-07", True),
    ("SKU-020", "Kuru Fasulye 1 kg", "DRY", 365, 62.0, 1.30, 1.0, 32, "SUP-07", True),
    ("SKU-021", "Buğday Unu 2 kg", "DRY", 240, 46.0, 1.28, 2.0, 55, "SUP-08", True),
    ("SKU-022", "Toz Şeker 1 kg", "DRY", 365, 36.0, 1.20, 1.0, 80, "SUP-08", True),
    ("SKU-023", "Sofra Tuzu 750 g", "DRY", 365, 9.0, 1.50, 0.75, 35, "SUP-08", True),
    ("SKU-024", "Siyah Çay 500 g", "DRY", 365, 105.0, 1.30, 0.5, 42, "SUP-09", True),
    ("SKU-025", "Türk Kahvesi 100 g", "DRY", 300, 64.0, 1.35, 0.1, 36, "SUP-09", True),
    ("SKU-026", "Naturel Zeytinyağı 1 L", "DRY", 365, 235.0, 1.22, 0.92, 28, "SUP-10", True),
    ("SKU-027", "Ayçiçek Yağı 2 L", "DRY", 330, 118.0, 1.20, 1.85, 60, "SUP-10", True),
    ("SKU-028", "Domates Salçası 700 g", "DRY", 365, 48.0, 1.32, 0.7, 44, "SUP-11", True),
    ("SKU-029", "Konserve Domates 400 g", "DRY", 365, 19.0, 1.35, 0.4, 50, "SUP-11", True),
    ("SKU-030", "Konserve Ton Balığı 160 g", "DRY", 365, 58.0, 1.30, 0.16, 34, "SUP-11", True),
    ("SKU-031", "Tuzlu Kraker 200 g", "DRY", 240, 14.0, 1.40, 0.2, 52, "SUP-06", True),
    ("SKU-032", "Sütlü Çikolata 80 g", "DRY", 270, 21.0, 1.45, 0.08, 66, "SUP-06", True),
    ("SKU-033", "Çiğ Fındık 250 g", "DRY", 300, 96.0, 1.30, 0.25, 26, "SUP-09", True),
    ("SKU-034", "Çekirdeksiz Kuru Üzüm 250 g", "DRY", 330, 48.0, 1.32, 0.25, 30, "SUP-09", True),
    ("SKU-035", "Çilek Reçeli 380 g", "DRY", 365, 38.0, 1.35, 0.55, 28, "SUP-11", True),
    ("SKU-036", "Çiçek Balı 460 g", "DRY", 365, 125.0, 1.30, 0.62, 22, "SUP-10", True),
    ("SKU-037", "Tahin 600 g", "DRY", 280, 92.0, 1.30, 0.8, 24, "SUP-10", True),
    ("SKU-038", "Siyah Zeytin 500 g", "DRY", 365, 72.0, 1.32, 0.7, 34, "SUP-11", True),
    ("SKU-039", "Karışık Turşu 720 g", "DRY", 365, 34.0, 1.38, 0.95, 32, "SUP-11", True),
    ("SKU-040", "Kuru Kayısı 500 g", "DRY", 330, 88.0, 1.30, 0.5, 25, "SUP-09", True),
]
PROD = {p[0]: p for p in PRODUCTS}
SKUS = [p[0] for p in PRODUCTS]
CAT = {p[0]: p[2] for p in PRODUCTS}
SHELF = {p[0]: p[3] for p in PRODUCTS}
PRICE = {p[0]: round(p[4] * p[5], 2) for p in PRODUCTS}
COST = {p[0]: p[4] for p in PRODUCTS}

# --------------------------------------------------------------------------------------
# Scenario SKUs. "lots" are received-date offsets (days relative to AS_OF) of in-stock lots.
# ratio = at-risk units as a share of the expected demand of the risky lot.
# --------------------------------------------------------------------------------------
STRICT_FIXED = {"BAYI-01": 0.26, "BAYI-02": 0.22, "BAYI-03": 0.17, "BAYI-04": 0.15}  # chain 80%
SPECIAL = {
    "SKU-001": dict(scn="FIFO_VIOLATION", lots=[-12, -8], ratio=0.60, basis="fefo",
                    bins=["C-14-4", "A-02-1"], override_last7_lot=1),
    "SKU-002": dict(scn="SHORT_SHELF_LIFE", lots=[-9], ratio=0.45),
    "SKU-003": dict(scn="STRICT_DEALER_ONLY", lots=[-11], ratio=0.45, fixed=STRICT_FIXED),
    "SKU-004": dict(scn="DEALER_STOPPED_ORDERING", lots=[-13], ratio=0.40,
                    fixed={"BAYI-05": 0.16}, stop_dealer="BAYI-05"),
    "SKU-005": dict(scn="INBOUND_FRESH_LOT", lots=[-13], ratio=0.40),
    "SKU-006": dict(scn="DEMAND_DROP_TREND", lots=[-12], ratio=0.50, drop=0.70),
    "SKU-007": dict(scn="LOW_CONFIDENCE", lots=[-9], ratio=0.25, noisy=True, noise=0.35, p_order=0.85),
    "SKU-008": dict(scn="CONTROL", lots=[-11], control_frac=0.85),
    "SKU-013": dict(scn="UNSAVEABLE", lots=[-165, -60], units=110, bins=["F-07-1", "F-02-2"]),
    "SKU-014": dict(scn="SLOW_MOVER_LARGE_LOT", lots=[-35], ratio=0.35, noise=0.10, p_order=1.0,
                    explicit={"BAYI-01": 0.22, "BAYI-02": 0.18, "BAYI-05": 0.24, "BAYI-06": 0.20,
                              "BAYI-08": 0.16}),
}
PRIMARY_LOT_INDEX = {"SKU-001": 0, "SKU-013": 0}  # which in-stock lot is the scenario lot (default 0)
CAMPAIGNS = {-16: ["SKU-020"], -9: ["SKU-020", "SKU-032"]}   # day offset -> sku list (demand x1.5)
STOCKOUTS = {-12: ["SKU-025"], -5: ["SKU-031"]}                # day offset -> sku list (no shipments)
INBOUND_NORMAL = {"SKU-009": (3, 420), "SKU-010": (5, 300), "SKU-011": (2, 500), "SKU-012": (6, 380),
                  "SKU-016": (8, 900), "SKU-021": (4, 700), "SKU-026": (9, 260), "SKU-033": (7, 240)}
INBOUND_SCENARIO = {"SKU-005": (3, 900)}


def srng(*parts) -> random.Random:
    return random.Random(f"{SEED}/" + "/".join(str(p) for p in parts))


# --------------------------------------------------------------------------------------
# Demand generation
# --------------------------------------------------------------------------------------
def weights_for(sku: str, rng: random.Random) -> dict:
    cfg = SPECIAL.get(sku, {})
    if "explicit" in cfg:
        return {d: cfg["explicit"].get(d, 0.0) for d in DEALER_IDS}
    raw = {d: BASE_W[d] * rng.uniform(0.85, 1.15) for d in DEALER_IDS}
    fixed = cfg.get("fixed", {})
    rest = [d for d in DEALER_IDS if d not in fixed]
    scale = (1.0 - sum(fixed.values())) / sum(raw[d] for d in rest)
    w = {d: raw[d] * scale for d in rest}
    w.update(fixed)
    return w


def gen_demand(sku: str, rng: random.Random) -> list:
    """Return [(date, dealer, qty)] for the 30 history days."""
    cfg = SPECIAL.get(sku, {})
    cat = CAT[sku]
    F = PROD[sku][7]
    noise = cfg.get("noise", 0.25)
    p_order = cfg.get("p_order", 0.92)
    w = weights_for(sku, rng)
    stop = cfg.get("stop_dealer")
    rows = []
    daymult = [0.2, 0.4, 0.7, 1.0, 1.4, 1.9, 2.5]
    for d in HIST:
        off = (d - AS_OF).days
        if sku in STOCKOUTS.get(off, []):
            continue
        m = rng.choice(daymult) if cfg.get("noisy") else 1.0
        if sku in CAMPAIGNS.get(off, []):
            m *= 1.5
        if cfg.get("drop") and off >= -7:
            m *= cfg["drop"]
        for dealer in DEALER_IDS:
            if w[dealer] <= 0:
                continue
            r1 = rng.random()
            r2 = rng.uniform(1 - noise, 1 + noise)
            if stop == dealer and off >= -9:
                continue
            if r1 > p_order:
                continue
            e = F * w[dealer] * WDF[cat][d.weekday()] * m
            q = int(e * r2 + 0.5)
            if q > 0:
                rows.append((d, dealer, q))
    # keep every ordering dealer "active": at least one order in the last 4 days
    have = {}
    for d, dealer, q in rows:
        have.setdefault(dealer, []).append(d)
    for dealer in DEALER_IDS:
        if w[dealer] <= 0:
            continue
        ds = have.get(dealer, [])
        if stop == dealer:
            target = AS_OF - timedelta(days=10)
            if target not in ds:
                e = F * w[dealer] * WDF[cat][target.weekday()]
                rows.append((target, dealer, max(1, int(e + 0.5))))
            continue
        if not any(x >= AS_OF - timedelta(days=4) for x in ds):
            d = AS_OF - timedelta(days=1)
            e = F * w[dealer] * WDF[cat][d.weekday()]
            rows.append((d, dealer, max(1, int(e + 0.5))))
    return rows


def series_stats(rows: list):
    daily = {d: 0 for d in HIST}
    for d, _, q in rows:
        daily[d] += q
    tot = sum(daily.values())
    last7 = sum(daily[d] for d in HIST[-7:]) / 7.0
    prev21 = sum(daily[d] for d in HIST[2:23]) / 21.0  # days -28 .. -8
    trend = (last7 / prev21 - 1.0) * 100 if prev21 > 0 else 0.0
    # 7-day backtest WAPE (same-weekday mean of up to 4 earlier values)
    num = den = 0.0
    for t in HIST[-7:]:
        prev = [daily[x] for x in HIST if x < t and x.weekday() == t.weekday()][-4:]
        f = sum(prev) / len(prev)
        num += abs(daily[t] - f)
        den += daily[t]
    wape = num / den if den else 1.0
    return dict(wape=wape, trend=trend, avg7=last7)


def accept(sku: str, st: dict) -> bool:
    cfg = SPECIAL.get(sku, {})
    scn = cfg.get("scn")
    if scn == "LOW_CONFIDENCE":
        return st["wape"] >= 0.55 and abs(st["trend"]) <= 15
    if scn == "DEMAND_DROP_TREND":
        return st["trend"] <= -24 and st["wape"] <= 0.38
    if st["wape"] > 0.30:
        return False
    if scn == "DEALER_STOPPED_ORDERING":
        return -17 <= st["trend"] <= -5
    if scn == "SLOW_MOVER_LARGE_LOT":
        return 5.0 <= st["avg7"] <= 7.6 and abs(st["trend"]) <= 15
    return abs(st["trend"]) <= 15


# --------------------------------------------------------------------------------------
# Lots
# --------------------------------------------------------------------------------------
def build_lots(sku: str) -> list:
    """All lots of the SKU (historical depleted + in stock). Dict per lot."""
    cfg = SPECIAL.get(sku, {})
    cat, S = CAT[sku], SHELF[sku]
    rng = srng(sku, "lots")
    if "lots" in cfg:
        offs = list(cfg["lots"])
    elif cat == "COLD":
        left0 = rng.randint(7, S - 8)
        offs = [-(S - left0)]
    else:
        offs = [-rng.randint(30, 60)]
    lots = [dict(received=AS_OF + timedelta(days=o), in_stock=True) for o in offs]
    if cat == "COLD":
        P = S - 7
        r = min(offs) - P
        while True:
            lots.append(dict(received=AS_OF + timedelta(days=r), in_stock=False))
            if r <= -30:
                break
            r -= P
    for l in lots:
        l["expiry"] = l["received"] + timedelta(days=S)
        if l["in_stock"]:
            assert l["expiry"] > AS_OF, (sku, l)
        else:
            assert l["expiry"] < AS_OF, (sku, l)
    lots.sort(key=lambda l: l["received"])
    for n, l in enumerate(lots, 1):
        l["lot_id"] = f"LOT-{sku}-{n}"
        l["sku"] = sku
        l["consumed"] = 0
    in_stock = [l for l in lots if l["in_stock"]]
    bins = cfg.get("bins")
    for i, l in enumerate(in_stock):
        if bins:
            l["bin"] = bins[i]
        else:
            aisle = rng.choice("ABC") if cat == "COLD" else rng.choice("DEFGH")
            l["bin"] = f"{aisle}-{rng.randint(1, 15):02d}-{rng.randint(1, 4)}"
    return lots


def allocate(sku: str, lots: list, rows: list) -> list:
    """FEFO allocation of each demand row to one lot. Returns shipment dicts."""
    cfg = SPECIAL.get(sku, {})
    cat = CAT[sku]
    in_stock = [l for l in lots if l["in_stock"]]
    out = []
    for d, dealer, q in sorted(rows, key=lambda r: (r[0], r[1])):
        need = MIN_DAYS[dealer][cat]
        elig = [l for l in lots if l["received"] <= d and (l["expiry"] - d).days >= need]
        elig.sort(key=lambda l: (l["expiry"], l["received"]))
        assert elig, (sku, d, dealer)
        pick = elig[0]
        k = cfg.get("override_last7_lot")
        if k is not None and (AS_OF - d).days <= 7:
            pick = in_stock[k]
            assert pick in elig, (sku, d, dealer)
        pick["consumed"] += q
        out.append(dict(date=d, dealer_id=dealer, sku_id=sku, lot_id=pick["lot_id"], qty_units=q))
    return out


# --------------------------------------------------------------------------------------
# Reference risk model (mirrors design.md; used to size lots and to self-check scenarios)
# --------------------------------------------------------------------------------------
class Model:
    def __init__(self, ships, lots_by_sku):
        self.lots_by_sku = lots_by_sku
        self.daily = {s: {d: 0 for d in HIST} for s in SKUS}
        self.dealer30 = {s: {} for s in SKUS}
        self.last7_lot = {s: {} for s in SKUS}
        self.last_order = {s: {} for s in SKUS}
        for r in ships:
            s, d = r["sku_id"], r["date"]
            self.daily[s][d] += r["qty_units"]
            self.dealer30[s][r["dealer_id"]] = self.dealer30[s].get(r["dealer_id"], 0) + r["qty_units"]
            if (AS_OF - d).days <= 7:
                self.last7_lot[s][r["lot_id"]] = self.last7_lot[s].get(r["lot_id"], 0) + r["qty_units"]
            lo = self.last_order[s].get(r["dealer_id"])
            if lo is None or d > lo:
                self.last_order[s][r["dealer_id"]] = d
        self.share = {}
        for s in SKUS:
            tot = sum(self.dealer30[s].values())
            self.share[s] = {d: v / tot for d, v in self.dealer30[s].items()} if tot else {}
        self.cat_daily = {c: {d: 0 for d in HIST} for c in ("COLD", "DRY")}
        for s in SKUS:
            for d, v in self.daily[s].items():
                self.cat_daily[CAT[s]][d] += v

    def wd_factor(self, cat):
        vals = self.cat_daily[cat]
        mean_all = sum(vals.values()) / len(HIST)
        out = []
        for wd in range(7):
            xs = [vals[d] for d in HIST if d.weekday() == wd]
            out.append(sum(xs) / len(xs) / mean_all)
        return out

    def fvals(self, sku, day):
        ds = [x for x in HIST if x.weekday() == day.weekday()][-4:]
        v = [self.daily[sku][x] for x in ds]
        return {"low": min(v), "exp": sum(v) / len(v), "high": max(v)}

    def mix(self, lot):
        tot = sum(self.last7_lot[lot["sku"]].values())
        return self.last7_lot[lot["sku"]].get(lot["lot_id"], 0) / tot if tot else 0.0

    def demand(self, lot, band="exp", mix=None, uplift=None):
        sku = lot["sku"]
        cat = CAT[sku]
        mix = self.mix(lot) if mix is None else mix
        uplift = uplift or {}
        min_all = min(MIN_DAYS[d][cat] for d in DEALER_IDS)
        total, window = 0.0, 0
        for off in range(0, 500):
            day = AS_OF + timedelta(days=off)
            left = (lot["expiry"] - day).days
            if left < min_all:
                break
            elig = [d for d in DEALER_IDS if left >= MIN_DAYS[d][cat]]
            window += 1
            sh = sum(self.share[sku].get(d, 0.0) * (1 + uplift.get(d, 0.0)) for d in elig)
            total += self.fvals(sku, day)[band] * sh * mix
        return total, window

    def wape(self, sku):
        daily = self.daily[sku]
        num = den = 0.0
        for t in HIST[-7:]:
            prev = [daily[x] for x in HIST if x < t and x.weekday() == t.weekday()][-4:]
            f = sum(prev) / len(prev)
            num += abs(daily[t] - f)
            den += daily[t]
        return num / den if den else 1.0

    def trend(self, sku):
        daily = self.daily[sku]
        l7 = sum(daily[d] for d in HIST[-7:]) / 7.0
        p21 = sum(daily[d] for d in HIST[2:23]) / 21.0
        return (l7 / p21 - 1) * 100 if p21 else 0.0

    def avg7(self, sku):
        return sum(self.daily[sku][d] for d in HIST[-7:]) / 7.0

    def risk(self, lot):
        sku = lot["sku"]
        q = lot["qty_units"]
        d_low, win = self.demand(lot, "low")
        d_exp, _ = self.demand(lot, "exp")
        d_high, _ = self.demand(lot, "high")
        at = {"low": max(0, round(q - d_high)), "expected": max(0, round(q - d_exp)),
              "high": max(0, round(q - d_low))}
        loss = {k: round(v * PRICE[sku], 2) for k, v in at.items()}
        return dict(window=win, at_risk=at, loss=loss, d_exp=d_exp)


def risk_level(loss):
    t = PARAMS["risk_level_thresholds_try"]
    return "HIGH" if loss >= t["high_min"] else "MEDIUM" if loss >= t["medium_min"] else "LOW"


def confidence(wape):
    t = PARAMS["forecast_low_confidence_wape"]
    return "LOW" if wape > t else "MEDIUM" if wape > t / 2 else "HIGH"


def fifo_flag(model, ships_by_sku, lot):
    """Older in-stock lot shipped over by a fresher lot in the last 7 days while eligible."""
    sku = lot["sku"]
    cat = CAT[sku]
    lots = {l["lot_id"]: l for l in model.lots_by_sku[sku]}
    for r in ships_by_sku[sku]:
        if (AS_OF - r["date"]).days > 7:
            continue
        shipped = lots[r["lot_id"]]
        if shipped["expiry"] > lot["expiry"]:
            left = (lot["expiry"] - r["date"]).days
            if lot["received"] <= r["date"] and left >= MIN_DAYS[r["dealer_id"]][cat]:
                return True
    return False


def reason_codes(model, ships_by_sku, inbound, lot, rk):
    sku, cat = lot["sku"], CAT[lot["sku"]]
    codes = []
    if lot["in_stock"] and fifo_flag(model, ships_by_sku, lot):
        codes.append("FIFO_VIOLATION")
    avg7 = model.avg7(sku)
    if avg7 < PARAMS["slow_mover_daily_units"] and avg7 > 0 and \
            lot["qty_units"] / avg7 > PARAMS["large_lot_days_of_cover"]:
        codes.append("SLOW_MOVER_LARGE_LOT")
    f = model.wd_factor(cat)
    if cat == "COLD" and f[5] < PARAMS["weekend_drop_factor"] and f[6] < PARAMS["weekend_drop_factor"]:
        codes.append("SHORT_SHELF_LIFE")
    for dealer, sh in sorted(model.share[sku].items()):
        if sh >= 0.05 and (AS_OF - model.last_order[sku][dealer]).days >= PARAMS["stopped_ordering_days"]:
            codes.append("DEALER_STOPPED_ORDERING")
            break
    chain = sum(model.share[sku].get(d, 0) for d in CHAIN_IDS) * 100
    if chain > PARAMS["strict_dealer_share_pct"]:
        codes.append("STRICT_DEALER_ONLY")
    if model.trend(sku) <= -PARAMS["demand_drop_trend_pct"]:
        codes.append("DEMAND_DROP_TREND")
    for row in inbound:
        if row["sku_id"] == sku and row["expiry_date"] > lot["expiry"] and \
                0 <= (row["expected_date"] - AS_OF).days < rk["window"]:
            codes.append("INBOUND_FRESH_LOT")
            break
    days_left = (lot["expiry"] - AS_OF).days
    p = PARAMS
    if (rk["at_risk"]["low"] > 0 and days_left < min(p["donation_min_days_to_expiry"],
                                                      p["supplier_return_min_days_to_expiry"])) \
            or (rk["at_risk"]["expected"] > 0 and rk["window"] == 0):
        codes.append("UNSAVEABLE")
    return codes


def simulate(model, lot, steps):
    """Loss waterfall using the reference demand model. steps = [(type, discount_pct)]."""
    sku, cat = lot["sku"], CAT[lot["sku"]]
    left0 = (lot["expiry"] - AS_OF).days
    elig_today = [d for d in DEALER_IDS if left0 >= MIN_DAYS[d][cat]]
    mix, uplift = model.mix(lot), {}
    el = PARAMS["elasticity"][cat]

    def loss():
        d, _ = model.demand(lot, "exp", mix, uplift)
        return max(0, round(lot["qty_units"] - d)) * PRICE[sku]

    out = [("BASELINE", loss())]
    for typ, disc in steps:
        if typ == "FEFO_PRIORITY":
            mix = 1.0
        elif typ == "DEALER_OFFER":
            top = sorted(elig_today, key=lambda d: (-model.share[sku].get(d, 0), d))[:2]
            for d in top:
                uplift[d] = uplift.get(d, 0) + el * disc / 100
        elif typ == "CAMPAIGN":
            for d in elig_today:
                uplift[d] = uplift.get(d, 0) + el * disc / 100
        out.append((f"{typ}{'' if typ == 'FEFO_PRIORITY' else ' ' + str(disc) + '%'}", loss()))
    return out


# --------------------------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------------------------
def write_csv(path: Path, header: list, rows: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def b(x: bool) -> str:
    return "true" if x else "false"


POLICY_MD = """# FEFO Politikası (sentetik taslak — içeriğin sahibi L)

> Bu dosya `data-gen/generate.py` tarafından üretilen kısa bir yer tutucudur. Sayılar `config/params.json` ile aynıdır.

- **POL-1.1** FEFO: Son kullanma tarihi en yakın uygun lot önce sevk edilir.
- **POL-1.2** Bayi kabul kuralı: Bir lot, `(SKT - sevk günü) >= min_days_on_receipt` ise o bayiye sevk edilebilir. Zincir bayilerde COLD için 6-7, DRY için 45-50 gün; geleneksel bayilerde COLD için 3-4, DRY için 20-22 gün.
- **POL-2.1** Bayiye özel teklif (DEALER_OFFER): `ticari` rolü en fazla %20 indirim onaylayabilir.
- **POL-2.2** Kampanya (CAMPAIGN): `ticari` rolü en fazla %25 indirim onaylayabilir.
- **POL-3.1** Bağış (DONATION): SKT'ye en az 1 gün kalmış olmalıdır.
- **POL-3.2** Tedarikçi iadesi (SUPPLIER_RETURN): ürün iadeye uygunsa ve SKT'ye en az 4 gün varsa yapılır; geri kazanım maliyetin %60'ıdır.
- **POL-4.1** Onay: `depo` FEFO, bağış ve iade aksiyonlarını; `ticari` bunlara ek olarak indirimli aksiyonları onaylar. Ajan hiçbir mesajı kendi başına göndermez.
"""

PROCESS_MD = """# FEFO Süreç Rehberi (sentetik taslak — içeriğin sahibi L)

> Bu dosya `data-gen/generate.py` tarafından üretilen kısa bir yer tutucudur.

- **PRC-1.1** Her sabah riskli lotlar listelenir; sıralama beklenen ₺ kaybına göredir.
- **PRC-1.2** Her lot için neden kodları gösterilir (ör. FIFO_VIOLATION, STRICT_DEALER_ONLY).
- **PRC-2.1** Risk seviyesi: beklenen kayıp 2.000 ₺'nin altında LOW, 10.000 ₺'ye kadar MEDIUM, üstü HIGH.
- **PRC-2.2** Kayıp şelalesi: aksiyonlar sırayla uygulanır; her adım kaybın ne kadar düştüğünü gösterir.
- **PRC-3.1** Onaydan sonra depo, ticari ekip ve tedarikçi için yalnızca TASLAK mesajlar hazırlanır.
- **PRC-3.2** Tahmin güveni LOW ise karar vermeden önce depo ekibi sayımı doğrular.
"""


def main() -> int:
    # --- demand with deterministic acceptance search -----------------------------------
    demand, attempts = {}, {}
    for sku in SKUS:
        for attempt in range(200):
            rows = gen_demand(sku, srng(sku, "demand", attempt))
            if accept(sku, series_stats(rows)):
                demand[sku], attempts[sku] = rows, attempt
                break
        else:
            raise SystemExit(f"no acceptable demand series for {sku}")

    # --- lots, allocation ----------------------------------------------------------------
    lots_by_sku = {s: build_lots(s) for s in SKUS}
    ships = []
    for s in SKUS:
        ships += allocate(s, lots_by_sku[s], demand[s])
    ships.sort(key=lambda r: (r["date"], r["dealer_id"], r["sku_id"], r["lot_id"]))
    ships_by_sku = {s: [r for r in ships if r["sku_id"] == s] for s in SKUS}
    model = Model(ships, lots_by_sku)

    # --- inbound plan ------------------------------------------------------------------
    inbound = []
    for sku, (off, qty) in sorted({**INBOUND_NORMAL, **INBOUND_SCENARIO}.items()):
        n = len(lots_by_sku[sku]) + 1
        exp_date = AS_OF + timedelta(days=off)
        inbound.append(dict(expected_date=exp_date, sku_id=sku, lot_id=f"LOT-{sku}-{n}", qty_units=qty,
                            expiry_date=exp_date + timedelta(days=SHELF[sku])))
    inbound.sort(key=lambda r: (r["expected_date"], r["sku_id"]))

    # --- size in-stock lots ------------------------------------------------------------
    for sku in SKUS:
        cfg = SPECIAL.get(sku, {})
        cat = CAT[sku]
        in_stock = [l for l in lots_by_sku[sku] if l["in_stock"]]
        rng = srng(sku, "qty")
        primary = in_stock[PRIMARY_LOT_INDEX.get(sku, 0)]
        for l in in_stock:
            if l is primary and cfg.get("scn") and cfg["scn"] not in ("CONTROL",):
                continue
            if cfg.get("scn") == "CONTROL":
                d_exp, _ = model.demand(l, "exp")
                l["qty_units"] = int(cfg["control_frac"] * d_exp)
            elif cat == "COLD":
                d_low, _ = model.demand(l, "low")
                l["qty_units"] = max(20, int(0.45 * d_low) // 5 * 5)
            else:
                avg30 = sum(model.daily[sku].values()) / 30.0
                l["qty_units"] = max(30, int(rng.uniform(10, 24) * avg30) // 10 * 10)
        if cfg.get("scn") and cfg["scn"] != "CONTROL":
            if "units" in cfg:
                primary["qty_units"] = cfg["units"]
            else:
                mix = 1.0 if cfg.get("basis") == "fefo" else None
                d_basis, _ = model.demand(primary, "exp", mix=mix)
                primary["qty_units"] = int(round(d_basis * (1 + cfg["ratio"])))
    lots_all = [l for s in SKUS for l in lots_by_sku[s]]
    stock = [l for l in lots_all if l["in_stock"]]
    for l in stock:
        assert l["qty_units"] > 0, l

    # --- risk table ---------------------------------------------------------------------
    risk_rows = []
    for l in stock:
        rk = model.risk(l)
        codes = reason_codes(model, ships_by_sku, inbound, l, rk)
        risk_rows.append((l, rk, codes))
    risk_rows.sort(key=lambda t: (-t[1]["loss"]["expected"], t[0]["lot_id"]))

    # --- write files ----------------------------------------------------------------------
    if OUT.exists():
        shutil.rmtree(OUT)
    raw, cfgdir, pol, scn = OUT / "raw", OUT / "config", OUT / "policy", OUT / "scenarios"

    write_csv(raw / "products.csv",
              ["sku_id", "sku_name", "category", "shelf_life_days", "unit_cost_try", "unit_price_try",
               "unit_weight_kg", "supplier_id", "supplier_return_allowed"],
              [[p[0], p[1], p[2], p[3], f"{COST[p[0]]:.2f}", f"{PRICE[p[0]]:.2f}", f"{p[6]:.3f}", p[8], b(p[9])]
               for p in PRODUCTS])
    write_csv(raw / "dealers.csv", ["dealer_id", "dealer_name", "region", "dealer_type"],
              [list(d) for d in DEALERS])
    write_csv(raw / "dealer_rules.csv", ["dealer_id", "category", "shelf_pull_days", "min_days_on_receipt"],
              [[d, c, RULES[d][i], RULES[d][i + 1]] for d in DEALER_IDS
               for c, i in (("COLD", 0), ("DRY", 2))])
    write_csv(raw / "shipments.csv", ["date", "dealer_id", "sku_id", "lot_id", "qty_units"],
              [[r["date"].isoformat(), r["dealer_id"], r["sku_id"], r["lot_id"], r["qty_units"]] for r in ships])
    write_csv(raw / "inventory_snapshot.csv",
              ["sku_id", "lot_id", "qty_units", "expiry_date", "received_date", "location_bin"],
              [[l["sku"], l["lot_id"], l["qty_units"], l["expiry"].isoformat(), l["received"].isoformat(),
                l["bin"]] for l in sorted(stock, key=lambda x: (x["sku"], x["lot_id"]))])
    write_csv(raw / "inbound_plan.csv", ["expected_date", "sku_id", "lot_id", "qty_units", "expiry_date"],
              [[r["expected_date"].isoformat(), r["sku_id"], r["lot_id"], r["qty_units"],
                r["expiry_date"].isoformat()] for r in inbound])
    cal = []
    for d in HIST:
        off = (d - AS_OF).days
        camp, so = sorted(CAMPAIGNS.get(off, [])), sorted(STOCKOUTS.get(off, []))
        cal.append([d.isoformat(), b(bool(camp)), ";".join(camp), ";".join(so)])
    write_csv(raw / "calendar.csv", ["date", "is_campaign_day", "campaign_sku_ids", "stockout_sku_ids"], cal)

    cfgdir.mkdir(parents=True, exist_ok=True)
    (cfgdir / "params.json").write_text(json.dumps(PARAMS, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pol.mkdir(parents=True, exist_ok=True)
    (pol / "policy.md").write_text(POLICY_MD, encoding="utf-8")
    (pol / "process_guide.md").write_text(PROCESS_MD, encoding="utf-8")

    truth = []
    for sku in SKUS:
        cfg = SPECIAL.get(sku)
        if not cfg:
            continue
        in_stock = [l for l in lots_by_sku[sku] if l["in_stock"]]
        lot = in_stock[PRIMARY_LOT_INDEX.get(sku, 0)]
        expected = cfg["scn"] if cfg["scn"] not in ("CONTROL", "LOW_CONFIDENCE") else ""
        truth.append([sku, lot["lot_id"], cfg["scn"], expected])
    write_csv(scn / "scenarios.csv", ["sku_id", "lot_id", "scenario", "expected_reason_code"], truth)

    self_check(model, ships_by_sku, inbound, risk_rows, truth, lots_by_sku)
    write_assumptions(model, risk_rows, attempts, ships, stock, truth, lots_by_sku)
    return 0


# --------------------------------------------------------------------------------------
# Self-check (section 3.12 on the written files + scenario expectations)
# --------------------------------------------------------------------------------------
def read_csv(path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def self_check(model, ships_by_sku, inbound, risk_rows, truth, lots_by_sku):
    errs = []
    raw = OUT / "raw"
    products = {r["sku_id"]: r for r in read_csv(raw / "products.csv")}
    dealers = {r["dealer_id"] for r in read_csv(raw / "dealers.csv")}
    rules = {(r["dealer_id"], r["category"]): r for r in read_csv(raw / "dealer_rules.csv")}
    inv = {r["lot_id"]: r for r in read_csv(raw / "inventory_snapshot.csv")}
    ships = read_csv(raw / "shipments.csv")
    cal = read_csv(raw / "calendar.csv")
    # reference tables
    for (d, c), r in rules.items():
        if d not in dealers or int(r["min_days_on_receipt"]) < int(r["shelf_pull_days"]) + 2:
            errs.append(f"dealer_rules {d}/{c}")
    for p in products.values():
        if not float(p["unit_price_try"]) > float(p["unit_cost_try"]) > 0:
            errs.append(f"price {p['sku_id']}")
        lo, hi = (7, 21) if p["category"] == "COLD" else (90, 365)
        if not lo <= int(p["shelf_life_days"]) <= hi:
            errs.append(f"shelf {p['sku_id']}")
    for l in inv.values():
        exp = date.fromisoformat(l["expiry_date"])
        rec = date.fromisoformat(l["received_date"])
        if l["sku_id"] not in products or int(l["qty_units"]) <= 0:
            errs.append(f"inventory {l['lot_id']}")
        if (exp - rec).days != int(products[l["sku_id"]]["shelf_life_days"]):
            errs.append(f"expiry/shelf {l['lot_id']}")
    stockout = {(c["date"], s) for c in cal for s in c["stockout_sku_ids"].split(";") if s}
    dates = {d.isoformat() for d in HIST}
    seen = set()
    for i, r in enumerate(ships, 2):
        key = (r["date"], r["dealer_id"], r["sku_id"], r["lot_id"])
        if key in seen:
            errs.append(f"duplicate shipment row {i}")
        seen.add(key)
        if r["date"] not in dates or r["dealer_id"] not in dealers or r["sku_id"] not in products \
                or int(r["qty_units"]) <= 0 or (r["date"], r["sku_id"]) in stockout:
            errs.append(f"shipment row {i}")
        lot = inv.get(r["lot_id"])
        if lot:
            d = date.fromisoformat(r["date"])
            need = int(rules[(r["dealer_id"], products[r["sku_id"]]["category"])]["min_days_on_receipt"])
            if lot["sku_id"] != r["sku_id"] or d < date.fromisoformat(lot["received_date"]) or \
                    (date.fromisoformat(lot["expiry_date"]) - d).days < need:
                errs.append(f"shipment eligibility row {i}")
    if len(dates) != 30 or len(cal) != 30:
        errs.append("history length")
    # scenario expectations
    by_lot = {l["lot_id"]: (rk, codes) for l, rk, codes in risk_rows}
    listed_skus = {l["sku"] for l, rk, _ in risk_rows if rk["at_risk"]["expected"] > 0}
    scn_skus = {t[0] for t in truth}
    for sku, lot_id, scn, exp in truth:
        rk, codes = by_lot[lot_id]
        if exp and exp not in codes:
            errs.append(f"{sku} missing {exp}, got {codes}")
        if scn == "CONTROL" and sku in listed_skus:
            errs.append("control is risky")
        if scn == "LOW_CONFIDENCE":
            if sku not in listed_skus or confidence(model.wape(sku)) != "LOW":
                errs.append("low-confidence SKU not LOW/listed")
    extra = sorted(listed_skus - scn_skus)
    if extra:
        errs.append(f"non-scenario SKUs risky: {extra}")
    for sku in SKUS:
        if sku not in scn_skus and confidence(model.wape(sku)) == "LOW":
            errs.append(f"unexpected LOW confidence {sku}")
    # exactly one lot per SKU listed except none duplicated risk lots
    for l, rk, codes in risk_rows:
        if rk["at_risk"]["expected"] > 0 and l["lot_id"] not in {t[1] for t in truth}:
            errs.append(f"unexpected risky lot {l['lot_id']}")
    # category weekday factors
    fc, fd = model.wd_factor("COLD"), model.wd_factor("DRY")
    if not (fc[5] < 0.85 and fc[6] < 0.85 and fd[5] >= 0.88 and fd[6] >= 0.88):
        errs.append(f"weekday factors {fc[5:]} {fd[5:]}")
    if len(truth) < 8 or len([t for t in truth if t[2] not in ("CONTROL", "LOW_CONFIDENCE")]) < 6:
        errs.append("scenario count")
    if errs:
        print("SELF-CHECK FAILED:", *errs, sep="\n  ", file=sys.stderr)
        raise SystemExit(1)
    print("self-check OK")


def write_assumptions(model, risk_rows, attempts, ships, stock, truth, lots_by_sku):
    P = PARAMS
    fc, fd = model.wd_factor("COLD"), model.wd_factor("DRY")
    scn_by_lot = {t[1]: t for t in truth}
    wf_steps = [("FEFO_PRIORITY", 0), ("DEALER_OFFER", 10), ("CAMPAIGN", 15)]
    L = []
    a = L.append
    a("# DATA_ASSUMPTIONS.md (synthetic data, task 1.1)")
    a("")
    a("Generated by `data-gen/generate.py` (seed `%d`, as_of_date `%s`). 100%% synthetic; present it as a "
      "\"representative scenario\", never as real data. Rerunning the generator reproduces every file byte for byte." % (SEED, AS_OF))
    a("")
    a("## 1. Threshold keys added to `config/params.json` (for L, the data owner)")
    a("")
    a("The first six keys are the new ones. The reason-code rules that use them are in `design.md` (risk.py). "
      "Percent keys are plain percent numbers (25 means 25 %), not fractions.")
    a("")
    a("| Key | Value | Meaning | How it is used |")
    a("|---|---|---|---|")
    a("| `slow_mover_daily_units` | %s | A SKU selling fewer units per day than this is a slow mover. | `SLOW_MOVER_LARGE_LOT` needs `avg_7d < slow_mover_daily_units`. `avg_7d` is the SKU's mean daily units over the last 7 days. |" % P["slow_mover_daily_units"])
    a("| `large_lot_days_of_cover` | %s | A lot covering more days of sales than this is a large lot. | `SLOW_MOVER_LARGE_LOT` also needs `qty_units / avg_7d > large_lot_days_of_cover`. |" % P["large_lot_days_of_cover"])
    a("| `weekend_drop_factor` | %s | Weekday factor below which a weekend day counts as a drop. | `SHORT_SHELF_LIFE` fires for COLD lots when both the Saturday and the Sunday factor of the category are below this value. The factor is the category's mean units on that weekday divided by its mean over all 30 days. |" % P["weekend_drop_factor"])
    a("| `stopped_ordering_days` | %s | Days without an order after which a regular dealer counts as stopped. | `DEALER_STOPPED_ORDERING` fires when a dealer with a regular 30-day share has `days_since_last_order >= stopped_ordering_days`. |" % P["stopped_ordering_days"])
    a("| `strict_dealer_share_pct` | %s | Share (percent of 30-day units) above which a SKU depends on strict CHAIN dealers. | `STRICT_DEALER_ONLY` fires when the CHAIN dealers' combined 30-day share is above this value. |" % P["strict_dealer_share_pct"])
    a("| `demand_drop_trend_pct` | %s | Size of the 7-day demand fall (percent) that counts as a drop. | `DEMAND_DROP_TREND` fires when `trend_pct <= -demand_drop_trend_pct`, with `trend_pct = (avg_last_7d / avg_prev_21d - 1) * 100`. |" % P["demand_drop_trend_pct"])
    a("")
    a("Other keys in the file (existing contract, values chosen by the generator):")
    a("")
    a("| Key | Value | Use |")
    a("|---|---|---|")
    a("| `elasticity` | COLD %s, DRY %s | Demand uplift = elasticity x discount fraction. |" % (P["elasticity"]["COLD"], P["elasticity"]["DRY"]))
    a("| `max_discount_pct_by_role` | `ticari`: DEALER_OFFER %s, CAMPAIGN %s | Discount limits in percent. `depo` has no discount action. Same shape as the default in `config.py`. |" % (P["max_discount_pct_by_role"]["ticari"]["DEALER_OFFER"], P["max_discount_pct_by_role"]["ticari"]["CAMPAIGN"]))
    a("| `donation_min_days_to_expiry` | %s | DONATION is feasible only with at least this many days left. Also used by `UNSAVEABLE`. |" % P["donation_min_days_to_expiry"])
    a("| `supplier_return_min_days_to_expiry` | %s | SUPPLIER_RETURN needs at least this many days left. Also used by `UNSAVEABLE`. |" % P["supplier_return_min_days_to_expiry"])
    a("| `supplier_return_credit_pct` | %s | **Fraction** (0.6 = 60 %%) of unit cost recovered on a return. The name says pct but the value is a fraction, as in `units x unit_cost x credit_pct`. |" % P["supplier_return_credit_pct"])
    a("| `forecast_low_confidence_wape` | %s | WAPE above this is LOW confidence; above half of it is MEDIUM. |" % P["forecast_low_confidence_wape"])
    a("| `risk_level_thresholds_try` | `medium_min` %s, `high_min` %s | LOW below 2,000 TRY, MEDIUM up to 10,000, HIGH from 10,000 (on `loss_try.expected`). Key names are this generator's choice; the schema owner (B) may rename them. |" % (P["risk_level_thresholds_try"]["medium_min"], P["risk_level_thresholds_try"]["high_min"]))
    a("")
    a("Why these values: `donation_min_days_to_expiry` is 1 and `supplier_return_min_days_to_expiry` is 4 so that a lot "
      "that no dealer accepts any more (below the 3-22 day acceptance minimums) can still be donated or returned. "
      "That is what makes the `UNSAVEABLE` scenario meaningful. `stopped_ordering_days` (7) is below the 9-10 days of "
      "silence in the scenario and above the 5 days any active dealer stays silent. `weekend_drop_factor` (0.85) sits between "
      "the COLD weekend factors (Sat %.2f, Sun %.2f) and the DRY ones (Sat %.2f, Sun %.2f)." % (fc[5], fc[6], fd[5], fd[6]))
    a("")
    a("## 2. Scenarios and ground truth")
    a("")
    a("`scenarios/scenarios.csv` (columns `sku_id, lot_id, scenario, expected_reason_code`) is test-only and must never be synced "
      "to the agent package. The `CONTROL` and `LOW_CONFIDENCE` rows have an empty `expected_reason_code`: skip empty values when "
      "asserting reason codes. Extra reason codes beyond the expected one are allowed (see the last column).")
    a("")
    a("| SKU | Lot | Scenario | Expected code | Qty | Days left | Expected loss (TRY) | Level | WAPE / confidence | All codes (reference model) |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for l, rk, codes in risk_rows:
        t = scn_by_lot.get(l["lot_id"])
        if not t or rk["at_risk"]["expected"] <= 0:
            continue
        a("| %s | %s | %s | %s | %d | %d | %s | %s | %.2f / %s | %s |" % (
            l["sku"], l["lot_id"], t[2], t[3] or "-", l["qty_units"], (l["expiry"] - AS_OF).days,
            f"{rk['loss']['expected']:,.0f}", risk_level(rk["loss"]["expected"]), model.wape(l["sku"]),
            confidence(model.wape(l["sku"])), ", ".join(codes) or "-"))
    ctrl = [t for t in truth if t[2] == "CONTROL"][0]
    cl = [l for l in stock if l["lot_id"] == ctrl[1]][0]
    crk = model.risk(cl)
    a("| %s | %s | CONTROL | - | %d | %d | 0 (not listed) | - | %.2f / %s | at-risk (worst case, low demand band) %d units |" % (
        ctrl[0], ctrl[1], cl["qty_units"], (cl["expiry"] - AS_OF).days, model.wape(ctrl[0]),
        confidence(model.wape(ctrl[0])), crk["at_risk"]["high"]))
    a("")
    a("Reference model numbers come from the design in `design.md` (4-week same-weekday forecast, eligibility rule, last-7-day lot mix). "
      "If `fefo_core` rounds or windows slightly differently, the scenario lots keep their expected codes because each rule has a wide margin; "
      "the control lot stays 15 % below expected demand.")
    a("")
    a("### Loss waterfall check (reference model, expected loss in TRY)")
    a("")
    a("Steps: FEFO_PRIORITY, then DEALER_OFFER 10 %, then CAMPAIGN 15 % (gross loss, action cost not included).")
    a("")
    a("| Lot | Baseline | After FEFO | After DEALER_OFFER 10% | After CAMPAIGN 15% | Share of loss removed |")
    a("|---|---|---|---|---|---|")
    for l, rk, codes in risk_rows[:6]:
        w = simulate(model, l, wf_steps)
        a("| %s | %s | %s | %s | %s | %.0f%% |" % (l["lot_id"], *[f"{v:,.0f}" for _, v in w],
                                                     100 * (1 - w[-1][1] / w[0][1]) if w[0][1] else 0))
    a("")
    a("## 3. Other assumptions in the synthetic data")
    a("")
    items = [
        "**Time frame.** `as_of_date` is 2026-11-25 (a Wednesday). History is 30 days, 2026-10-26 to 2026-11-24. `calendar.csv` has the same 30 days.",
        "**Size.** 40 products (12 COLD, 28 DRY, not 100 as the plan's reference size), 10 dealers (4 CHAIN, 6 TRADITIONAL), %d shipment rows, %d in-stock lots, %d inbound rows. The plan's 150-250 inventory rows assume 100 SKUs." % (len(ships), len(stock), len(INBOUND_NORMAL) + len(INBOUND_SCENARIO)),
        "**Lots.** Almost every SKU has one lot in stock (1 to 2 lots for SKU-001 and SKU-013). Lots that are no longer in stock appear only in `shipments.csv` (`stokta ya da geçmişte var olan lot`). They are not in `inventory_snapshot.csv`, so a validator can check eligibility only for lots in the snapshot. Every such historical lot expired before the as-of date.",
        "**Lot ids.** `LOT-<sku_id>-<n>`, numbered by received date, historical lots first. Inbound lots continue the numbering.",
        "**Stock consistency.** Lot stock is never negative: the generator treats a lot's initial stock as `qty_units` now plus everything shipped from it. The snapshot has no initial quantity, so a validator cannot check this rule beyond `received_date <= shipment date` and the eligibility rule.",
        "**Shipments.** Every shipment row takes one lot (oldest eligible lot first, FEFO). Every row satisfies `(expiry_date - date) >= min_days_on_receipt` and `date >= received_date`. No row exists for days without a shipment. No duplicate (date, dealer, SKU, lot) rows.",
        "**Demand model.** Daily units per (SKU, dealer) = SKU base units x dealer weight x weekday factor x random factor. Dealer weights are the same for all SKUs except for the scenarios below, with the random factor in 0.75-1.25 and a 92 % chance that a dealer orders on a given day. The generator re-draws a SKU's series (deterministic attempt index) until WAPE and trend fit the scenario, so normal SKUs have WAPE of at most 0.30 and trend within 15 %.",
        "**Weekday factors.** COLD Mon-Sun %s; DRY %s. Measured on the generated category totals: COLD Sat %.2f / Sun %.2f, DRY Sat %.2f / Sun %.2f." % (WDF["COLD"], WDF["DRY"], fc[5], fc[6], fd[5], fd[6]),
        "**SHORT_SHELF_LIFE is category-wide.** The design rule uses the category's weekday factor, so every risky COLD lot carries this code, not only the one in the scenario.",
        "**Dealer rules.** COLD: CHAIN pull 4-5 / min 6-7 days, TRADITIONAL pull 1-2 / min 3-4. DRY: CHAIN pull 30-35 / min 45-50, TRADITIONAL pull 10-12 / min 20-22. Rule `min_days_on_receipt >= shelf_pull_days + 2` holds for all rows.",
        "**Prices.** `unit_price_try = unit_cost_try x margin` (1.20-1.50), rounded to 2 decimals. Names are generic Turkish product names, no brands. `supplier_return_allowed` is false for 6 of the 12 COLD products (fresh dairy and juice).",
        "**Regular dealer.** `DEALER_STOPPED_ORDERING` needs a \"regular 30-day share\" that the design does not define. The scenario dealer (BAYI-05 on SKU-004) has a 30-day share of about 11 %. Every other ordering dealer of every SKU has an order in the last 4 days, so any definition of regular gives the same answer.",
        "**Scenario SKUs.** FIFO_VIOLATION SKU-001 (older lot LOT-SKU-001-3 in bin C-14-4, all shipments of the last 7 days from the fresher LOT-SKU-001-4), SHORT_SHELF_LIFE SKU-002, STRICT_DEALER_ONLY SKU-003 (CHAIN 80 % of units), DEALER_STOPPED_ORDERING SKU-004 (BAYI-05 silent since 2026-11-15), INBOUND_FRESH_LOT SKU-005 (fresh lot arriving 2026-11-28), DEMAND_DROP_TREND SKU-006 (last 7 days at 70 % of normal), UNSAVEABLE SKU-013 (old lot with 15 days left, below every dealer's DRY minimum; a newer lot LOT-SKU-013-2 serves the dealers), SLOW_MOVER_LARGE_LOT SKU-014 (about 7 units a day, 60 days left).",
        "**Control SKU.** SKU-008 holds 85 % of its expected sellable demand, so it is close to risky but its expected at-risk units are 0.",
        "**Low-confidence SKU.** SKU-007 has random day-to-day demand (0.2x to 2.5x) and an 85 % order chance. Its WAPE is above `forecast_low_confidence_wape`. It is also a small risky lot (LOW level) so it appears in `get_expiry_risks` with `forecast_confidence = LOW`. No other SKU has WAPE above the threshold.",
        "**Everything else is risk free.** The 30 other SKUs hold at most 45 % of their low-band window demand (COLD) or 10-24 days of cover with 90+ days left (DRY), so their expected at-risk units are 0 in the reference model.",
        "**Loss spread.** Risky lots span LOW to HIGH (see the table above), sized so that FEFO_PRIORITY, DEALER_OFFER and CAMPAIGN each remove a visible part of the loss. At-risk units are 35-60 % of the lot's expected demand; UNSAVEABLE has no sellable window at all.",
        "**Calendar.** Campaign days: 2026-11-09 (SKU-020) and 2026-11-16 (SKU-020, SKU-032), demand x1.5. Stock-outs (no shipments for the SKU that day): SKU-025 on 2026-11-13, SKU-031 on 2026-11-20. These touch only normal DRY SKUs.",
        "**Inbound.** One inbound row per SKU for 9 SKUs. Only SKU-005 has an inbound lot that is fresher than the risky lot inside its sellable window. Inbound rows of the other SKUs belong to risk-free SKUs.",
        "**Policy documents.** `policy/policy.md` and `policy/process_guide.md` are short placeholders with the POL/PRC numbers the stub uses (POL-1.1, 2.1, 2.2, 3.1, 3.2). L should replace them with the real text; keep the numbers equal to `params.json`.",
        "**Files not generated.** `contacts.csv` (Plan 2) is not generated. Nothing is written to the repo-level `data/` directory.",
    ]
    for it in items:
        a("- " + it)
    a("")
    a("## 4. Checks run by the generator on every run")
    a("")
    a("The generator reads its own CSV output back and fails (non-zero exit) if any of these break: reference IDs exist; "
      "`min_days_on_receipt >= shelf_pull_days + 2`; price above cost; shelf life in range; `expiry_date = received_date + shelf_life_days`; "
      "no negative or zero quantities; every shipment is in the 30-day window, has a valid dealer and SKU, falls on no stock-out day, "
      "and (for lots in the snapshot) is eligible for the dealer; each Scenario_SKU lot has its expected reason code in the reference model; "
      "the control SKU and all non-scenario SKUs have no at-risk units; the low-confidence SKU is the only SKU with LOW confidence; "
      "the weekday factors are on the right side of `weekend_drop_factor`.")
    a("")
    (OUT / "DATA_ASSUMPTIONS.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
