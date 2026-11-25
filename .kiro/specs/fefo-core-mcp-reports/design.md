# Design Document

## Overview

This feature replaces the stub MCP backend with a real pipeline, in two slices:

- **Vertical slice (must finish):** `data-gen/` produces synthetic CSVs, `scripts/sync_data.sh` copies them one way into the agent package, `fefo_core` (pure Python) validates, builds features, forecasts and scores risk, `fefo_mcp` (a copy of `fefo_mcp_stub` with fixture reads replaced by `fefo_core` calls) serves the same five tools over stdio, and `generate_report_file` produces a `DAILY_RISK` PDF uploaded to S3 with a presigned URL. In this slice `simulate_actions` only has to keep working for the stub-contract shape. The agent switches with `MCP_BACKEND=fefo_mcp`, is deployed, and the Lab 7 checks pass.
- **Refinement slice (after the vertical slice is green):** `simulate_actions` follows `TEAM_PLAN_FEFO_AGENT.md` section 4.3 exactly, and `generate_report_file` gains the `RISK_TABLE` xlsx report.

The tool contract (`schemas.py`, `fefo_mcp_stub/tools.py` signatures) is reused, so the agent, `mcp_adapter.py` and `role_hook.py` need no change beyond the existing `MCP_BACKEND` env var.

Constraints: Python 3.12 and 3.14 (the runtime in `agentcore.json` is `PYTHON_3_14`; local dev uses 3.12), no pandas (stdlib `csv`/`json`/`datetime` only), all logging to stderr, no `print` and nothing on stdout.

## Architecture

```
data-gen/                       (Dev-authored, never synced as a whole)
  generate.py                   fixed-seed generator
  out/
    raw/ config/ policy/        synced by scripts/sync_data.sh
    scenarios/scenarios.csv     Scenario_Truth_File, outside the agent package, never copied

scripts/sync_data.sh            one-way copy {data/ | data-gen/out} -> FefoAgent/app/agent/data/
                                (raw/ config/ policy/ only; scenarios/ excluded)

FefoAgent/app/agent/            (AgentCore codeLocation = zip root)
  data/                         synced copy: raw/ config/ policy/
  fefo_core/                    stdlib only
    validate.py  features.py  forecast.py  risk.py  simulate.py  pipeline.py
  fefo_mcp/                     copy of fefo_mcp_stub/
    __main__.py  tools.py  report.py  assets/DejaVuSans.ttf
  fefo_mcp_stub/                untouched until the user approves deletion
  mcp_adapter.py  main.py  parse.py  role_hook.py  config.py  schemas.py   unchanged
```

### Import style (how `fefo_mcp` is launched)

`mcp_adapter.module_name("fefo_mcp")` returns `"fefo_mcp"`. The adapter starts it as `[sys.executable, "-m", "fefo_mcp"]` with `env["PYTHONPATH"] = APP_DIR + os.pathsep + <existing>`, where `APP_DIR` is the directory containing `mcp_adapter.py`. It does not set `cwd`. The contract-test harness (`tests/conftest.py`) does the same and also sets `cwd=APP_DIR`. In the AgentCore CodeZip runtime `APP_DIR` is the zip root (`codeLocation: app/agent`), so `fefo_core`, `fefo_mcp`, `config` and `schemas` are all top-level packages in both cases.

The import style that works in all three places (local pytest, `agentcore dev`, deployed runtime):

- Inside `fefo_mcp`: relative imports for siblings, `from . import tools`, `from .report import generate_report_file`.
- From `fefo_mcp` to the core and shared modules: absolute top-level imports, `from fefo_core.pipeline import load_snapshot`, `import config`.
- Inside `fefo_core`: relative imports only, `from .validate import run`.
- No `sys.path` edits, no `from app.agent...`, no `from agent...`, no reliance on `cwd`.
- Data and font paths come from `Path(__file__).resolve().parent...`, never from `cwd`.

The adapter's `importlib.util.find_spec("fefo_mcp")` check runs in the agent process, where `main.py`'s directory is on `sys.path`. It does not check `fefo_core`, so a missing `fefo_core` would only show up as a subprocess startup failure (stderr message, non-zero exit). The contract tests with `MCP_BACKEND=fefo_mcp` catch that locally.

One existing inconsistency to fix when `fefo_mcp` lands: `config.PARAMS_PATH` points to `app/agent/data/params.json`, but the sync copies `params.json` to `app/agent/data/config/params.json`. `fefo_core` reads `data/config/params.json`; `config.PARAMS_PATH` (used by `role_hook` for `max_discount_pct_by_role`) must be changed to the same path, or it silently falls back to its built-in defaults.

### Startup data flow (per `fefo_mcp` subprocess)

```
load (CSV+JSON) -> validate -> features -> forecast -> risk -> Snapshot (in memory)
```

1. **Load:** `pipeline.load_snapshot(data_dir, as_of_date)` reads `products.csv`, `dealers.csv`, `dealer_rules.csv`, `shipments.csv`, `inventory_snapshot.csv`, `inbound_plan.csv` (optional), `calendar.csv` and `config/params.json`.
2. **Validate:** section 3.12 checks. Failures raise `ValidationError` with `(file, row, rule)` items. `fefo_mcp` logs them to stderr and exits non-zero before `mcp.run()`.
3. **Features, forecast, risk:** described below.
4. **Cache:** `tools.py` builds the `Snapshot` once at import time and every tool call reads from it.

## fefo_core

### features.py

- **Missing days:** per SKU, a daily series over the 30 history days (`as_of_date - 30` to `as_of_date - 1`); days without shipment rows are 0.
- **Dealer shares:** per SKU, each dealer's share of units over the last 7 days and the last 30 days. `share_pct` in `get_sku_profile` uses 30 days.
- **Weekday factor (per category):** for each category, mean units on a weekday divided by the mean over all days, computed on the category's daily totals. Exposed as `weekday_factors {Mon..Sun}`.
- **Trend:** `trend_pct = (avg_last_7d / avg_prev_21d - 1) * 100`; 0 when the previous 21 days are all 0.
- **Ordering dealers:** dealers with at least one shipment of the SKU in the last 30 days, with `last_order_date` and `days_since_last_order`.
- **FIFO violation:** true for a lot when an older-expiry lot of the same SKU is in stock and, in the last 7 days, shipments came from a fresher lot while the older lot was eligible for that dealer on that day.

### forecast.py (one method only)

- **Method:** for a day `d`, the forecast is the average of the same weekday over the last 4 weeks (the last 4 occurrences of `d`'s weekday in history). `forecast_method` is reported as `"WEEKDAY_AVG_4W"`.
- **Bands:** `low` = min and `high` = max of those 4 values; `expected` = their mean. For a window of several days, each band is summed over the days of the window.
- **Backtest and WAPE:** for each of the last 7 history days `t`, forecast `t` from the same weekday in the weeks before `t` (up to 4 values; with a 30-day history the earliest test days have 3). `wape = sum(|actual_t - forecast_t|) / sum(actual_t)` over the 7 days. If `sum(actual_t) = 0`, `wape = 0.0` when the forecasts are also 0, otherwise `1.0`.
- **Confidence:** `LOW` when `wape > params.forecast_low_confidence_wape`; `MEDIUM` when `wape > forecast_low_confidence_wape / 2`; otherwise `HIGH`.

### risk.py

- **Eligibility rule:** lot `L` can go to dealer `D` on day `d` iff `(expiry_date - d).days >= min_days_on_receipt(D, category)`.
- **Sellable window:** the days `d` from `as_of_date` up to the last day on which at least one dealer is eligible; `sellable_window_days` is that count, floored at 0 (it is at most `days_to_expiry - min over dealers of min_days_on_receipt`).
- **Demand for the lot:** per window day, `forecast(d) * eligible_dealer_share(d) * lot_mix_share`, where `lot_mix_share` is the lot's share of the SKU's units shipped in the last 7 days. The sum over the window gives `forecast_units_in_window {low, expected, high}`.
- **At-risk units:** `max(0, qty_units - forecast_units_in_window.<band>)`, rounded to integers, per band. Because `low` demand gives more at-risk units, the `low` demand band pairs with the `high` loss band; the output fields stay named by loss: `loss_try.low` uses the `high` demand band.
- **Loss:** `loss_try = at_risk_units * unit_price_try`, per band.
- **risk_level:** from `params.risk_level_thresholds_try` using `loss_try.expected`: below the LOW limit is `LOW`, up to the MEDIUM limit is `MEDIUM`, above is `HIGH` (example in the plan: 2,000 and 10,000).
- **forecast_confidence and wape:** from forecast.py.
- **Listed items:** lots with `at_risk_units.expected > 0`, sorted by `loss_try.expected` descending.
- **reason_codes (enum = `schemas.REASON_CODES`, same eight values as TEAM_PLAN 3.11):** each is a rule on features, with thresholds read from `params.json` (keys added to the schema by B, defaults documented in `DATA_ASSUMPTIONS.md`):

| Code | Rule |
|---|---|
| `FIFO_VIOLATION` | FIFO violation flag from features.py for this lot |
| `SLOW_MOVER_LARGE_LOT` | `avg_7d` is low (below `slow_mover_daily_units`) and `qty_units` covers more than `large_lot_days_of_cover` days of that demand |
| `SHORT_SHELF_LIFE` | category `COLD` and the weekday factor of Saturday and Sunday is below `weekend_drop_factor` |
| `DEALER_STOPPED_ORDERING` | a dealer with a regular 30-day share has `days_since_last_order >= stopped_ordering_days` |
| `STRICT_DEALER_ONLY` | CHAIN dealers hold more than `strict_dealer_share_pct` of the 30-day share |
| `DEMAND_DROP_TREND` | `trend_pct <= -demand_drop_trend_pct` |
| `INBOUND_FRESH_LOT` | `inbound_plan.csv` has a fresher lot of the SKU arriving within the lot's sellable window |
| `UNSAVEABLE` | `at_risk_units.low > 0` and `days_to_expiry` is below the smallest of `donation_min_days_to_expiry` and `supplier_return_min_days_to_expiry`, or no dealer is eligible in the remaining window |

### simulate.py (follows TEAM_PLAN 4.3)

Actions are applied in the given order; each step starts from the loss left by the previous step.

- **Baseline (no actions):** `expected` demand forecast, dealer shares and the eligibility rule, with the lot mix of the last 7 days. `baseline_loss_try = loss_try.expected` from risk.py.
- `FEFO_PRIORITY` (no params): the lot mix changes from "the last 7 days' mix continues" to "oldest eligible lot first", so this lot's share of eligible demand rises to 1 until it is used up.
- `DEALER_OFFER {dealer_ids?, discount_pct}`: without `dealer_ids`, pick the 2 eligible dealers with the highest `avg_daily_units`. Their demand rises by `elasticity * discount_pct / 100` (elasticity from `params.json` by category).
- `CAMPAIGN {discount_pct}`: the same uplift for all eligible dealers.
- `DONATION {units?}`: defaults to the remaining at-risk units. Feasible only if `days_to_expiry >= donation_min_days_to_expiry`. TRY loss is unchanged; `kg_saved = units * unit_weight_kg`.
- `SUPPLIER_RETURN {units?}`: feasible only if `supplier_return_allowed` and `days_to_expiry >= supplier_return_min_days_to_expiry`. Recovery is `units * unit_cost_try * supplier_return_credit_pct`.
- **Step fields:** `action_cost_try = discounted units sold * unit_price_try * discount_pct / 100`; `net_benefit_try = loss reduction - action_cost_try`; `policy_refs` lists the related POL items. Discounts above `max_discount_pct_by_role` or failed day conditions give `feasible: false` with `infeasible_reason` and no loss change.
- **Output:** `{lot_id, baseline_loss_try, steps[], final_loss_try, total_net_benefit_try}`.

**Vertical slice:** `simulate` first returns the stub-contract shape with the same step fields (a lot found in the snapshot, `baseline_loss_try` from risk.py, per-action `feasible`, `loss_after_try`, `net_benefit_try`, `kg_saved`, `policy_refs`), using simple proportional savings like the stub. The semantics above replace it in the refinement slice without changing the output shape.

### Interfaces

```python
# fefo_core/pipeline.py
@dataclass(frozen=True)
class Snapshot:
    as_of_date: str
    risk_items: list[dict]           # ExpiryRiskItem, sorted by loss_try.expected desc
    sku_profiles: dict[str, dict]    # sku_id -> SkuProfile
    lots_by_id: dict[str, dict]      # enriched lots for simulate and report
    params: dict

def load_snapshot(data_dir: Path, as_of_date: str) -> Snapshot: ...

# fefo_core/validate.py
@dataclass
class ValidationIssue: file: str; row: int; rule: str
class ValidationError(Exception): ...
def run(tables) -> list[ValidationIssue]: ...     # empty list = valid

# fefo_core/forecast.py
@dataclass
class ForecastResult: low: float; expected: float; high: float; wape: float; confidence: str
```

`fefo_core` imports nothing from `fefo_mcp` or AWS libraries.

## fefo_mcp

- `__main__.py`: same tool declarations as the stub (names, parameters, `Literal` enums, docstrings). Only the tools import changes, and `logging.basicConfig(stream=sys.stderr)` stays.
- `tools.py`: replaces fixture reads with `_SNAPSHOT = load_snapshot(DATA_DIR, DEFAULT_AS_OF_DATE)` at import time, `DATA_DIR = Path(__file__).resolve().parent.parent / "data"`. Invalid input returns `_err(code, message)` and never raises. A different `as_of_date` recomputes risk from the cached features, not from the files.
- `report.py`: `generate_report_file`, with the `fpdf2`, `openpyxl` and `boto3` imports kept inside this module.

### PDF (`DAILY_RISK`)

- `fpdf2` (pure Python, no ARM64 wheel problem). Font order: `fc-list` search for a font with ş ğ ı İ ç ö ü ₺; else the bundled `assets/DejaVuSans.ttf`; else download DejaVu Sans into `assets/` (not expected in this sandbox).
- Sections: title and `as_of_date`, total expected loss, top N lots table, reason-code counts, pending decisions (`decisions/*.json` with `status=DRAFT`; an empty list is fine). `summary_text` is printed verbatim under a separate "Yorum" heading, and no number is read from it. Every number comes from the `Snapshot`.
- File name `FEFO_Gunluk_Risk_<as_of_date>.pdf`.

### Excel (`RISK_TABLE`, refinement)

`openpyxl`; bold header row matching `ExpiryRiskItem` fields, one row per item in `Snapshot.risk_items`, integer formats for `qty_units` and `days_to_expiry`, `'#,##0.00 "₺"'` for `loss_try` columns. File name `FEFO_Risk_Tablosu_<as_of_date>.xlsx`.

### S3 upload

```python
key = f"reports/{as_of_date}/{file_id}.{ext}"
s3.put_object(Bucket=bucket, Key=key, Body=data)
url = s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=3600)
```

Missing `REPORTS_BUCKET` or any `ClientError`/`BotoCoreError` returns `{"error": {"code", "message"}}` with no `download_url`. A missing `lot_id` for `LOT_ACTION_PLAN` returns `INVALID_ARGUMENT`.

### S3 policy (checked against the files)

- `FefoAgent/app/agent/policies/s3-reports.json` has one statement, Sid `FefoReportsAndDecisionsObjects`, `Allow` on `s3:PutObject` and `s3:GetObject` for `arn:aws:s3:::fefo-862714237836-us-east-1/reports/*` and `.../decisions/*`.
- `agentcore/agentcore.json` lists `"policies/s3-reports.json"` in the `agent` runtime's `additionalPolicies` (path relative to `codeLocation: app/agent`) and sets `REPORTS_BUCKET` to `fefo-862714237836-us-east-1`, the same bucket as the policy.
- So the key prefix `reports/` is covered for `PutObject` and `GetObject`, and the `reports/<as_of_date>/<file_id>.<ext>` key falls under `reports/*`. No bucket-level actions (such as `ListBucket`) are granted; the design does not need them.
- The presigned URL is signed with the runtime role credentials and works only while those credentials are valid; 3600 seconds is the requested expiry, not a guarantee.
- No policy change is needed. If a deployed call returns `AccessDeniedException`, extend `s3-reports.json`, never edit IAM by hand.

### Other changes

- `mcp_adapter.py` stays unchanged: `PASSTHROUGH_KEYS` already includes the AWS credentials, `AWS_REGION`, `AWS_DEFAULT_REGION` and `REPORTS_BUCKET`, and `build_child_env()` copies the full environment.
- `agentcore.json`: `MCP_BACKEND` changes from `"stub"` to `"fefo_mcp"` at deploy time.
- `pyproject.toml` `[project].dependencies` gains `fpdf2` and `openpyxl`. `fefo_core` adds none.

## Error Handling

- **Startup validation failure:** issues go to stderr and the process exits non-zero before `mcp.run()`.
- **Tool input errors:** `INVALID_ARGUMENT`, `LOT_NOT_FOUND`, `SKU_NOT_FOUND` returned as a dict, never raised.
- **Report errors:** `ReportError` maps to `{"error": {...}}` with no `download_url`.
- **Sync script:** a missing source directory prints a warning to stderr and leaves the destination untouched; an unknown option or `--from` without a value prints usage and exits non-zero.

## Test Plan

Plain pytest, no property-based testing.

1. **`fefo_core` unit tests:** one test module per `fefo_core` module (`validate`, `features`, `forecast`, `risk`, `simulate`) on a small hand-built fixture (a few SKUs, 2 dealers, about 35 days). Examples: `validate` rejects one known-bad row per rule; `features` fills missing days with 0 and returns the expected shares, trend and FIFO flag; `forecast` returns the expected 4-week weekday average, min/max band and WAPE on a known series; `risk` returns the exact hand-computed `at_risk_units`, `loss_try`, `risk_level` and `forecast_confidence`; `simulate` checks each of the five actions on one lot.
2. **Contract tests:** the existing `FefoAgent/app/agent/tests/` run with `MCP_BACKEND=fefo_mcp` (and still with `stub`).
3. **Scenario test:** on the data in `data-gen/out/`, with `scenarios/scenarios.csv` as truth: each Scenario_SKU's returned `reason_codes` contain its `expected_reason_code`; the Control_SKU is not listed as risky; the Low_Confidence_SKU has `forecast_confidence == "LOW"`.
4. **PDF test:** generate a `DAILY_RISK` PDF locally (S3 call mocked or skipped), open it, extract the text and check that ş ğ ı İ ç ö ü ₺ are present.
5. **`sync_data.sh` smoke test:** run it into a temp destination from a temp source that contains `raw/`, `config/`, `policy/` and `scenarios/`; assert the three directories are copied, `scenarios/` is never copied, and the source is unchanged. Also check the missing-source and bad-option exits.
6. **Deploy verification (manual):** the five Lab 7 checks plus the "Gunluk riskli urun raporunu PDF yap" prompt returning a link that downloads a file starting with `%PDF`.
