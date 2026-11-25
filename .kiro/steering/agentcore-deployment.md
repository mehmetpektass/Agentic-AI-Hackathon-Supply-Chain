---
inclusion: always
---
# AgentCore Deployment Guide

Guide for deploying Python agents to Amazon Bedrock AgentCore using the official AgentCore CLI (`@aws/agentcore`).

## Prerequisites
- Node.js 20.12+ installed (the CLI is an npm package)
- Python 3.10+ installed
- uv installed (the CLI runs uv sync in the runtime code directory)
- AWS CDK installed (npm install -g aws-cdk)
- AgentCore CLI 1.0.3 installed (npm install -g @aws/agentcore@1.0.3)
- AWS credentials configured with Bedrock and AgentCore access

## Model Access (Anthropic models need a one-time account agreement)

Anthropic models on Bedrock are sold through AWS Marketplace. The first invocation in an account only succeeds for a principal that holds aws-marketplace:Subscribe; the AgentCore runtime role does not, so a deployed agent fails with:
`AccessDeniedException: Model access is denied due to IAM user or service role is not authorized to perform the required AWS Marketplace actions`

The agreement is account-level and one-time. The workshop bootstrap accepts it for every active Anthropic model when the team account is prepared, so normally nothing is needed. If a deployed agent returns the error above, run this once from the IDE terminal (it uses the participant role, which has the Marketplace permissions, and skips models already enabled), then wait 2 to 6 minutes for the agreement to propagate and invoke again:

enable_anthropic_models

Do NOT add aws-marketplace permissions to the runtime execution role and do NOT edit IAM roles to work around this error; the agreement is the fix.

### How to discover the latest available model

aws bedrock list-foundation-models --by-provider Anthropic \
  --query "modelSummaries[?modelLifecycle.status=='ACTIVE'].{id:modelId,name:modelName}" \
  --output table --region us-east-1

Use the model ID from that list with the global. inference profile prefix (for example global.anthropic.claude-sonnet-5-5). The participant role cannot call bedrock:ListInferenceProfiles, so do not try to list inference profiles; prefix the foundation model ID instead.

## MANDATORY: Agent Project Scaffolding

When asked to build an agent, you MUST FIRST run the AgentCore CLI to scaffold the project before writing any agent code. This is non-negotiable, do NOT create project structure manually.

Use the framework the participant names. If none is named, use Strands.

### Required Command (Strands, the guided default)
Use the name the participant gives you; the workshop's guided sample uses CustomerServiceAgent.
agentcore create --name <YourAgentName> --template agent-python-strands

This creates <YourAgentName>/ with the runtime named `agent` in app/agent/ (main.py, parse.py, model/load.py, memory/session.py, pyproject.toml), installs dependencies (npm install, uv sync), initializes git, and declares an AgentCore Memory named `agentMemory` (SEMANTIC and EPISODIC strategies) in agentcore/agentcore.json. Keep that memory: Lab 2 inspects and tunes it.

### LangGraph variant
agentcore create --name <YourAgentName> --template agent-python-langchain

This creates <YourAgentName>/ with the runtime named `agent` in app/agent/ (main.py, model/load.py, pyproject.toml): Bedrock only, no memory, LangChain 1.x `create_agent` with an InMemorySaver checkpointer keyed on the Runtime session id, and opentelemetry-instrumentation-langchain already in the dependencies. Follow langgraph-agent-coding.md for the code.

### Bring your own code variant
agentcore create --name <YourAgentName>
cd <YourAgentName>
agentcore add runtime --name <YourAgentName> --language python --protocol HTTP

Without `--template`, `agentcore create` makes an empty project: agentcore/agentcore.json with no runtime. `agentcore add runtime` registers app/<YourAgentName>/ as the runtime code directory (build CodeZip, entrypoint main.py) and writes README.md and AGENTS.md there; it generates no code and overwrites nothing. Copy the existing code into app/<YourAgentName>/ with a main.py that exposes a `BedrockAgentCoreApp` HTTP server (see Agent Code Requirements) and a pyproject.toml whose [project].dependencies list the runtime dependencies. The runtime is then named <YourAgentName>: use `--runtime <YourAgentName>` instead of `--runtime agent` in the invoke commands below.

The CLI 0.x create flags (defaults, framework, model-provider, memory, build) do not exist in CLI 1.x; `agentcore create` accepts only `--name`, `--template`, `--skip-install` and `--skip-git`.

## Development Workflow

### Step 1: Create the Project
agentcore create --name <YourAgentName> --template agent-python-strands
cd <YourAgentName>
(LangGraph and own-code projects: use the matching variant from the scaffolding section above.)

### Step 2: Test Locally
Terminal 1 (serves the runtime on port 8081, headless):
agentcore dev --port 8081

Terminal 2 (sends one request to the local server):
agentcore invoke --runtime agent --local --port 8081 --payload '{"prompt":"Tell me a joke"}'

### Step 3: Deploy to AgentCore Runtime
agentcore deploy

The first deploy creates the default target from the account and region, bootstraps CDK and enables CloudWatch Transaction Search; it takes 5 to 8 minutes, later deploys about 5 minutes. Use `agentcore --debug deploy` for verbose output.

### Step 4: Test Deployed Agent
agentcore invoke --runtime agent --payload '{"prompt":"Tell me a joke"}'
agentcore invoke --runtime agent --session-id my-first-session-anycompany-telecom-01 --payload '{"prompt":"Hello"}'
agentcore invoke --runtime agent --payload '{"prompt":"What is my plan?","actorId":"CUST-001"}'

The payload is JSON: `prompt` is the user message and `actorId` identifies the end user (it scopes memory namespaces and tool access). `--runtime agent` is the runtime name every template declares; for your own code, use the name you passed to `agentcore add runtime`. The response streams by default as raw `data: {...}` server-sent events (the text is in `contentBlockDelta.delta.text`), followed by one `status=200 ...` line. Reuse `--session-id` to continue a conversation; the value must be at least 33 characters (shorter values fail with `Value at 'runtimeSessionId' failed to satisfy constraint: Member must have length greater than or equal to 33`).

### Step 5: Check Status, Logs and Traces
agentcore status
agentcore logs runtime --tail
agentcore traces runtime list --since 15m

## Agent Code Requirements

The entry point (app/agent/main.py, or app/<YourAgentName>/main.py for your own code) must, whatever the framework:
1. Import from bedrock_agentcore.runtime (NOT from bedrock_agentcore directly)
2. Use lazy initialization of the agent or graph to avoid 30s cold start timeout
3. Use async generator handler with @app.entrypoint
4. Have app.run() in __main__
5. Read `prompt` and `actorId` from the payload (the Strands template's parse_payload does this; keep it, and mirror it in LangGraph or own code)

## Kiro IDE Browser Users: Accessing the Local Dev Server

Always start the local dev server with `agentcore dev --port 8081`. Port 8080 is used by the Kiro IDE Browser itself and must not be reused or stopped.

`agentcore dev --port 8081` is headless: test it from a second terminal with `agentcore invoke --runtime agent --local --port 8081 --payload '{"prompt":"..."}'`. The optional Agent Inspector (`agentcore dev --mode browser --port 8081 --ui-port 8082`) is untested behind the IDE `/proxy/<port>/` path, so prefer headless dev plus local invoke. Participants using Kiro IDE locally can open `http://localhost:8082` directly when they use browser mode.

## Critical Rules

### Model IDs must use inference profile format
- Correct: global.anthropic.claude-sonnet-4-6 (prefixed with an inference profile scope such as global. or us.)
- Wrong: anthropic.claude-sonnet-4-6 (fails with "on-demand throughput not supported")
- Always discover the latest model ID first: do NOT hardcode stale model IDs

### Import path matters for cold start
- Correct: from bedrock_agentcore.runtime import BedrockAgentCoreApp
- Wrong: from bedrock_agentcore import BedrockAgentCoreApp (pulls heavy modules, times out)

### pyproject.toml: runtime deps only
The file is app/agent/pyproject.toml (app/<YourAgentName>/pyproject.toml for your own code). Only include runtime packages in [project].dependencies. Do NOT put dev/test dependencies there, they may lack ARM64 wheels and break the build. Test tools such as pytest belong in a [dependency-groups] dev table: uv sync installs them locally and the CodeZip build excludes them (uv export --no-default-groups).

### Runtime role permissions: declare them in the project, never by hand
The runtime role the CLI creates grants bedrock:InvokeModel*, bedrock:CountTokens and the memory actions only. Any other AWS API the agent's tools call (bedrock:Retrieve on the Knowledge Base ARN plus bedrock:RetrieveAndGenerate on "*" for a Knowledge Base tool, DynamoDB, S3, and so on; an action with no IAM resource type only matches Resource "*") must be granted through the runtime's additionalPolicies list in agentcore/agentcore.json: each entry is a managed policy ARN or a JSON policy document path relative to the runtime's codeLocation (for example policies/knowledge-base-retrieve.json under app/agent/), attached on the next agentcore deploy. Do NOT run aws iam put-role-policy on the runtime role: the participant role cannot, and a manual grant is lost on redeploy. Without the grant the deployed agent fails with AccessDeniedException on the tool call while local invokes, which run as the participant role, still work.

### ARM64 constraint
AgentCore Runtime runs on ARM64 (Graviton). Any dependency without a pre-built ARM64 Linux wheel will fail.

### Observability (CloudWatch traces)
ALWAYS keep `UNIFIED_TRACES_DESTINATION_ENABLED` set to `true` as an entry in the runtime's `envVars` list in `agentcore/agentcore.json`:

"runtimes": [
  {
    "name": "agent",
    "...": "...",
    "envVars": [
      { "name": "UNIFIED_TRACES_DESTINATION_ENABLED", "value": "true" }
    ]
  }
]

Tracing instrumentation (`instrumentation.enableOtel`) is on by default and aws-opentelemetry-distro is already a dependency; without this variable spans are not exported to the agent's CloudWatch log group. The agent works but has no observability visible in the console.

Enable CloudWatch Transaction Search in your account and send trace segments to Amazon CloudWatch Logs. Without Transaction Search, AgentCore cannot deliver spans to the agent's log group. For more information, see [Enabling CloudWatch Transaction Search](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-configure.html#observability-configure-builtin-cw).

## CLI Commands Reference

| Action | Command |
| ------ | ------- |
| Create project | agentcore create --name X --template agent-python-strands (LangGraph: --template agent-python-langchain; own code: no --template, then agentcore add runtime --name X --language python --protocol HTTP) |
| Local dev server | agentcore dev --port 8081 |
| Invoke local | agentcore invoke --runtime agent --local --port 8081 --payload '{"prompt":"..."}' |
| Deploy | agentcore deploy |
| Check status | agentcore status (interactive tree in a terminal; agentcore status --json for scripts and tools) |
| Invoke deployed | agentcore invoke --runtime agent --payload '{"prompt":"..."}' |
| Stream logs | agentcore logs runtime --tail |
| List traces | agentcore traces runtime list |
| Add resources | agentcore add [runtime|memory|gateway|gateway-target|credentials] (gateways: --protocol-type MCP, name 12 characters or fewer) |
| Remove everything | agentcore remove all --yes, then agentcore deploy --yes (stack removal takes up to 25 minutes) |

## Troubleshooting

| Error | Fix |
| ----- | --- |
| Runtime initialization time exceeded (30s) | Use lazy init pattern with from bedrock_agentcore.runtime import |
| runtimeSessionId ... length greater than or equal to 33 | Use a --session-id of at least 33 characters |
| Gateway name is N characters long but must be <= 48 | The CDK composes <project>_default_<gateway>; use a gateway name of 12 characters or fewer |
| MCPClientInitializationError / McpError: Connection closed | The gateway was added without --protocol-type MCP; its URL lacks /mcp. Remove it, deploy, re-add with --protocol-type MCP |
| Model ID on-demand throughput not supported | Prefix model ID with region: global.anthropic.claude-sonnet-4-6 |
| uv install failed for all platform candidates | Dependency lacks ARM64 wheel, remove from runtime deps |
| Permission denied | Verify aws sts get-caller-identity and IAM policies |
| CDK deployment errors | Run agentcore --debug deploy for the CDK output; the first deploy bootstraps CDK itself |
| Port 8081 in use (agentcore dev) | lsof -ti:8081 \| xargs kill -9 or use agentcore dev --port 8082. Never stop a process on port 8080, the IDE uses it |
