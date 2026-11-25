# Requirements Document

## Introduction

Bu özellik, FEFO Kurtarma Ajanı için `stub` MCP backend'inin yerine gerçek hesaplama yapan `fefo_core` (saf Python pipeline) ve `fefo_mcp` (kendi MCP server'ımız) bileşenlerini, bunların ürettiği PDF/Excel raporlarını ve veri senkronizasyonunu kapsar. Kaynak: `TEAM_PLAN_FEFO_AGENT.md` bölüm 3, 3.11, 4.3, 4.6, 6.3 (adım 1, 2, 5) ve 9.

Öncelik sırası **uçtan uca dikey dilimdir**: sentetik veri → `fefo_core` → `fefo_mcp` → PDF rapor → deploy ve doğrulama. `simulate_actions` ayrıntılandırması ve `RISK_TABLE` xlsx raporu dikey dilimden sonra gelir (Requirement 8 ve 9).

Kapsam dışı: DynamoDB, git commit, Plan 2/3 tool'ları (`list_contacts`, `prepare_email`), chat UI, Knowledge Base.

Varsayımlar:
- `data/` dizini sahibi Lojistik (L) rolüdür. Bu özellik `data/` altına yalnızca kullanıcı onayıyla yazar.
- `create_action_drafts` ve `decision_id` davranışı stub'daki gibi kalır.
- `fefo_core` ve `fefo_mcp` kodu doğrudan `FefoAgent/app/agent/fefo_core/` ve `FefoAgent/app/agent/fefo_mcp/` altına yazılır.
- `fefo_mcp_stub/` dizini, kullanıcı onaylayana kadar silinmez ve değiştirilmez.

## Glossary

- **Synthetic_Data_Generator**: `data-gen/` altındaki, sabit seed ile sentetik veri üreten betik.
- **Generated_Output_Dir**: `data-gen/out/` dizini; alt dizinleri `raw/`, `config/`, `policy/`.
- **Data_Dir**: Repo kökündeki `data/` dizini (alt dizinler `raw/`, `config/`, `policy/`, `scenarios/`).
- **Agent_Data_Dir**: `FefoAgent/app/agent/data/` dizini.
- **Sync_Script**: Repo kökündeki `scripts/sync_data.sh` betiği.
- **Scenarios_Dir**: `data/scenarios/` dizini; ground truth içerir ve agent paketine girmez.
- **Scenario_Truth_File**: Sentetik senaryo SKU'ları için beklenen `reason_code` değerlerini içeren ground-truth dosyası; `data-gen/out/scenarios/` altına yazılır ve agent paketinin dışında kalır.
- **Scenario_SKU**: `TEAM_PLAN_FEFO_AGENT.md` bölüm 3.11 senaryolarından birini temsil eden SKU.
- **Control_SKU**: Riskli olmaması beklenen kontrol SKU'su.
- **Low_Confidence_SKU**: Düşük tahmin güvenine sahip olması beklenen SKU.
- **Contract_Tests**: `FefoAgent/app/agent/tests/` altındaki mevcut MCP sözleşme testleri.
- **Fefo_Core**: `FefoAgent/app/agent/fefo_core/` altındaki saf Python modülleri: validate, features, forecast, risk, simulate.
- **Fefo_MCP**: `FefoAgent/app/agent/fefo_mcp/` altındaki stdio MCP server'ı; `fefo_mcp_stub/` kopyalanarak oluşturulur ve `FastMCP` ile tool'ları sunar.
- **Stub_Server**: `FefoAgent/app/agent/fefo_mcp_stub/` altındaki sahte MCP server.
- **Tool_Contract**: `TEAM_PLAN_FEFO_AGENT.md` bölüm 4.1–4.4 ve 4.6'daki tool girdi/çıktı sözleşmeleri.
- **Report_Generator**: `generate_report_file` tool'unun rapor üreten parçası.
- **Reports_Bucket**: `REPORTS_BUCKET` ortam değişkeniyle verilen S3 bucket'ı.
- **Presigned_URL**: Reports_Bucket'taki bir nesne için 3600 saniye geçerli S3 indirme bağlantısı.
- **Agent_Runtime**: `FefoAgent` AgentCore Runtime'ı (runtime adı `agent`).
- **Agent_Model**: `global.anthropic.claude-sonnet-5` model ID'si.
- **As_Of_Date**: Varsayılan `2026-11-25` tarihi.
- **Agent_Pyproject**: `FefoAgent/app/agent/pyproject.toml`.
- **Unicode_Font**: PDF'e gömülen Unicode TTF fontu (ör. DejaVuSans); `FefoAgent/app/agent/fefo_mcp/assets/` altında paketlenir.
- **Font_Assets_Dir**: `FefoAgent/app/agent/fefo_mcp/assets/` dizini.

## Requirements

### Requirement 1: Synthetic data staging

**User Story:** As a Dev B, I want synthetic data generated into a staging directory, so that the real `data/` directory owned by L is never overwritten unintentionally.

#### Acceptance Criteria

1. WHEN the Synthetic_Data_Generator runs, THE Synthetic_Data_Generator SHALL write its output to `raw/`, `config/` and `policy/` subdirectories of the Generated_Output_Dir.
2. THE Synthetic_Data_Generator SHALL produce the files and columns defined in `TEAM_PLAN_FEFO_AGENT.md` section 3 (3.1–3.8) for `raw/` and `config/`.
3. WHEN the Synthetic_Data_Generator runs twice with the same seed, THE Synthetic_Data_Generator SHALL produce byte-identical output files.
4. THE Synthetic_Data_Generator SHALL write no file into the Data_Dir.
5. WHEN a task requires writing into the Data_Dir, THE System SHALL obtain explicit user approval before the write.
6. THE Synthetic_Data_Generator SHALL write the Scenario_Truth_File only under `data-gen/out/scenarios/` and SHALL write no `scenarios/` content into the Agent_Data_Dir or into the `raw/`, `config/` and `policy/` subdirectories of the Generated_Output_Dir.
7. THE Synthetic_Data_Generator SHALL generate 30 days of data for 10 dealers and approximately 40 products.
8. THE Synthetic_Data_Generator SHALL generate at least 6 Scenario_SKUs, each implementing a distinct scenario of `TEAM_PLAN_FEFO_AGENT.md` section 3.11.
9. THE Synthetic_Data_Generator SHALL generate exactly 1 Control_SKU and exactly 1 Low_Confidence_SKU.
10. THE Synthetic_Data_Generator SHALL use a fixed random seed.
11. THE Synthetic_Data_Generator SHALL record the expected `reason_code` of every Scenario_SKU in the Scenario_Truth_File.

### Requirement 2: One-way data sync script

**User Story:** As a Dev B, I want a single sync script at `scripts/sync_data.sh`, so that agent data is copied one-way from the source data directory to the agent package.

#### Acceptance Criteria

1. WHEN the Sync_Script runs without arguments, THE Sync_Script SHALL copy `raw/`, `config/` and `policy/` from the Data_Dir to the Agent_Data_Dir.
2. WHEN the Sync_Script runs with the argument `--from data-gen/out`, THE Sync_Script SHALL copy `raw/`, `config/` and `policy/` from the Generated_Output_Dir to the Agent_Data_Dir.
3. THE Sync_Script SHALL exclude the Scenarios_Dir from every copy.
4. IF the source directory does not exist, THEN THE Sync_Script SHALL print a warning naming the missing directory to stderr and exit without modifying the Agent_Data_Dir.
5. IF the argument `--from` is given without a value or with an unknown option, THEN THE Sync_Script SHALL print a usage message and exit with a non-zero status.
6. WHEN the Sync_Script completes, THE Sync_Script SHALL print the source directory, the destination directory and the number of files copied.
7. THE Sync_Script SHALL leave the Data_Dir unchanged.

### Requirement 3: Deterministic pure-Python pipeline

**User Story:** As a Dev B, I want a deterministic pure-Python pipeline, so that risk numbers are reproducible and lightweight enough to run inside the agent package.

#### Acceptance Criteria

1. THE Fefo_Core SHALL use only the Python standard library, with no pandas dependency and no third-party packages.
2. THE Fefo_Core SHALL run on Python 3.12 and Python 3.14.
3. WHEN the Fefo_Core `validate` step runs, THE Fefo_Core SHALL check the consistency rules of `TEAM_PLAN_FEFO_AGENT.md` section 3.12 that apply to the generated data.
4. IF a validation rule fails, THEN THE Fefo_Core SHALL return an error list naming the file, row and rule.
5. WHEN the Fefo_Core runs twice on identical input files, THE Fefo_Core SHALL return identical output.
6. WHEN the Fefo_Core `forecast` step runs for a SKU, THE Fefo_Core SHALL use a single forecast method, the average of the same weekday over the last 4 weeks (`WEEKDAY_AVG_4W`), and SHALL return low, expected and high daily-demand values (minimum, mean and maximum of those 4 values) and a WAPE value from a 7-day backtest.
7. WHEN the Fefo_Core `risk` step runs for a lot, THE Fefo_Core SHALL compute the at-risk units and the expected loss in TRY using the dealer eligibility rule `(expiry_date − d) ≥ min_days_on_receipt` and the thresholds from `config/params.json`.
8. THE Fefo_Core SHALL read every assumption value (elasticity, thresholds, action limits) from `config/params.json`.
9. THE Fefo_Core SHALL be written directly to `FefoAgent/app/agent/fefo_core/`.
10. THE Fefo_Core SHALL include unit tests that run against a fixture smaller than the generated dataset.

### Requirement 4: Fefo_MCP stub-compatible tools

**User Story:** As an agent developer, I want Fefo_MCP to expose the same tools as the stub, so that switching backends needs no agent code change.

#### Acceptance Criteria

1. THE Fefo_MCP SHALL expose the tools `get_expiry_risks`, `get_sku_profile`, `simulate_actions`, `create_action_drafts` and `generate_report_file` over stdio transport using `FastMCP`.
2. THE Fefo_MCP SHALL keep the tool names, parameter names, parameter types, enum values and docstrings identical to those in the Stub_Server.
3. THE Fefo_MCP SHALL be created by copying the Stub_Server directory `fefo_mcp_stub/` to `FefoAgent/app/agent/fefo_mcp/` and replacing only the code that reads fixtures with calls to the Fefo_Core.
4. WHEN the Fefo_MCP server starts, THE Fefo_MCP SHALL compute the Fefo_Core results once and keep them in memory for all later tool calls.
5. THE Fefo_MCP SHALL return output that conforms to the Tool_Contract.
6. WHEN a tool receives invalid input, THE Fefo_MCP SHALL return `{"error": {"code": "...", "message": "..."}}` and raise no exception.
7. THE Fefo_MCP SHALL write nothing to stdout and send all log output to stderr.
8. WHEN `as_of_date` is not provided, THE Fefo_MCP SHALL use the As_Of_Date.
9. WHEN `get_expiry_risks` returns items, THE Fefo_MCP SHALL sort them by `loss_try.expected` in descending order.
10. THE Fefo_MCP SHALL read data files through paths relative to the package location.
11. WHEN `create_action_drafts` runs, THE Fefo_MCP SHALL return `decision_id` and `status`, `drafts` and `summary` fields with the same behavior as the Stub_Server, including the "TASLAK — gönderilmedi" header in every draft body.

### Requirement 5: PDF daily risk report

**User Story:** As a user, I want a PDF daily risk report with correct Turkish characters, so that I can download and read it.

#### Acceptance Criteria

1. WHEN `generate_report_file` receives `report_type` `DAILY_RISK` and `format` `pdf`, THE Report_Generator SHALL produce a PDF containing the total expected loss, the top N riskiest lots, the reason code distribution and the pending decisions.
2. THE Report_Generator SHALL create PDF files with `fpdf2` and embed the Unicode_Font so that the characters ş, ğ, ı, İ, ç, ö, ü and ₺ render correctly.
3. WHEN the Unicode_Font is selected, THE Report_Generator SHALL first search the system with `fc-list` for a Unicode font that contains these characters.
4. IF `fc-list` finds no suitable Unicode font, THEN THE System SHALL download a permissively licensed Unicode font and place it in the Font_Assets_Dir.
5. THE Report_Generator SHALL print every number in the report from Fefo_Core output.
6. WHERE `summary_text` is provided, THE Report_Generator SHALL place it in a separate "Yorum" section.
7. WHEN the Report_Generator writes a file, THE Report_Generator SHALL store it in the Reports_Bucket at `reports/<as_of_date>/<file_id>.pdf`.
8. WHEN the Report_Generator stores a file, THE Report_Generator SHALL return a Presigned_URL as `download_url` and `3600` as `expires_in_sec`.
9. THE Report_Generator SHALL return `file_id`, `file_name`, `format`, `s3_key`, `download_url`, `expires_in_sec` and `size_bytes` with `size_bytes` greater than 0.
10. THE Report_Generator SHALL name the file in the form `FEFO_Gunluk_Risk_<as_of_date>.pdf` for `DAILY_RISK`.
11. IF the Reports_Bucket variable is missing or the S3 write fails, THEN THE Report_Generator SHALL return an error with code and message and no `download_url`.
12. IF `report_type` is `LOT_ACTION_PLAN` and `lot_id` is missing, THEN THE Report_Generator SHALL return an `INVALID_ARGUMENT` error.

### Requirement 6: MCP subprocess environment and dependencies

**User Story:** As Dev B, I want the MCP server to receive the environment it needs, so that report upload works inside the Agent_Runtime.

#### Acceptance Criteria

1. WHEN the agent starts the Fefo_MCP subprocess, THE Agent_Runtime SHALL pass the AWS credential variables, `AWS_REGION` and `REPORTS_BUCKET` to the subprocess.
2. THE Agent_Runtime SHALL start the Fefo_MCP with the same Python interpreter as the agent.
3. WHEN `MCP_BACKEND` is `fefo_mcp`, THE Agent_Runtime SHALL load the Fefo_MCP instead of the Stub_Server.
4. THE feature implementation SHALL add `fpdf2` and `openpyxl` to `[project].dependencies` of the Agent_Pyproject.
5. THE Agent_Pyproject SHALL list only runtime dependencies that have ARM64 Linux wheels in `[project].dependencies`.
6. THE Agent_Runtime SHALL use the Agent_Model as the model ID.

### Requirement 7: Deploy and end-to-end verification

**User Story:** As Dev B, I want the real backend deployed and verified end to end, so that the vertical slice is proven in the AgentCore environment.

#### Acceptance Criteria

1. WHEN the deploy runs, THE Agent_Runtime SHALL have `MCP_BACKEND` set to `fefo_mcp` in `FefoAgent/agentcore/agentcore.json`.
2. WHEN the deploy completes, THE verification SHALL pass the five Lab 7 checks of `TEAM_PLAN_FEFO_AGENT.md` section 9: `agentcore status` shows the runtime deployed with an ARN, the invoke with prompt "Bugun riskli urunler neler? Bir aracini cagir ve sonucu goster." and `actorId` `depo-test` returns tool data, the `-DEFAULT` log group exists and `agentcore traces runtime list --since 15m` shows the invoke trace, `.kiro/specs/` documents the agent, and `agentcore traces runtime get <trace-id>` shows `fefo_mcp` tool call spans.
3. WHEN the extra test prompt "Gunluk riskli urun raporunu PDF yap" is invoked on the deployed Agent_Runtime, THE Agent_Runtime SHALL return a chat answer containing a download link that returns HTTP 200 and a file starting with `%PDF`.
4. IF the deployed Agent_Runtime returns an `AccessDeniedException` on the S3 write, THEN THE deploy configuration SHALL grant the permission through `additionalPolicies` in `FefoAgent/agentcore/agentcore.json` and SHALL NOT use manual IAM edits.
5. WHILE the user has not approved, THE System SHALL keep the `fefo_mcp_stub` directory in place and SHALL delete it only after explicit user approval.
6. THE System SHALL create no git commit during this feature.

### Requirement 8: Action simulation refinement

**User Story:** As a commercial user, I want realistic action simulation, so that the loss waterfall reflects demand, eligibility and policy limits.

#### Acceptance Criteria

1. WHEN `simulate_actions` receives a list of actions, THE Fefo_Core SHALL apply the actions in the given order.
2. THE Fefo_Core SHALL support the action types `FEFO_PRIORITY`, `DEALER_OFFER`, `CAMPAIGN`, `DONATION` and `SUPPLIER_RETURN` with the semantics of `TEAM_PLAN_FEFO_AGENT.md` section 4.3.
3. WHEN `DEALER_OFFER` or `CAMPAIGN` is simulated, THE Fefo_Core SHALL increase demand by `elasticity × discount_pct` using the elasticity value from `config/params.json`.
4. WHEN a step is simulated, THE Fefo_Core SHALL return `net_benefit_try` equal to the loss reduction minus `action_cost_try`.
5. WHEN `DONATION` is simulated, THE Fefo_Core SHALL return `kg_saved` and no reduction in TRY loss.
6. IF an action violates a feasibility limit from `config/params.json`, THEN THE Fefo_Core SHALL return the step with `feasible` set to false and an `infeasible_reason`.
7. WHEN a step is returned, THE Fefo_Core SHALL include `policy_refs` listing the related POL items.

### Requirement 9: Excel risk table

**User Story:** As a user, I want an Excel risk table, so that I can filter and sort all risky lots.

#### Acceptance Criteria

1. WHEN `generate_report_file` receives `report_type` `RISK_TABLE` and `format` `xlsx`, THE Report_Generator SHALL produce an xlsx file with `openpyxl` containing every risky lot.
2. THE Report_Generator SHALL write a header row, numeric cell formats and TRY-formatted loss columns in the xlsx file.
3. THE Report_Generator SHALL print values identical to the Fefo_Core output.
4. WHEN the Report_Generator stores the xlsx file, THE Report_Generator SHALL use the S3 key and Presigned_URL rules of Requirement 5.
5. THE Report_Generator SHALL name the file in the form `FEFO_Risk_Tablosu_<as_of_date>.xlsx`.

### Requirement 10: Local verification of the Fefo_MCP backend

**User Story:** As a Dev B, I want the real backend verified locally against contracts and scenarios, so that the deploy starts from a proven state.

#### Acceptance Criteria

1. WHEN `MCP_BACKEND` is `fefo_mcp`, THE Contract_Tests in `FefoAgent/app/agent/tests` SHALL pass.
2. WHEN the Fefo_MCP runs on the data in the Generated_Output_Dir, THE Fefo_MCP SHALL return for each Scenario_SKU a `reason_codes` list that contains the expected `reason_code` recorded in the Scenario_Truth_File.
3. WHEN the Fefo_MCP runs on the data in the Generated_Output_Dir, THE Fefo_MCP SHALL return no risky lot for the Control_SKU.
4. WHEN a PDF report is generated locally, THE System SHALL open the generated PDF file and check that it contains the characters ş, ğ, ı, İ, ç, ö, ü and ₺.
