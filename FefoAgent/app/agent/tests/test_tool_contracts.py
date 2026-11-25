"""Tool kontrat testleri (Stub_MCP varsayılan). Her tool çıktısı schemas.py ile doğrulanır."""
import csv
import os
import subprocess
import sys

import pytest

import schemas
from tests.conftest import APP_DIR

IS_STUB = os.environ.get("MCP_BACKEND", "stub") == "stub"
SCENARIOS_CSV = APP_DIR.parents[2] / "data-gen" / "out" / "scenarios" / "scenarios.csv"


def _lot_id(mcp_backend) -> str:
    """Stub: sabit fixture lotu. Diğer backend'ler: canlı sunucudaki en riskli lot."""
    if IS_STUB:
        return "LOT-SKU-012-1"
    return mcp_backend.call("get_expiry_risks", top_n=1)["items"][0]["lot_id"]


def _control_sku() -> str | None:
    if IS_STUB:
        return "SKU-077"
    if not SCENARIOS_CSV.exists():
        return None
    with open(SCENARIOS_CSV, newline="") as f:
        return next((r["sku_id"] for r in csv.DictReader(f) if r["scenario"] == "CONTROL"), None)


def test_get_expiry_risks_contract_and_order(mcp_backend):
    data = mcp_backend.call("get_expiry_risks")
    assert schemas.validate_expiry_risks(data) == []
    assert data["as_of_date"] == "2026-11-25"
    losses = [i["loss_try"]["expected"] for i in data["items"]]
    assert losses == sorted(losses, reverse=True)


def test_get_expiry_risks_filters(mcp_backend):
    data = mcp_backend.call("get_expiry_risks", category="COLD", min_loss_try=1000, top_n=2)
    assert schemas.validate_expiry_risks(data) == []
    assert len(data["items"]) <= 2
    assert all(i["category"] == "COLD" and i["loss_try"]["expected"] >= 1000
               for i in data["items"])


def test_get_sku_profile_contract_and_error(mcp_backend):
    assert schemas.validate_sku_profile(mcp_backend.call("get_sku_profile", sku_id="SKU-012")) == []
    assert schemas.is_tool_error(mcp_backend.call("get_sku_profile", sku_id="YOK"))


def test_simulate_actions_contract_and_order(mcp_backend):
    actions = [{"type": "FEFO_PRIORITY", "params": {}},
               {"type": "DEALER_OFFER", "params": {"discount_pct": 10}}]
    data = mcp_backend.call("simulate_actions", lot_id=_lot_id(mcp_backend), actions=actions)
    assert schemas.validate_simulation(data) == []
    assert [s["action"] for s in data["steps"]] == ["FEFO_PRIORITY", "DEALER_OFFER"]
    assert data["final_loss_try"] <= data["baseline_loss_try"]


def test_create_action_drafts_contract(mcp_backend):
    data = mcp_backend.call("create_action_drafts", lot_id=_lot_id(mcp_backend),
                            approved_actions=[{"type": "SUPPLIER_RETURN", "params": {}}],
                            approver_actor_id="depo-test")
    assert schemas.validate_drafts(data) == []


def test_generate_report_file_contract_and_error(mcp_backend):
    data = mcp_backend.call("generate_report_file", report_type="DAILY_RISK", format="pdf")
    assert schemas.validate_report(data) == []
    assert data["s3_key"] == f"reports/2026-11-25/{data['file_id']}.pdf"
    err = mcp_backend.call("generate_report_file", report_type="LOT_ACTION_PLAN", format="pdf")
    assert schemas.is_tool_error(err)


def test_stub_stdout_only_protocol():
    """stdout'a MCP dışı çıktı yazılmamalı: stdin kapanınca süreç temiz çıkmalı ve stdout boş olmalı."""
    proc = subprocess.run([sys.executable, "-m", "fefo_mcp_stub"], input="", capture_output=True,
                          text=True, cwd=APP_DIR, timeout=30,
                          env={"PYTHONPATH": str(APP_DIR), "PATH": "/usr/bin"})
    assert proc.stdout == ""


def test_reason_codes_enum_and_control_sku(mcp_backend):
    data = mcp_backend.call("get_expiry_risks")
    assert all(c in schemas.REASON_CODES for i in data["items"] for c in i["reason_codes"])
    control_sku = _control_sku()
    if control_sku is not None:
        control = next((i for i in data["items"] if i["sku_id"] == control_sku), None)
        if control is not None or IS_STUB:
            assert control["risk_level"] == "LOW" and control["reason_codes"] == []
    assert schemas.invalid_reason_codes(["YOK_KOD"]) != []
