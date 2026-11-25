"""Scenario ground-truth test: fefo_mcp (stdio) vs data-gen/out/scenarios/scenarios.csv.

Per-scenario outcomes are written to tests/.scenario_results.json (generated file).
"""
import csv
import json
from pathlib import Path

import pytest

from .conftest import APP_DIR, McpHarness

SCENARIOS_CSV = APP_DIR.parents[2] / "data-gen" / "out" / "scenarios" / "scenarios.csv"
DATA_DIR = APP_DIR / "data"
RESULTS_PATH = Path(__file__).resolve().parent / ".scenario_results.json"
CONTROL_SKU, LOW_CONF_SKU, TOP_LOT = "SKU-008", "SKU-007", "LOT-SKU-001-3"

if not SCENARIOS_CSV.is_file():
    pytest.skip(f"scenario ground truth missing: {SCENARIOS_CSV}", allow_module_level=True)
if not DATA_DIR.is_dir():
    pytest.skip(f"agent data directory missing: {DATA_DIR}", allow_module_level=True)

ROWS = list(csv.DictReader(SCENARIOS_CSV.open(encoding="utf-8")))
RESULTS: dict[str, dict] = {}


@pytest.fixture(scope="module")
def fefo_harness() -> McpHarness:
    """Always the fefo_mcp backend, ignoring MCP_BACKEND."""
    return McpHarness("fefo_mcp")


@pytest.fixture(scope="module")
def risks(fefo_harness) -> dict:
    data = fefo_harness.call("get_expiry_risks", top_n=100000)
    assert "items" in data, f"get_expiry_risks failed: {data}"
    return data


def _record(key: str, passed: bool, detail: str) -> None:
    RESULTS[key] = {"passed": passed, "detail": detail}
    RESULTS_PATH.write_text(json.dumps(RESULTS, indent=2, ensure_ascii=False), encoding="utf-8")


def _checked(key: str, fn) -> None:
    try:
        detail = fn()
    except AssertionError as e:
        _record(key, False, str(e))
        raise
    _record(key, True, detail or "ok")


@pytest.mark.parametrize("row", [r for r in ROWS if r["expected_reason_code"]],
                         ids=lambda r: f'{r["sku_id"]}-{r["scenario"]}')
def test_expected_reason_code(risks, row):
    def check():
        item = next((i for i in risks["items"] if i["lot_id"] == row["lot_id"]), None)
        assert item is not None, f'{row["lot_id"]} not in get_expiry_risks items'
        assert row["expected_reason_code"] in item["reason_codes"], \
            f'{row["expected_reason_code"]} not in {item["reason_codes"]}'
        return f'reason_codes={item["reason_codes"]}'
    _checked(f'{row["sku_id"]}:{row["scenario"]}', check)


def test_control_sku_not_risky(risks):
    def check():
        hits = [i["lot_id"] for i in risks["items"] if i["sku_id"] == CONTROL_SKU]
        assert not hits, f"{CONTROL_SKU} appears in items: {hits}"
        return "absent from items"
    _checked(f"{CONTROL_SKU}:CONTROL", check)


def test_low_confidence_sku(risks, fefo_harness):
    def check():
        items = [i for i in risks["items"] if i["sku_id"] == LOW_CONF_SKU]
        assert items, f"{LOW_CONF_SKU} not in items"
        assert all(i["forecast_confidence"] == "LOW" for i in items), \
            [(i["lot_id"], i["forecast_confidence"]) for i in items]
        profile = fefo_harness.call("get_sku_profile", sku_id=LOW_CONF_SKU)
        for k in ("forecast_confidence", "confidence"):
            if k in profile:
                assert profile[k] == "LOW", f"profile {k}={profile[k]}"
        return f"item confidence LOW; profile keys={sorted(profile)}"
    _checked(f"{LOW_CONF_SKU}:LOW_CONFIDENCE", check)


def test_items_sorted_desc_and_top_item(risks):
    def check():
        losses = [i["loss_try"]["expected"] for i in risks["items"]]
        assert losses == sorted(losses, reverse=True), "items not sorted by loss_try.expected desc"
        assert risks["items"][0]["lot_id"] == TOP_LOT, \
            f'top item is {risks["items"][0]["lot_id"]}, expected {TOP_LOT}'
        return f"{len(losses)} items; top={TOP_LOT}"
    _checked("ordering:top_item", check)
