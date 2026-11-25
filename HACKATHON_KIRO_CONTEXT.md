# Hackathon Context for Kiro — Agentic AI in Supply Chain (AWS AgentCore + Kiro)

> **Source:** AWS Workshop Studio event "Agentic AI in Supply Chain Hackathon Training — Ship Production Agents on Amazon Bedrock AgentCore with Kiro" (all pages of Getting Started, Labs 1–7, Cleanup, Conclusion), compiled 2026-11-24.
> A companion file `HACKATHON_FULL_GUIDE_RAW.md` holds the full text of every workshop page if a detail is missing here.

---

## 0. INSTRUCTIONS FOR KIRO (read first)

You are helping a team build a hackathon agent inside the **Kiro IDE Browser** of an AWS Workshop Studio team account. Follow these rules:

1. **Theme:** the hackathon is about **agentic AI in supply chain**. Our project is Lab 7 ("Bring Your Own Use Case") with a supply-chain use case. Judges/organizers want us to use the AWS stack below: **Kiro Specs (or AI-DLC) → Strands Agents → Amazon Bedrock AgentCore (Runtime, Memory, Gateway, Identity, Observability) → optional chat UI on ECS Fargate.** Prefer these technologies over alternatives.
2. **Three non-negotiable guardrails** (section 4) must appear as acceptance criteria in every `requirements.md` and as tasks in every `tasks.md`. Do not approve or execute a plan that misses one.
3. **Always scaffold with the AgentCore CLI** (`agentcore create ... --template agent-python-strands`). Never hand-create the project structure. Project name must NOT be `CustomerServiceAgent`.
4. The steering files `~/environment/.kiro/steering/agentcore-deployment.md` and `strands-agent-coding.md` are the authoritative production rules; this file summarizes them and adds context. If they conflict, steering wins.
5. Work spec-first: requirements → design → tasks → execute one task at a time, verifying each. Ask clarifying questions before drafting.
6. Respect every rule in section 6 (critical gotchas): model ID format, import path, lazy init, ARM64, runtime-only deps, IAM via `additionalPolicies`, ports, session-id length, CLI version pin.
7. Use the MCP servers (`aws-mcp`, `bedrock-agentcore-mcp-server`, `strands-agents`, `awslabs.ecs-mcp-server`) to look up current docs before guessing APIs; say which doc you used.
8. When something breaks: investigate first (logs, `agentcore status`, traces), explain the cause, then fix. For stubborn issues use the **Bug Fix** built-in agent.

---

## 1. Event facts

| Item | Value |
|---|---|
| Event | Agentic AI in Supply Chain Hackathon Training — Ship Production Agents on Amazon Bedrock AgentCore with Kiro |
| Start / duration | 2026-11-24 09:38, 72 hours (account auto-closes at the end; all resources deleted) |
| Region | **us-east-1** only |
| Workshop level | 200–300; Part 1 (Labs 1–6) ≈ 2 h guided; Part 2 (Lab 7) = hackathon, 4 h – 2 days |
| AWS services listed | Amazon Bedrock AgentCore, Kiro, Amazon ECS |

**Event outputs (Workshop Studio dashboard):**

| Output | Stack | Purpose |
|---|---|---|
| `URL` | kiro-ide-browser | Kiro IDE Browser (pre-authenticated; URL contains a token — get it from the dashboard, don't share) |
| `S3BucketName` | workshop-team-stack | `workshop-team-stack-knowledgebasebucketc011dd60-xgntd78nbfll` — upload **our own documents** here for a Knowledge Base (`$S3_BUCKET_NAME`) |
| `EcsClusterArn` | workshop-team-stack | `arn:aws:ecs:us-east-1:825264609680:cluster/agent-workshop-cluster` (`$ECS_CLUSTER`) for the chat UI |
| `DashboardUrl` | workshop-central-stack | Leaderboard: https://d1bq2pj3ye0f30.cloudfront.net (login with credentials from the event's Central Infrastructure outputs) |

AWS console for the team account: link in the left nav of the Event Dashboard.

---

## 2. Environment, permissions and limits

**Kiro IDE Browser**: Kiro IDE served in the browser, runs on an instance in the team account, already signed in with a team Kiro API key. No Kiro account / Builder ID needed. If Kiro ever asks to sign in → don't; contact facilitator.
- Workspace: `~/environment` (terminal opens there, user `participant`). Never use `sudo`.
- First load: "Do you trust the remote host '.cloudfront.net'?" → *Always trust* + *Trust and Connect*. A ">50 MCP tools enabled" warning is expected; dismiss.
- Terminal: `Ctrl+Shift+\``. Kiro chat panel on the right; **Autopilot** toggle (applies edits without per-step approval); `+` = New Session (use per task to keep context clean).
- Built-in agents in a new session: **Spec, Quick Spec, Plan, Bug Fix** (Vibe = plain chat).
- Kiro CLI: `kiro-cli chat` from `~/environment` (V3 UI). Commands: `/clear`, `/model`, `/tools`, `/quit`, `/spec new <name>`. `kiro-cli chat --list-models` checks model access.

**Pre-installed toolchain** (verify with the block below): Node ≥20, Python ≥3.10, AWS CLI v2, CDK v2, **AgentCore CLI 1.0.3 (pinned — never run `agentcore update` or `npm update -g @aws/agentcore`)**, Kiro CLI, uv/uvx, git, jq, Docker + buildx (no sudo).

```bash
node --version; python3 --version; aws --version; cdk --version; agentcore --version
kiro-cli --version; uv --version; uvx --version; git --version; jq --version
docker --version; docker buildx version; docker ps; aws sts get-caller-identity
echo "$AWS_REGION $ACCOUNT_ID $S3_BUCKET_NAME $ECS_CLUSTER $IDE_URL"
```

**Environment variables**: `AWS_REGION`, `ACCOUNT_ID`, `S3_BUCKET_NAME`, `ECS_CLUSTER`, `IDE_URL` (open local web apps via `python3 -m webbrowser $IDE_URL/proxy/<port>/`). After Lab 3 backend creation: `API_GATEWAY_URL`.

**Python packages**: system Python has **no pip**. Use `uv` (`uv venv && source .venv/bin/activate && uv pip install -r requirements.txt`, or `uv sync` / `uv run` inside an agent project).

**Ports**: `8080` = the IDE itself (never use/kill), `8081` = `agentcore dev`, `8082` = optional Agent Inspector UI, `8888` = chat UI.

**Permissions / what the participant role can't do:**
- Cannot `bedrock:ListInferenceProfiles` → don't list profiles; prefix the foundation model ID with `global.` (or `us.`).
- Cannot `aws iam put-role-policy` on the runtime role → grant extra AWS permissions only through `additionalPolicies` in `agentcore/agentcore.json` (see 6).
- Anthropic models need a one-time Marketplace agreement (bootstrap already did it). If a deployed agent gets `AccessDeniedException ... AWS Marketplace actions`, run `enable_anthropic_models` once in the terminal and wait 2–6 min. **Never** add marketplace perms to the runtime role.
- If AWS credentials expire: re-export them from the Workshop Studio event page.

**Workshop helper commands (terminal aliases):**

| Command | What it does |
|---|---|
| `create_knowledge_base` | Creates the sample Bedrock KB `anycompany-telecom-kb` (telecom docs, own bucket, OpenSearch Serverless) and prints the KB ID |
| `create_backend_systems` | Creates sample backend: 3 Lambdas (`billing-mcp`, `ticketing-mcp`, `escalation-mcp`), DynamoDB (`customers`, `billing`, `tickets`, seeded CUST-001…CUST-010), API Gateway `MCP-Server-API` (~2 min). Re-run to update Lambda code |
| `enable_anthropic_models` | Accepts the Marketplace agreement for active Anthropic models |
| `cleanup_workshop` | Removes lab resources (agent in current folder, ECS service, Lab 3 backend, KB). Only needed to reset/rebuild |

**Pre-provisioned Kiro skills** (`~/environment/.kiro/skills/`, invoke with `/` in chat): `build-customer-service-agent` (Lab 1 playbook), `build-chat-ui` (Lab 6 UI playbook), `deploy-chat-ui-to-ecs` (Lab 6 ECS playbook). Good references for our own build.

---

## 3. Technology cheat sheet

### Development side
| Technology | What it is | How we use it |
|---|---|---|
| **Kiro** | Agentic IDE + CLI built around spec-driven development | All building happens by prompting Kiro |
| **Kiro Specs** | Prompt → `.kiro/specs/<name>/requirements.md` (user stories, EARS acceptance criteria) + `design.md` + `tasks.md`; each phase approved before code | Main build path for Lab 7 (~4 h). Edit spec files directly; Kiro picks up edits. "Run all tasks for this spec" executes |
| **Quick Spec** | Same 3 artifacts generated in one pass after clarifying questions, no approval gates between phases | Use when < 2 h or for smaller features; still review `tasks.md` against guardrails |
| **Vibe / Plan / Bug Fix** | Free chat; planning agent; investigate→diagnose→fix flow | Quick questions; debugging stubborn errors |
| **Steering files** | `.kiro/steering/*.md`, always-on rules read at every session start (`inclusion: always`) | `agentcore-deployment.md` + `strands-agent-coding.md` (or `langgraph-agent-coding.md` — never both). We can add our own (e.g. supply-chain domain rules) |
| **Skills** | `.kiro/skills/<name>/SKILL.md`, on-demand playbooks invoked with `/` | 3 pre-provisioned; AI-DLC adds `aidlc` |
| **Hooks** | `.kiro/hooks/*.json`, run a command/prompt on events (e.g. `PostFileSave`) | Optional: run pytest on save, health check on save |
| **MCP servers (dev tooling)** | `~/.kiro/settings/mcp.json`: `aws-mcp` (AWS docs + API), `bedrock-agentcore-mcp-server` (AgentCore CLI docs), `strands-agents` (Strands SDK docs), `awslabs.ecs-mcp-server` (read-only ECS/Fargate) | Kiro looks up current docs; check with `/tools` |
| **Kiro Powers** | Packaged MCP + context (Strands, AWS AgentCore) | Alternative to manual mcp.json — use one or the other, not both |
| **AI-DLC** | AWS Labs "AI-Driven Development Lifecycle" workflow (`/aidlc`), phases Initialization → Ideation → Inception → Construction → Operation, approval before major steps, artifacts in `~/environment/aidlc/` | Alternative Lab 7 path. Profiles: `express` (~4 h), `workshop` (~1 day), `feature` (≤2 days), `poc` fallback |

### Runtime / AWS side
| Technology | What it is | How we use it |
|---|---|---|
| **Strands Agents SDK** | AWS open-source Python agent SDK, model-driven loop (prompt → model → tool use → response), `@tool` decorator, hooks, MCP client | Default agent framework (template `agent-python-strands`) |
| **LangGraph** (alternative) | Graph-based agent framework | Allowed for Lab 7 via template `agent-python-langchain` + LangGraph steering file |
| **Amazon Bedrock** | Managed foundation models | Claude via **inference profile ID** (e.g. `global.anthropic.claude-sonnet-…`), discovered at build time |
| **Bedrock Knowledge Bases** | Managed RAG: S3 docs → embeddings → OpenSearch Serverless vector store; `Retrieve` / `RetrieveAndGenerate` APIs | Domain documents (SOPs, supplier contracts, policies) for our agent |
| **AgentCore Runtime** | Serverless, auto-scaling hosting for agents (ARM64/Graviton), session isolation, streaming endpoint | Deploy target (`agentcore deploy`) — **required guardrail** |
| **AgentCore CLI** (`@aws/agentcore` 1.0.3) | Scaffold, dev, deploy, invoke, logs, traces, memory inspection; CDK under the hood | Every lifecycle step |
| **AgentCore Memory** | Short-term (session events, EPISODIC `/episodes/{actorId}/{sessionId}`) + long-term (SEMANTIC facts `/users/{actorId}/facts`, extracted async ~1 min) | Template already declares `agentMemory`; keep it |
| **AgentCore Gateway** | Managed MCP server that exposes Lambdas / APIs as tools behind one URL, with IAM role and injected URL env var | Connect agent to backend systems (inventory, orders, suppliers…) |
| **AgentCore Identity** | Inbound JWT authorizer on runtime (`CUSTOM_JWT`) + outbound credential management (`agentcore add credentials api-key|oauth`) | Per-user/tenant scoping; lab version uses `actorId` + Strands hook |
| **AgentCore Observability** | OpenTelemetry (ADOT) traces → CloudWatch (needs Transaction Search, enabled by first deploy) | **Required guardrail**; `agentcore traces`, CloudWatch GenAI Observability timeline |
| **MCP (Model Context Protocol)** | Open protocol for tools; Gateway speaks MCP (streamable HTTP, URL ends in `/mcp`) | Agent ↔ tools |
| **AWS Lambda + DynamoDB + API Gateway** | Serverless backend | Tool implementations behind Gateway |
| **Amazon ECS Fargate + ECR + Docker** | Serverless containers + image registry | Streaming chat UI (port 8888) |
| **Amazon CloudWatch** | Logs, traces, Transaction Search | Debug & demo |
| **AWS CDK** | IaC; AgentCore CLI deploys a CDK/CloudFormation stack `AgentCore-<Project>-default` | Implicit |

---

## 4. Lab 7 — our hackathon build (the part that matters)

### Guardrails (must all pass)
| Guardrail | Requirement |
|---|---|
| **Deploy** | Deployed to AgentCore Runtime with `agentcore deploy`, from a project created with `agentcore create` in `~/environment` whose name is **not** `CustomerServiceAgent` |
| **Observability** | `UNIFIED_TRACES_DESTINATION_ENABLED` = `true` as an entry in the runtime's `envVars` list in `agentcore/agentcore.json` |
| **Tool** | At least one tool: an AgentCore Gateway target, an MCP server, or a local tool (Strands `@tool` / LangChain `@tool`) |

Framework can be Strands, LangGraph or own code, as long as the project is created / runtime registered with the AgentCore CLI. Supporters review briefs and plans against these guardrails.

**End state:** AgentCore project under `~/environment`, deployed runtime with observability, ≥1 tool, and a spec folder (`.kiro/specs/<name>/`) or `aidlc/` folder documenting the build.

### Inputs to prepare before briefing Kiro
1. **Use case** — one sentence: what the agent does and what it must never do.
2. **Persona** — who talks to it.
3. **Knowledge source** — documents uploaded to `$S3_BUCKET_NAME`; ask Kiro in the brief to create a Knowledge Base from them.
4. **Tools** — the tool(s) that satisfy the Tool guardrail.
5. **Project name** for `agentcore create` (not `CustomerServiceAgent`) → referred to as `<YourLab7Project>`.

Official seed ideas (adapt to supply chain): Investment Assistant (`get_portfolio_summary` from local JSON), IT Helpdesk (runbooks + `create_ticket`), Travel Concierge (`check_availability` mock), Clinical Trial FAQ (`prescreen_eligibility`). Pattern: **docs in a KB + one action tool backed by mock JSON/DynamoDB/Lambda**.

### Path A — Kiro Specs (~4 h)
Time boxes: Start spec 10 min → Requirements 30 → Design 30 → Tasks 20 → Execute 150. With < 2 h, use Quick Spec.
Start: chat panel → new session → **Spec** (or Quick Spec) → "Build a Feature" → Requirements workflow. CLI: `kiro-cli chat` then `/spec new <name>`.
Check `requirements.md` and `tasks.md`: every guardrail must be an acceptance criterion and have a task (`agentcore create --template ...`, set the env var, build the tool, `agentcore deploy`). Execute tasks one by one and confirm each result.

**Spec brief template (keep guardrail lines verbatim):**
```
I want to build a production-grade AI agent: <USE CASE>. The agent serves <PERSONA>.
It answers from <KNOWLEDGE SOURCE> (documents I upload to $S3_BUCKET_NAME, or the
workshop Knowledge Base) and can call <TOOLS>.

Non-negotiable constraints (Lab 7 guardrails):

- Deployed to AgentCore Runtime with `agentcore deploy`, from a project created with `agentcore create` in `~/environment` whose name is not `CustomerServiceAgent` (the Lab 1 project)
- `UNIFIED_TRACES_DESTINATION_ENABLED` set to `true` as an entry in the runtime's `envVars` list in `agentcore/agentcore.json`
- At least one tool exposed: an AgentCore Gateway target, an MCP server, or a local tool (Strands `@tool` or LangChain `@tool`)

Turn this into a spec: write the requirements with acceptance criteria that include
every constraint above, then the design, then the task list. Ask me clarifying
questions before drafting. Wait for my approval of each document before executing.
```
Useful extra constraints to add (from Lab 1's proven brief): import from `bedrock_agentcore.runtime`, lazy init, async streaming handler, keep template `parse_payload` and `agentMemory`, discover latest Claude Sonnet inference-profile ID in `app/agent/model/load.py`, grant KB permissions via `additionalPolicies` policy file under `app/agent/policies/`.

### Path B — AI-DLC (4 h – 2 days)
Install (≈5 min, terminal, no sudo): back up `.kiro` → download pinned installer v2.11.1 → PATH → configure → doctor → verify → reload IDE.
```bash
# 1 backup
if [ -d ~/aidlc-backup ]; then echo "Existing backup kept"; else rm -rf ~/aidlc-backup.tmp && mkdir ~/aidlc-backup.tmp && cp -a ~/environment/.kiro ~/aidlc-backup.tmp/environment-kiro && cp -a ~/.kiro/settings ~/aidlc-backup.tmp/kiro-settings && mv ~/aidlc-backup.tmp ~/aidlc-backup && echo "Backup created"; fi
# 2 install
AIDLC_URL=github.com/awslabs/aidlc-workflows/releases/download/v2.11.1/install.sh
curl -fsSL -o /tmp/aidlc-install.sh "https://$AIDLC_URL" && sh /tmp/aidlc-install.sh --yes
# 3 PATH
export PATH="$HOME/.local/bin:$PATH"; grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc; aidlc --version
# 4 configure + 5 check
cd ~/environment && aidlc config --harness kiro-ide --yes
cd ~/environment && aidlc doctor; echo "aidlc doctor exit code: $?"
# 7 restore if workshop files changed
# cp -a ~/aidlc-backup/environment-kiro/. ~/environment/.kiro/ && cp -a ~/aidlc-backup/kiro-settings/. ~/.kiro/settings/
```
Then reload the IDE tab, accept "Trust this folder", pick agent `aidlc` in a new chat (every new chat starts on Default) and send `/aidlc express <brief + the three guardrail lines>`. CLI: `cd ~/environment && kiro-cli chat --agent aidlc`. If code generation hasn't started by half the planned time → restart with `/aidlc poc <brief>`. Artifacts: `aidlc/spaces/<space>/intents/<YYMMDD>-<label>/…` (`aidlc-state.md`, `inception/requirements-analysis/requirements.md`, `construction/.../code-summary.md`, `construction/build-and-test/test-results.md`, `operation/deployment-execution/deployment-log.md`). If Spec/Quick Spec disappear after AI-DLC install → restore backup, or enable Kiro setting "Workflows".

### Verify (both paths)
```bash
cd ~/environment/<YourLab7Project> && agentcore status          # runtime "deployed" + ARN
agentcore invoke --runtime agent --payload '{"prompt":"Describe your use case in one sentence, then call one of your tools and show what it returns."}'
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/ --query "logGroups[].logGroupName" --output text   # .../<agent-id>-DEFAULT exists
agentcore traces runtime list --since 15m                         # trace of the invoke
```

### Stretch goals (after verify passes) — maps to Labs 2–6
Memory tuning (Lab 2) · Gateway Lambda tools (Lab 3) · Identity scoping (Lab 4) · trace inspection (Lab 5) · streaming chat UI on ECS (Lab 6). Recipes in section 5.

---

## 5. Capability recipes (condensed from Labs 1–6)

### 5.1 Project scaffold + local test + deploy (Lab 1)
```bash
cd ~/environment
agentcore create --name <Project> --template agent-python-strands   # LangGraph: --template agent-python-langchain
# own code: agentcore create --name <P>; cd <P>; agentcore add runtime --name <P> --language python --protocol HTTP  (then use --runtime <P>)
cd <Project>
agentcore dev --port 8081                                            # terminal 1 (headless)
agentcore invoke --runtime agent --local --port 8081 --payload '{"prompt":"hi"}'   # terminal 2
agentcore deploy            # first: 5–8 min (CDK bootstrap, Transaction Search); later ~5 min; verbose: agentcore --debug deploy
agentcore status            # interactive; --json for scripts
```
Template layout: `agentcore/agentcore.json` (runtime `agent`, memory `agentMemory`, gateways, envVars), `agentcore/aws-targets.json`, `agentcore/.env.local`, `agentcore/cdk/`; `app/agent/main.py` (handler + lazy `_get_agent`), `parse.py` (prompt, messages, actorId), `model/load.py` (model ID), `memory/session.py`, `pyproject.toml`; we add `tools/`, `prompts/system_prompt.py`, `tests/`, `policies/`.

**Readable invoke output** (raw output is SSE `data:` lines):
```bash
agentcore invoke --runtime agent --payload '{"prompt":"..."}' \
  | sed -n 's/^data: //p' | jq -rj '.event.contentBlockDelta.delta.text // (.error | select(. != null) | "ERROR: \(.)\n") // empty'; echo
```
Payload is single-quoted JSON → no apostrophes in prompts. Fields: `prompt`, `actorId`. `--session-id` must be ≥33 chars.

**Knowledge Base tool**: put docs in `$S3_BUCKET_NAME`, ask Kiro to create a KB (or `create_knowledge_base` for the sample). The runtime role needs `bedrock:Retrieve` on the KB ARN + `bedrock:RetrieveAndGenerate` on `"*"` via `additionalPolicies` (policy JSON under `app/agent/policies/`). Local invoke works without it (runs as participant) but deployed agent fails with AccessDenied.

Lab 1 checks:
```bash
grep -r "bedrock_agentcore.runtime" app/agent/*.py
grep -A2 '"memories"' agentcore/agentcore.json
grep -A3 envVars agentcore/agentcore.json
grep -A1 additionalPolicies agentcore/agentcore.json && grep -l 'bedrock:Retrieve' app/agent/policies/*.json
grep "global\." app/agent/model/load.py
```

### 5.2 Memory (Lab 2)
- `agentMemory` (SEMANTIC + EPISODIC, events expire 30 days). Deploy injects `MEMORY_AGENTMEMORY_ID` (`MEMORY_<NAME>_ID`).
- `app/agent/memory/session.py` builds `AgentCoreMemorySessionManager` (from `bedrock_agentcore.memory.integrations.strands`) with `retrieval_config` per namespace (`RetrievalConfig(top_k=…, relevance_score=…)`); `main.py` passes it to `Agent`, keyed by `session_id` (request context) and `actorId` (payload, default `default`).
- Lab tuning: facts `top_k` 3 → 5; system prompt "use remembered facts instead of asking again".
- No memory in project? `agentcore add memory --name agentMemory --strategies SEMANTIC,EPISODIC && agentcore deploy`.
- Inspect: `agentcore memory list --json`, `agentcore memory get --id <id>`, `agentcore memory record list --id <id> --namespace /users/<actor>/facts`, `agentcore memory event list --id <id> --actor-id <a> --session-id <s>`.
- Test: same `--session-id` = short-term; new session-id recalls via SEMANTIC (wait ~60 s).

### 5.3 Gateway tools (Lab 3)
```bash
agentcore add gateway --name ToolGateway --protocol-type MCP --authorizer-type NONE --exception-level debug
```
- Gateway name ≤ 12 chars (CDK composes `<project>_default_<gateway>` ≤ 48). `--protocol-type MCP` is mandatory and can't be changed later (else URL lacks `/mcp` → `McpError: Connection closed`; fix: set `agentCoreGateways` to `[]`, deploy, re-add).
- Targets in `agentcore.json` use `targetType: "lambdaFunctionArn"` (not `apiGateway` — AWS_PROXY Lambdas produce no valid OpenAPI → "responses is missing"):
```json
{ "name": "BillingTools", "targetType": "lambdaFunctionArn",
  "lambdaFunctionArn": { "lambdaArn": "arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:billing-mcp",
                         "toolSchemaFile": "billing-tools.json" } }
```
  Or `agentcore add gateway-target --gateway ToolGateway --target-configuration file://target.json`.
- Tool schema files live in the **project root** (next to `agentcore/` and `app/`): JSON array of `{name, description, inputSchema{type:object, properties, required}}`.
- CDK grants `lambda:InvokeFunction` to the gateway role and injects `AGENTCORE_GATEWAY_<NAME>_URL` (e.g. `AGENTCORE_GATEWAY_TOOLGATEWAY_URL`).
- `app/agent/mcp_client.py`:
```python
import os
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

def get_streamable_http_mcp_client() -> MCPClient | None:
    endpoint = os.environ.get("AGENTCORE_GATEWAY_TOOLGATEWAY_URL", "")
    if not endpoint:
        return None
    return MCPClient(lambda: streamablehttp_client(endpoint))
```
  In `_get_agent` (lazy, `@lru_cache`): `mcp_client.start(); agent_tools.extend(mcp_client.list_tools_sync())`. Tool names appear as `<Target>___<tool>`.
- Gateway sample backend: tools `get_billing_info`, `get_billing_history`, `create_ticket`, `query_tickets`, `update_ticket`, `escalate_to_human` (all take `customer_id`). 404 "Unknown path" → re-run `create_backend_systems`.

### 5.4 Identity scoping (Lab 4)
- Identity arrives as `actorId` in payload (template `parse.py` reads it; memory namespaces use it) or `agentcore invoke --user-id X` (header `X-Amzn-Bedrock-AgentCore-Runtime-User-Id`, not read by template). Production: `agentcore add runtime --authorizer-type CUSTOM_JWT` + `agentcore add credentials api-key|oauth`.
- Enforce with a Strands hook (`app/agent/scope.py`):
```python
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

class CustomerScopeHook(HookProvider):
    def __init__(self, actor_id: str) -> None:
        self.actor_id = actor_id
    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self._check_customer)
    def _check_customer(self, event: BeforeToolCallEvent) -> None:
        requested = (event.tool_use.get("input") or {}).get("customer_id")
        if requested and requested != self.actor_id:
            event.cancel_tool = (f"Access denied: this session is authenticated as {self.actor_id} "
                                 f"and cannot access data for {requested}.")
```
  Pass `hooks=[CustomerScopeHook(actor_id)]` to `Agent(...)` and add "The authenticated customer is {actor_id}. Never request another customer's data." to the system prompt. Denial must not end the conversation.

### 5.5 Observability (Lab 5)
- `instrumentation.enableOtel` is on by default (ADOT in deps). Add `{ "name": "UNIFIED_TRACES_DESTINATION_ENABLED", "value": "true" }` to the runtime `envVars`, redeploy.
- Traces appear 30–90 s after an invoke:
```bash
agentcore traces runtime list --since 15m
agentcore traces runtime get <trace-id>     # writes <trace-id>.json (spans: name, kind, durationNano, attributes)
agentcore logs runtime --tail               # live; or --since 15m
```
- Log group `/aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT`; CloudWatch **GenAI Observability** page shows the trace timeline. Spans: `invoke_agent Strands Agents`, `execute_event_loop_cycle`, `chat`, `execute_tool`, MCP tool spans.

### 5.6 Streaming chat UI + ECS Fargate (Lab 6)
UI guardrails: dir `~/environment/chat-ui/`, port **8888**, `GET /health` → 200, reads `AGENTCORE_ENDPOINT` (runtime ARN) + `AWS_REGION`, streams tokens incrementally, binds `0.0.0.0`, **relative paths** (works behind `/proxy/8888/`), `requirements.txt`, Docker-ready, keeps history on error.
```bash
agentcore status --json | jq -r '.resources[] | select(.resourceType=="runtime") | .arn'   # AGENTCORE_ENDPOINT
cd ~/environment/chat-ui && uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
curl http://localhost:8888/health ; python3 -m webbrowser $IDE_URL/proxy/8888/
```
ECS deploy requirements (or use skill `deploy-chat-ui-to-ecs`): Dockerfile (Python base, port 8888, HEALTHCHECK `/health`) → ECR repo `agent-chat-ui` → Fargate task def 512 CPU / 1024 MB, env `AGENTCORE_ENDPOINT` + `AWS_REGION`, task role allowed to invoke the AgentCore runtime → service on `$ECS_CLUSTER`, desired count 1, public IP, default VPC public subnets, SG inbound TCP 8888 → tag `Workshop=anycompany-telecom-agent` → done when task RUNNING and public `/health` healthy. Tasks cycling → usually port mismatch or health check failing.

---

## 6. Critical rules & gotchas

| Rule | Correct | Wrong / symptom |
|---|---|---|
| Model ID | Inference profile: `global.anthropic.claude-sonnet-<latest>` — discover with `aws bedrock list-foundation-models --by-provider Anthropic --query "modelSummaries[?modelLifecycle.status=='ACTIVE'].{id:modelId,name:modelName}" --output table --region us-east-1` and prefix `global.` | `anthropic.claude-...` → "on-demand throughput not supported"; don't hardcode stale IDs |
| Import | `from bedrock_agentcore.runtime import BedrockAgentCoreApp` | `from bedrock_agentcore import ...` → heavy import, 30 s init timeout |
| Entry point | Lazy agent init, `async` generator handler with `@app.entrypoint`, `app.run()` in `__main__`, read `prompt` + `actorId` | "Runtime initialization time exceeded (30s)" |
| Dependencies | Only runtime deps in `[project].dependencies`; pytest etc. in `[dependency-groups] dev` | No ARM64 wheel → "uv install failed for all platform candidates" |
| Platform | AgentCore Runtime = ARM64 Linux | x86-only packages fail |
| IAM | Extra AWS perms via runtime `additionalPolicies` in `agentcore.json` (managed ARN or JSON file relative to codeLocation) | `aws iam put-role-policy` (not allowed, lost on redeploy) |
| Observability | `UNIFIED_TRACES_DESTINATION_ENABLED=true` in runtime `envVars` | No traces in CloudWatch |
| Session id | ≥ 33 characters | "runtimeSessionId ... length greater than or equal to 33" |
| Gateway | `--protocol-type MCP`, name ≤ 12 chars, `lambdaFunctionArn` targets, schema files in project root | Connection closed / name > 48 / OpenAPI "responses is missing" / "Cannot find asset" |
| CLI flags | CLI 1.x `agentcore create` only accepts `--name`, `--template`, `--skip-install`, `--skip-git` | 0.x flags (`--framework`, `--memory`…) don't exist |
| CLI version | Stay on 1.0.3 | Don't update |
| Ports | 8081 dev, 8888 UI | Never touch 8080 (the IDE). Port busy: `lsof -ti:8081 \| xargs kill -9` |
| Failed first deploy | `aws cloudformation delete-stack --stack-name CDKToolkit && aws cloudformation wait stack-delete-complete --stack-name CDKToolkit; aws s3 rb "s3://cdk-hnb659fds-assets-${ACCOUNT_ID}-${AWS_REGION}" --force; agentcore deploy` | "CDKToolkit stack is in ROLLBACK_COMPLETE" / "StagingBucket already exist" |
| Marketplace | `enable_anthropic_models`, wait 2–6 min | Editing IAM roles |
| `agentcore status` / `memory list` | Interactive TUI: exit with `Ctrl+C` (Esc = filter); use `--json` in scripts/Kiro tool calls | Hanging tool call |
| Packaging check | `cd app/agent && uv sync && uv run python -c "import main"` | — |

---

## 7. AgentCore CLI quick reference

| Action | Command |
|---|---|
| Create | `agentcore create --name X --template agent-python-strands` |
| Local dev / invoke | `agentcore dev --port 8081` / `agentcore invoke --runtime agent --local --port 8081 --payload '{"prompt":"..."}'` |
| Deploy | `agentcore deploy` (`agentcore --debug deploy`) |
| Status | `agentcore status` (`--json`) |
| Invoke deployed | `agentcore invoke --runtime agent [--session-id <≥33 chars>] --payload '{"prompt":"...","actorId":"..."}'` |
| Logs | `agentcore logs runtime --tail` / `--since 15m` |
| Traces | `agentcore traces runtime list --since 15m` / `agentcore traces runtime get <id>` |
| Add resources | `agentcore add runtime|memory|gateway|gateway-target|credentials` |
| Memory | `agentcore memory list|get|record list|event list` |
| Remove all | `agentcore remove all --yes && agentcore deploy --yes` (stack removal up to 25 min) |

---

## 8. Troubleshooting prompts for Kiro
```
My deployed agent answers without using the Knowledge Base. Check the system prompt, the retrieval tool, and `agentcore logs runtime --since 15m` for the last invocation, and tell me why retrieval is not happening.
```
```
Use the aws-mcp and bedrock-agentcore-mcp-server tools to look up this error and explain how to fix it for an AgentCore Runtime agent: <error message>. Tell me which documentation page you used.
```
```
The chat UI loads, but every message returns an error. Check the UI server logs and the agent invocation, find where the request fails, and fix it.
```

---

## 9. Suggested hackathon game plan (supply chain)

1. **Setup (15 min):** open Kiro IDE Browser, run the verify block, confirm steering files, `mcp.json`, skills (`ls ~/environment/.kiro/steering ~/environment/.kiro/skills`; `/tools` in `kiro-cli chat`).
2. **Pick use case + inputs (20 min):** one-sentence use case + "must never", persona, documents, tool(s), project name. Supply-chain examples in the same shape as the official seeds:
   - *Inventory & Replenishment Assistant* — KB: SOPs, reorder policies; tool: `get_stock_levels` / `suggest_reorder` over mock JSON or DynamoDB; must never place orders without human approval.
   - *Supplier Risk Analyst* — KB: supplier contracts, audit reports; tool: `get_supplier_scorecard`; escalates high-risk suppliers.
   - *Shipment Exception Agent* — KB: carrier SLAs, incident runbooks; tools: `track_shipment`, `create_exception_ticket` (Gateway + Lambda).
3. **Upload docs** to `$S3_BUCKET_NAME` (`aws s3 cp ./docs s3://$S3_BUCKET_NAME/<folder>/ --recursive`).
4. **Spec (Quick Spec if short on time)** with the brief template + guardrails → review → execute task by task.
5. **Deploy + verify** (section 4 verify block) — get green early.
6. **Stretch** in order of demo value: Gateway tools → memory → identity scoping → chat UI on ECS → traces screenshot for the pitch.
7. **Demo:** show spec docs, live invoke/chat UI, a trace in CloudWatch GenAI Observability, and memory recall across sessions.
