"""Rapor üretimi: DAILY_RISK ve LOT_ACTION_PLAN PDF'i (fpdf2) + S3 yükleme.

tools.py yalnızca `generate_report_file(...)` çağırır. PDF üretimi (`build_daily_risk_pdf`,
`build_lot_action_plan_pdf`, saf, bytes döner) S3 yüklemesinden (`upload_report`) ayrıdır.
RISK_TABLE ve xlsx görev 8.3'e kadar NOT_IMPLEMENTED döner. print yok, loglar stderr'e.
"""
import logging
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from config import get_region, get_reports_bucket
from fefo_core.pipeline import Snapshot
from fefo_core.simulate import simulate

logger = logging.getLogger("fefo_mcp.report")

EXPIRES_IN_SEC = 3600
DEFAULT_TOP_N = 10
DEFAULT_ACTIONS = [
    {"type": "FEFO_PRIORITY"},
    {"type": "DEALER_OFFER", "params": {"discount_pct": 10}},
    {"type": "CAMPAIGN", "params": {"discount_pct": 15}},
]
REPORT_TYPES = ("DAILY_RISK", "LOT_ACTION_PLAN", "RISK_TABLE")
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FONT_FILE, FONT_BOLD_FILE = "DejaVuSans.ttf", "DejaVuSans-Bold.ttf"
REQUIRED_GLYPHS = "şğıİçöü₺"
FONT_FAMILY = "DejaVu"


def _err(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


# --- font -------------------------------------------------------------------------------

def _covers_glyphs(path: Path) -> bool:
    try:
        from fontTools.ttLib import TTFont  # fpdf2 bağımlılığı
        cmap = TTFont(str(path), lazy=True).getBestCmap()
        return all(ord(ch) in cmap for ch in REQUIRED_GLYPHS)
    except Exception:
        return False


def _system_font(bold: bool) -> Path | None:
    """Yalnızca geliştirme ortamı: fc-list ile DejaVu Sans ara (fc-list yoksa None)."""
    try:
        out = subprocess.run(["fc-list", ":family=DejaVu Sans", "file", "style"],
                             capture_output=True, text=True, timeout=10, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    wanted = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for line in out.splitlines():
        path = Path(line.split(":", 1)[0].strip())
        if path.name == wanted and path.is_file() and _covers_glyphs(path):
            return path
    return None


def resolve_font(bold: bool = False) -> Path:
    """Önce paketlenmiş asset, yoksa fc-list (dev). Hiçbiri yoksa FileNotFoundError."""
    bundled = ASSETS_DIR / (FONT_BOLD_FILE if bold else FONT_FILE)
    if bundled.is_file():
        return bundled
    found = _system_font(bold)
    if found is None:
        raise FileNotFoundError(f"{bundled.name} bulunamadı (assets/ ve fc-list)")
    return found


# --- PDF yardımcıları ----------------------------------------------------------------------

def _try(value: float) -> str:
    """12.345,67 ₺ (Türkçe biçim)."""
    s = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} ₺"


def _int(value: int | float) -> str:
    return f"{int(round(value)):,}".replace(",", ".")


def _new_pdf():
    from fpdf import FPDF
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_font(FONT_FAMILY, "", str(resolve_font()))
    pdf.add_font(FONT_FAMILY, "B", str(resolve_font(bold=True)))
    pdf.set_auto_page_break(True, margin=12)
    pdf.add_page()
    return pdf


def _heading(pdf, text: str, size: int = 12) -> None:
    pdf.ln(3)
    pdf.set_font(FONT_FAMILY, "B", size)
    pdf.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT_FAMILY, "", 9)


def _line(pdf, text: str) -> None:
    pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")


def _table(pdf, headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    pdf.set_font(FONT_FAMILY, "", 8)
    with pdf.table(col_widths=widths, text_align="LEFT", line_height=5,
                   headings_style=_heading_style()) as table:
        head = table.row()
        for h in headers:
            head.cell(h)
        for r in rows:
            row = table.row()
            for c in r:
                row.cell(str(c))
    pdf.set_font(FONT_FAMILY, "", 9)


def _heading_style():
    from fpdf.fonts import FontFace
    return FontFace(family=FONT_FAMILY, emphasis="BOLD", fill_color=(230, 230, 230))


def _finish(pdf) -> bytes:
    return bytes(pdf.output())


def _footer_note(pdf) -> None:
    pdf.ln(4)
    pdf.set_font(FONT_FAMILY, "", 8)
    _line(pdf, "Açıklama: Beklenen kayıp, talep tahminine göre satılamayacak adetlerin "
               "birim fiyatla çarpımıdır. Rapor FEFO ajanı tarafından oluşturuldu.")


def _yorum(pdf, summary_text: str | None) -> None:
    if summary_text and summary_text.strip():
        _heading(pdf, "Yorum")
        _line(pdf, summary_text.strip())


# --- DAILY_RISK ----------------------------------------------------------------------------

def build_daily_risk_pdf(snapshot: Snapshot, summary_text: str | None = None,
                         top_n: int = DEFAULT_TOP_N) -> bytes:
    day = snapshot.as_of_date.isoformat()
    items = [i for i in snapshot.risk_items if i["at_risk_units"]["expected"] > 0]
    items.sort(key=lambda i: (-i["loss_try"]["expected"], i["lot_id"]))
    total = sum(i["loss_try"]["expected"] for i in items)

    pdf = _new_pdf()
    pdf.set_font(FONT_FAMILY, "B", 16)
    pdf.cell(0, 9, f"FEFO Günlük Risk Raporu - {day}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT_FAMILY, "", 10)
    pdf.cell(0, 6, f"Toplam beklenen kayıp: {_try(total)}   |   Riskli lot sayısı: {len(items)}",
             new_x="LMARGIN", new_y="NEXT")

    _heading(pdf, f"İlk {min(top_n, len(items))} Riskli Lot")
    rows = [[i["sku_id"], i["lot_id"], _int(i["qty_units"]), i["days_to_expiry"],
             _try(i["loss_try"]["expected"]), i["risk_level"], ", ".join(i["reason_codes"])]
            for i in items[:top_n]]
    _table(pdf, ["SKU", "Lot", "Adet", "SKT'ye gün", "Beklenen kayıp", "Risk düzeyi",
                 "Neden kodları"], rows, [24, 38, 20, 22, 34, 24, 115])

    levels: dict[str, int] = {}
    codes: dict[str, int] = {}
    for i in items:
        levels[i["risk_level"]] = levels.get(i["risk_level"], 0) + 1
        for c in i["reason_codes"]:
            codes[c] = codes.get(c, 0) + 1
    _heading(pdf, "Risk Düzeyi Dağılımı")
    _line(pdf, "   ".join(f"{k}: {v}" for k, v in sorted(levels.items())) or "Riskli lot yok")
    _heading(pdf, "Neden Kodu Dağılımı")
    _line(pdf, "   ".join(f"{k}: {v}" for k, v in sorted(codes.items(), key=lambda kv: (-kv[1], kv[0])))
          or "Neden kodu yok")

    _heading(pdf, "Bekleyen Kararlar")
    _line(pdf, "Bekleyen karar yok")  # fefo_mcp karar saklamaz (taslaklar durumsuz)
    _yorum(pdf, summary_text)
    _footer_note(pdf)
    return _finish(pdf)


# --- LOT_ACTION_PLAN -------------------------------------------------------------------------

def build_lot_action_plan_pdf(snapshot: Snapshot, lot_id: str,
                              summary_text: str | None = None) -> bytes:
    """lot_id bilinmiyorsa KeyError. Simülasyon hatası ValueError(kod: mesaj)."""
    item = snapshot.lot(lot_id)
    if item is None:
        raise KeyError(lot_id)
    sim = simulate(snapshot, lot_id, DEFAULT_ACTIONS)
    if "error" in sim:
        raise ValueError(f"{sim['error']['code']}: {sim['error']['message']}")
    day = snapshot.as_of_date.isoformat()

    pdf = _new_pdf()
    pdf.set_font(FONT_FAMILY, "B", 16)
    pdf.cell(0, 9, f"FEFO Aksiyon Planı - {lot_id} - {day}", new_x="LMARGIN", new_y="NEXT")
    _heading(pdf, "Lot Bilgileri")
    _line(pdf, f"Ürün: {item['sku_id']} {item['sku_name']} ({item['category']})\n"
               f"Lot: {lot_id}   Adet: {_int(item['qty_units'])}   Raf: {item['location_bin']}\n"
               f"Son kullanma tarihi: {item['expiry_date']} ({item['days_to_expiry']} gün kaldı)")

    _heading(pdf, "Risk Rakamları")
    ar, ls = item["at_risk_units"], item["loss_try"]
    _table(pdf, ["Senaryo", "Riskli adet", "Kayıp"],
           [[k, _int(ar[k]), _try(ls[k])] for k in ("low", "expected", "high")], [40, 40, 60])
    _line(pdf, f"Risk düzeyi: {item['risk_level']}   Tahmin güveni: {item['forecast_confidence']}")
    _line(pdf, "Neden kodları: " + (", ".join(item["reason_codes"]) or "yok"))

    _heading(pdf, "Aksiyon Simülasyonu")
    _line(pdf, f"Başlangıç kaybı: {_try(sim['baseline_loss_try'])}")
    rows = []
    for s in sim["steps"]:
        pct = (s.get("params") or {}).get("discount_pct")
        name = f"{s['action']}" + (f" %{pct}" if pct is not None else "")
        rows.append([name, "Evet" if s["feasible"] else "Hayır: " + s.get("infeasible_reason", ""),
                     _int(s["units_saved"]), _try(s["loss_after_try"]),
                     _try(s["action_cost_try"]), _try(s["net_benefit_try"]),
                     f"{s['kg_saved']:.2f}"])
    _table(pdf, ["Aksiyon", "Uygulanabilir", "Kurtarılan adet", "Sonraki kayıp", "Aksiyon maliyeti",
                 "Net fayda", "Kurtarılan kg"], rows, [38, 70, 28, 36, 36, 36, 30])
    _line(pdf, f"Nihai kayıp: {_try(sim['final_loss_try'])}   "
               f"Toplam net fayda: {_try(sim['total_net_benefit_try'])}")
    _yorum(pdf, summary_text)
    _footer_note(pdf)
    return _finish(pdf)


# --- S3 ----------------------------------------------------------------------------------------

def upload_report(pdf_bytes: bytes, as_of_date: str, file_id: str, bucket: str | None = None,
                  content_type: str = "application/pdf", ext: str = "pdf") -> dict[str, Any]:
    """S3'e yükler, presigned GET URL döner. Hata: {"error": {...}} (download_url yok)."""
    bucket = bucket or get_reports_bucket()
    if not bucket:
        return _err("S3_NOT_CONFIGURED", "REPORTS_BUCKET tanımlı değil")
    key = f"reports/{as_of_date}/{file_id}.{ext}"
    try:
        import boto3  # tembel import: cold start
        s3 = boto3.client("s3", region_name=get_region())
        s3.put_object(Bucket=bucket, Key=key, Body=pdf_bytes, ContentType=content_type)
        url = s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key},
                                        ExpiresIn=EXPIRES_IN_SEC)
    except Exception as exc:
        logger.error("S3 yükleme hatası: %s", type(exc).__name__)
        return _err("S3_UPLOAD_FAILED", f"Rapor yüklenemedi ({type(exc).__name__})")
    return {"s3_key": key, "download_url": url, "expires_in_sec": EXPIRES_IN_SEC}


# --- tool giriş noktası ------------------------------------------------------------------------

def generate_report_file(report_type: str, format: str, lot_id: str | None,
                         decision_id: str | None, summary_text: str | None,
                         snapshot: Snapshot) -> dict:
    if report_type not in REPORT_TYPES:
        return _err("INVALID_ARGUMENT", "report_type geçersiz")
    if format not in ("pdf", "xlsx"):
        return _err("INVALID_ARGUMENT", "format pdf veya xlsx olmalı")
    if report_type == "LOT_ACTION_PLAN" and not lot_id:
        return _err("INVALID_ARGUMENT", "LOT_ACTION_PLAN için lot_id gerekli")
    if report_type == "LOT_ACTION_PLAN" and snapshot.lot(lot_id) is None:
        return _err("LOT_NOT_FOUND", f"{lot_id} bulunamadı")
    if report_type == "RISK_TABLE" or format == "xlsx":
        return _err("NOT_IMPLEMENTED", "Şimdilik yalnızca DAILY_RISK ve LOT_ACTION_PLAN için pdf desteklenir")

    day = snapshot.as_of_date.isoformat()
    try:
        if report_type == "DAILY_RISK":
            data = build_daily_risk_pdf(snapshot, summary_text)
            file_name = f"FEFO_Gunluk_Risk_{day}.pdf"
        else:
            data = build_lot_action_plan_pdf(snapshot, lot_id, summary_text)
            file_name = f"FEFO_Aksiyon_Plani_{lot_id}_{day}.pdf"
    except Exception as exc:
        logger.error("PDF üretilemedi: %s", type(exc).__name__)
        return _err("REPORT_FAILED", f"PDF üretilemedi ({type(exc).__name__})")

    file_id = uuid.uuid4().hex[:12]
    up = upload_report(data, day, file_id)
    if "error" in up:
        return up
    return {"file_id": file_id, "file_name": file_name, "format": "pdf", "s3_key": up["s3_key"],
            "download_url": up["download_url"], "expires_in_sec": up["expires_in_sec"],
            "size_bytes": len(data)}
