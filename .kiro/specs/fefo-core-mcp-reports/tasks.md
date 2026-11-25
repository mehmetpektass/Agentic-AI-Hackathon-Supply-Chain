# Implementation Plan: fefo-core-mcp-reports

## Overview

Vertical slice first: synthetic data, sync script, `fefo_core`, `fefo_mcp`, PDF report, deploy and verify (tasks 1 to 7). Refinement after the slice: full `simulate_actions` semantics and the `RISK_TABLE` xlsx (task 8, optional). Language: Python 3.12 (runtime 3.14), stdlib only in `fefo_core`, plain pytest. No git commit, no DynamoDB, no property-based tests. Paths below are relative to the repo root; agent code lives in `FefoAgent/app/agent/`.

## Tasks

- [x] 1. Synthetic data generator
  - [x] 1.1 Write `data-gen/generate.py` with a fixed seed, output only to `data-gen/out/{raw,config,policy}`
    - Files and columns per TEAM_PLAN section 3.1 to 3.8; 30 days, 10 dealers, about 40 products
    - At least 6 Scenario_SKUs (distinct scenarios of section 3.11), exactly 1 Control_SKU, exactly 1 Low_Confidence_SKU
    - Write the truth file to `data-gen/out/scenarios/scenarios.csv` (`expected_reason_code` per Scenario_SKU); nothing under `scenarios/` goes into raw/config/policy
    - Run it twice and confirm byte-identical output
    - STOP and ask the user before writing anything into `data/`; this task writes nothing there
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11_

- [x] 2. Sync script
  - [x] 2.1 Write `scripts/sync_data.sh` with `--from <dir>` (default `data/`)
    - Copy only `raw/`, `config/`, `policy/` to `FefoAgent/app/agent/data/`; never `scenarios/`; never modify the source
    - Missing source: warning on stderr, destination untouched. Bad option or `--from` without value: usage and non-zero exit
    - Print source, destination and file count
    - Run `scripts/sync_data.sh --from data-gen/out` to fill the agent data dir
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 2.2 Write the sync smoke test (`FefoAgent/app/agent/tests/test_sync_data.py`)
    - Temp source with `raw/ config/ policy/ scenarios/`, temp destination: three dirs copied, `scenarios/` not copied, source unchanged
    - Missing-source and bad-option exits
    - _Requirements: 2.3, 2.4, 2.5, 2.7_

- [x] 3. fefo_core pipeline
  - [x] 3.1 Implement `fefo_core/validate.py` and `tests/test_validate.py`
    - Section 3.12 rules; `ValidationIssue(file, row, rule)`, `ValidationError`; one known-bad row per rule in a small hand-built fixture (shared `tests/fixtures/` data, about 2 dealers, a few SKUs, about 35 days)
    - _Requirements: 3.1, 3.3, 3.4, 3.10_

  - [x] 3.2 Implement `fefo_core/features.py` and `tests/test_features.py`
    - Missing days as 0, 7d/30d dealer shares, per-category weekday factors, `trend_pct`, ordering dealers, FIFO violation flag
    - _Requirements: 3.1, 3.5, 3.10_

  - [x] 3.3 Implement `fefo_core/forecast.py` and `tests/test_forecast.py`
    - `WEEKDAY_AVG_4W`, low/expected/high, 7-day backtest WAPE, confidence from `forecast_low_confidence_wape`
    - _Requirements: 3.5, 3.6, 3.8, 3.10_

  - [x] 3.4 Implement `fefo_core/risk.py` and `tests/test_risk.py`
    - Eligibility `(expiry_date - d) >= min_days_on_receipt`, sellable window, at-risk units, `loss_try` low/expected/high, `risk_level`, the eight reason-code rules with thresholds from `params.json`
    - Test exact hand-computed values on the fixture
    - _Requirements: 3.1, 3.5, 3.7, 3.8, 3.10_

  - [x] 3.5 Implement `fefo_core/pipeline.py` (`Snapshot`, `load_snapshot`) and a minimal stub-shape `fefo_core/simulate.py`
    - Load, validate, features, forecast, risk; risk items sorted by `loss_try.expected` desc; `simulate` returns the stub-contract shape with proportional savings
    - Relative imports only inside `fefo_core`; paths from `__file__`
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.9, 4.9_

- [x] 4. fefo_mcp backend
  - [x] 4.1 Copy `fefo_mcp_stub/` to `fefo_mcp/` and replace fixture reads with `fefo_core` calls
    - Same tool names, parameters, enums, docstrings; `_SNAPSHOT = load_snapshot(...)` at import; errors returned as `{"error": {...}}`; stderr logging only; do not touch `fefo_mcp_stub/`
    - Startup validation failure: log to stderr and exit non-zero before `mcp.run()`
    - Import style: relative inside `fefo_mcp`, absolute `fefo_core` and `config`, no `sys.path` edits
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11_

  - [x] 4.2 Fix `config.PARAMS_PATH` to `data/config/params.json`
    - `role_hook` must read the synced file, not fall back to defaults
    - _Requirements: 3.8, 4.10_

  - [x] 4.3 Run the Contract_Tests with `MCP_BACKEND=fefo_mcp`
    - Fix failures in `fefo_mcp`, not in the tests; also confirm they still pass with `stub`
    - _Requirements: 10.1, 6.3_

  - [x] 4.4 Write the scenario test (`tests/test_scenarios.py`)
    - Truth from `data-gen/out/scenarios/scenarios.csv`: each Scenario_SKU's `reason_codes` contain its expected code; Control_SKU not in risky items; Low_Confidence_SKU `forecast_confidence == "LOW"`
    - _Requirements: 10.2, 10.3_

- [x] 5. PDF daily risk report
  - [x] 5.1 Add `fpdf2` and `openpyxl` to `[project].dependencies` in `FefoAgent/app/agent/pyproject.toml`
    - Runtime deps only; confirm ARM64 wheels (fpdf2 is pure Python); run `uv sync`
    - _Requirements: 6.4, 6.5_

  - [x] 5.2 Implement `fefo_mcp/report.py` `DAILY_RISK` PDF and wire it into `generate_report_file`
    - Font: `fc-list` search for ş ğ ı İ ç ö ü ₺, else bundled `fefo_mcp/assets/DejaVuSans.ttf` (copy a found TTF there; download only if none found)
    - Sections: total expected loss, top N lots, reason-code counts, pending decisions, separate "Yorum" for `summary_text`; all numbers from `Snapshot`
    - Name `FEFO_Gunluk_Risk_<as_of_date>.pdf`; upload to `reports/<as_of_date>/<file_id>.pdf`; presigned URL 3600 s; return `file_id, file_name, format, s3_key, download_url, expires_in_sec, size_bytes`
    - Missing `REPORTS_BUCKET` or S3 error: error dict, no `download_url`; `LOT_ACTION_PLAN` without `lot_id`: `INVALID_ARGUMENT`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12_

  - [x] 5.3 Generate a PDF locally, open it and verify Turkish characters (required)
    - Test `tests/test_report_pdf.py` (S3 mocked): extract text and assert ş ğ ı İ ç ö ü ₺ are present; also write the file to a temp path and open it to confirm
    - _Requirements: 5.2, 10.4_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Deploy and verify
  - [x] 7.1 Set `MCP_BACKEND` to `fefo_mcp` in `FefoAgent/agentcore/agentcore.json`
    - Keep `UNIFIED_TRACES_DESTINATION_ENABLED=true`, `REPORTS_BUCKET` and the `policies/s3-reports.json` entry in `additionalPolicies`
    - _Requirements: 7.1, 6.1, 6.3, 6.6_

  - [x] 7.2 Ask the user before deleting `fefo_mcp_stub/`
    - Delete only after explicit approval; otherwise leave it in place
    - _Requirements: 7.5_

  - [x] 7.3 Run `agentcore deploy` from `FefoAgent/`
    - On S3 `AccessDeniedException`, extend `policies/s3-reports.json` and redeploy; no manual IAM edits
    - _Requirements: 7.4_

  - [x] 7.4 Verify TEAM_PLAN section 9 (five Lab 7 checks)
    - `agentcore status`, invoke "Bugun riskli urunler neler? Bir aracini cagir ve sonucu goster." with `actorId` `depo-test`, log group and `traces runtime list --since 15m`, `.kiro/specs/` documents the agent, `traces runtime get <trace-id>` shows `fefo_mcp` spans
    - _Requirements: 7.2_

  - [x] 7.5 Invoke "Gunluk riskli urun raporunu PDF yap" on the deployed runtime
    - Answer contains a link that returns HTTP 200 and a body starting with `%PDF`
    - _Requirements: 7.3, 7.6_

- [ ] 8. Refinement after the slice (optional)
  - [ ]* 8.1 Implement full `simulate_actions` semantics (TEAM_PLAN 4.3) in `fefo_core/simulate.py`
    - Ordered steps, five action types, elasticity uplift, `action_cost_try`, `net_benefit_try`, `kg_saved`, `feasible`/`infeasible_reason`, `policy_refs`; output shape unchanged
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [ ]* 8.2 Write `tests/test_simulate.py`
    - Each of the five actions on one lot of the small fixture, plus an infeasible case
    - _Requirements: 8.2, 8.5, 8.6_

  - [ ]* 8.3 Add `RISK_TABLE` xlsx to `fefo_mcp/report.py` with `openpyxl`
    - Header row, one row per risky lot, integer formats, `'#,##0.00 "₺"'` loss columns, name `FEFO_Risk_Tablosu_<as_of_date>.xlsx`, same S3 key and presigned URL rules
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 8.4 Write `tests/test_report_xlsx.py`
    - Reopen the workbook (S3 mocked), compare values with `Snapshot.risk_items`
    - _Requirements: 9.1, 9.3_

## Notes

- Tasks marked with `*` are optional (refinement slice). Contract tests, the scenario test and the PDF Turkish check are required.
- Nothing is written into `data/` without explicit user approval; `fefo_mcp_stub/` is deleted only after approval.
- No git commit is created at any step.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "5.1"] },
    { "id": 1, "tasks": ["2.1", "3.1", "3.2"] },
    { "id": 2, "tasks": ["2.2", "3.3"] },
    { "id": 3, "tasks": ["3.4"] },
    { "id": 4, "tasks": ["3.5"] },
    { "id": 5, "tasks": ["4.1", "4.2"] },
    { "id": 6, "tasks": ["4.3", "4.4", "5.2"] },
    { "id": 7, "tasks": ["5.3"] },
    { "id": 8, "tasks": ["7.1"] },
    { "id": 9, "tasks": ["7.2"] },
    { "id": 10, "tasks": ["7.3"] },
    { "id": 11, "tasks": ["7.4"] },
    { "id": 12, "tasks": ["7.5"] },
    { "id": 13, "tasks": ["8.1", "8.3"] },
    { "id": 14, "tasks": ["8.2", "8.4"] }
  ]
}
```
