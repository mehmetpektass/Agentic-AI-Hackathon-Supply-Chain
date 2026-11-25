"""Tests for fefo_core.pipeline (snapshot + sku profile)."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from fefo_core.pipeline import load_snapshot, sku_profile
from fefo_core.validate import ValidationError
from schemas import validate_sku_profile

APP_DIR = Path(__file__).resolve().parents[1]
FIXTURE = APP_DIR / "tests" / "fixtures" / "data"
GENERATED = APP_DIR / "data"


@pytest.fixture(scope="module")
def snap():
    return load_snapshot(GENERATED, "2026-11-25")


def test_generated_snapshot_top_lot(snap):
    assert snap.as_of_date == date(2026, 11, 25)
    assert snap.risk_items[0]["lot_id"] == "LOT-SKU-001-3"
    losses = [i["loss_try"]["expected"] for i in snap.risk_items]
    assert losses == sorted(losses, reverse=True)
    assert snap.lot("LOT-SKU-001-3")["sku_id"] == "SKU-001"
    assert any(i["lot_id"] == "LOT-SKU-001-3" for i in snap.lots_of_sku("SKU-001"))
    assert snap.lot("YOK") is None and snap.lots_of_sku("YOK") == []


def test_fixture_snapshot_loads():
    s = load_snapshot(FIXTURE, date(2026, 11, 26))
    assert len(s.risk_items) == len(s.by_lot) > 0
    assert s.params is s.tables.params


def test_validation_failure_raises(tmp_path):
    import shutil
    shutil.copytree(FIXTURE, tmp_path / "d")
    p = tmp_path / "d" / "raw" / "dealers.csv"
    lines = p.read_text(encoding="utf-8").splitlines()
    p.write_text("\n".join(lines + [lines[1]]) + "\n", encoding="utf-8")  # duplicate dealer
    with pytest.raises(ValidationError):
        load_snapshot(tmp_path / "d", date(2026, 11, 26))


def test_sku_profile_shape_and_unknown(snap):
    prof = sku_profile(snap, "SKU-001")
    assert validate_sku_profile(prof) == []
    assert prof["sku"]["sku_id"] == "SKU-001"
    assert "FIFO_VIOLATION" in prof["signals"]
    assert any(l["lot_id"] == "LOT-SKU-001-3" for l in prof["lots"])
    assert sum(d["share_pct"] for d in prof["dealers"]) == pytest.approx(100, abs=1)
    assert sku_profile(snap, "YOK") is None
