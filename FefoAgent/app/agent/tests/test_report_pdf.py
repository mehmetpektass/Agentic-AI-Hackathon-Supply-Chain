"""PDF rapor testleri (S3 yok / mock'lu boto3)."""
import io
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pypdf import PdfReader

from config import DEFAULT_AS_OF_DATE
from fefo_core.pipeline import load_snapshot
from fefo_mcp import report

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def snap():
    return load_snapshot(DATA_DIR, DEFAULT_AS_OF_DATE)


def _text(pdf_bytes: bytes) -> str:
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf_bytes)).pages)


def test_daily_risk_pdf_turkish_glyphs(snap, tmp_path):
    data = report.build_daily_risk_pdf(snap, summary_text="Şeker ğ ı İ ç ö ü ₺ yorumu")
    assert data.startswith(b"%PDF")
    out = tmp_path / "r.pdf"
    out.write_bytes(data)
    text = _text(out.read_bytes())
    for ch in "şğıİçöü₺":
        assert ch in text, ch
    assert "Yorum" in text and "Bekleyen karar yok" in text
    assert snap.as_of_date.isoformat() in text
    top = next(i for i in snap.risk_items if i["at_risk_units"]["expected"] > 0)
    assert top["lot_id"] in text


def test_daily_risk_without_summary_has_no_yorum(snap):
    assert "Yorum" not in _text(report.build_daily_risk_pdf(snap))


def test_lot_action_plan_pdf(snap):
    lot = snap.risk_items[0]["lot_id"]
    text = _text(report.build_lot_action_plan_pdf(snap, lot))
    assert lot in text and "FEFO_PRIORITY" in text and "CAMPAIGN" in text


def test_lot_action_plan_requires_lot_id(snap):
    err = report.generate_report_file("LOT_ACTION_PLAN", "pdf", None, None, None, snap)
    assert err["error"]["code"] == "INVALID_ARGUMENT"


def test_lot_action_plan_unknown_lot(snap):
    err = report.generate_report_file("LOT_ACTION_PLAN", "pdf", "LOT-YOK", None, None, snap)
    assert err["error"]["code"] == "LOT_NOT_FOUND"


def test_not_implemented_for_xlsx_and_risk_table(snap):
    assert report.generate_report_file("RISK_TABLE", "xlsx", None, None, None,
                                       snap)["error"]["code"] == "NOT_IMPLEMENTED"
    assert report.generate_report_file("DAILY_RISK", "xlsx", None, None, None,
                                       snap)["error"]["code"] == "NOT_IMPLEMENTED"


def test_missing_bucket(snap, monkeypatch):
    monkeypatch.delenv("REPORTS_BUCKET", raising=False)
    err = report.generate_report_file("DAILY_RISK", "pdf", None, None, None, snap)
    assert "error" in err and "download_url" not in err


def test_upload_success(snap, monkeypatch):
    monkeypatch.setenv("REPORTS_BUCKET", "test-bucket")
    client = MagicMock()
    client.generate_presigned_url.return_value = "https://signed.example/x"
    boto3 = pytest.importorskip("boto3")
    monkeypatch.setattr(boto3, "client", lambda *a, **k: client)
    res = report.generate_report_file("DAILY_RISK", "pdf", None, None, None, snap)
    day = snap.as_of_date.isoformat()
    assert res["s3_key"] == f"reports/{day}/{res['file_id']}.pdf"
    assert res["file_name"] == f"FEFO_Gunluk_Risk_{day}.pdf"
    assert res["download_url"] == "https://signed.example/x"
    assert res["expires_in_sec"] == 3600 and res["size_bytes"] > 0 and res["format"] == "pdf"
    put = client.put_object.call_args.kwargs
    assert put["Bucket"] == "test-bucket" and put["Key"] == res["s3_key"]
    assert put["ContentType"] == "application/pdf" and put["Body"].startswith(b"%PDF")
    assert client.generate_presigned_url.call_args.kwargs["ExpiresIn"] == 3600


def test_upload_failure_returns_error(snap, monkeypatch):
    monkeypatch.setenv("REPORTS_BUCKET", "test-bucket")
    client = MagicMock()
    client.put_object.side_effect = RuntimeError("boom")
    boto3 = pytest.importorskip("boto3")
    monkeypatch.setattr(boto3, "client", lambda *a, **k: client)
    err = report.generate_report_file("DAILY_RISK", "pdf", None, None, None, snap)
    assert "error" in err and "download_url" not in err
