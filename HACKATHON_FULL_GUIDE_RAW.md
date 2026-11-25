# Full workshop text — Ship Production Agents on Amazon Bedrock AgentCore with Kiro

> Raw text of every page (Getting Started → Conclusion), scraped 2026-11-24. Curated summary: HACKATHON_KIRO_CONTEXT.md

---

<!-- page: 00_getting-started -->
# Getting Started

Before You Start
Each team account comes with a Kiro IDE Browser, a Kiro IDE served from your web browser and already signed in with your team's Kiro API key. You only need a modern web browser; every tool the labs use is pre-installed except AI-DLC, which you install at the start of the Lab 7 Build with AI-DLC page.
Complete these pages in order:

| Step | Page | What you do |
| 1 | AWS Event Setup | Join the event, open the URL output, and verify the tools in the Kiro IDE Browser terminal |
| 2 | Kiro IDE Browser | Open the IDE, meet the chat panel and terminal, and confirm Kiro is signed in |
| 3 | Steering, Skills and MCP Servers | Configure the steering files, verify the pre-provisioned skills, and set up the MCP servers that guide Kiro during the labs |

Once you finish Step 3, pick your path below.
Pick Your Path
The workshop has two parts and you choose where to spend your time. Both paths use the same team account, tools, and steering files, so a team can start on one and switch to the other.

- 
- 

For teams new to Amazon Bedrock AgentCore or to Kiro, and for anyone who wants each building block explained before an open build.

You build the AnyCompany Telecom customer service agent one capability at a time across Labs 1 to 6: agent creation and deployment, memory, Gateway tools, identity scoping, observability, and a chat UI on Amazon ECS. Each lab is a set of challenges with a goal and guardrails. You build each challenge your own way with Kiro Specs, with the guided Kiro skill (type `/` in chat), or with a Quick Spec seeded from the sample brief; all three converge on the same result.

- Time: about 2 hours for Labs 1 to 6 
- Start: Lab 1: Build Your Agent 
- Afterwards: continue to Lab 7 in the same account if your event has time, or go to Cleanup 

Treat Part 1 as the enablement for Lab 7: every capability you add to the sample agent is one you can add to your own agent later, and Lab 7 links back to the lab that shows how.

Troubleshooting With Kiro
When you get stuck on a lab, Kiro is your first troubleshooter. It runs commands in your terminal, reads your code and logs, inspects the resources in your team account, and looks up current documentation through the MCP servers you set up in Step 3. Your job is to give it the problem with enough context and ask it to investigate before it changes anything.
For a stubborn problem, open a new session and choose Bug Fix under Start with a built-in agent. It takes Kiro through investigation, diagnosis, and resolution as separate steps you review, instead of jumping straight to an edit.
Prompts to adapt
The agent runs but behaves wrong:

```
My deployed agent answers billing questions without using the Knowledge Base. Check the system prompt, the retrieval tool, and `agentcore logs runtime --since 15m` for the last invocation, and tell me why retrieval is not happening.
```

An error you do not recognize:

```
Use the aws-mcp and bedrock-agentcore-mcp-server tools to look up this error and explain how to fix it for an AgentCore Runtime agent: <error message>. Tell me which documentation page you used.
```

A chat UI problem:

```
The chat UI loads, but every message returns an error. A screenshot is attached. Check the UI server logs and the agent invocation, find where the request fails, and fix it.
```

---

<!-- page: 01_getting-started__aws-event -->
# AWS Event Setup

Running the Workshop at an AWS Event
To complete this workshop, you are provided with an AWS account via Workshop Studio. Each team account has pre-provisioned infrastructure: the Kiro IDE Browser, an S3 bucket for knowledge base documents, and an ECS cluster. The Kiro IDE Browser is your development environment. It serves the Kiro IDE and Kiro CLI from your browser, already signed in to Kiro with a team API key, so there is no password to enter and no Kiro account to sign in with. The goal of this section is to help you open the IDE and confirm the workshop toolchain is ready.
Access Your Workshop Environment
 
- Open a Chrome or Firefox browser and navigate to the Workshop Studio event page provided by the event host. 
Open Event Dashboard
 
- Choose Email One-Time Password (OTP) and enter your email address. 

 
- Enter your email address and the event access code from the event host (a 12-character code with dashes). 
 
 
- When the login is successful, you will see the Review and Join page. Review terms and click Join event. 

 
- Scroll down to the Event Outputs table. You will find the following values there: 

| Output | Stack | Description |
| URL | kiro-ide-browser | URL to open the Kiro IDE Browser |
| S3BucketName | workshop-team-stack | Workshop S3 bucket, pre-loaded with a copy of the AnyCompany Telecom documents; Lab 7 teams upload their own documents here (create_knowledge_base in Lab 1 uses a bucket of its own) |
| EcsClusterArn | workshop-team-stack | ECS cluster for deploying the chat UI in Lab 6 |

 
- Copy the value of the URL output (from the `kiro-ide-browser` stack) and open it in a new browser tab. On first load the IDE asks Do you trust the remote host '.cloudfront.net'?. This is the IDE asking whether its own extensions may run, not a Kiro sign-in: tick Always trust this remote host and choose Trust and Connect. The Kiro IDE then opens with `~/environment` as the workspace folder. There is no password prompt and no Kiro sign-in: the IDE and the Kiro CLI are already authenticated. 

No sign-in needed

The Kiro IDE Browser is pre-authenticated for your team, so you never sign in to Kiro during this workshop. If you see a Kiro sign-in prompt, contact the event facilitator. Two messages are expected and need no action: the remote host trust dialog above (if you chose Don't Connect, reload the tab to get it again) and a warning that more than 50 MCP tools are enabled, which comes from the AWS MCP servers pre-installed in the IDE; dismiss it.

 
- Once the IDE has loaded, open a terminal with the shortcut `Ctrl+Shift+`` (Control, Shift and backtick). You can also open the menu (hamburger icon at the top left), choose Terminal, then New Terminal. The terminal starts in `~/environment`. This is what you will use during this workshop to run commands. 
- After returning to your Event Dashboard, click the link on the left navigation column to access the AWS console. This will open your temporary AWS account in a new browser tab. 

Verify Your Environment
Run each command in the IDE terminal, without `sudo`, and compare the output with the expected result:

| Tool | Command | Expected result |
| Node.js | node --version | v20.x.x or later (minimum version 20) |
| Python | python3 --version | Python 3.10.x or later (minimum version 3.10) |
| AWS CLI | aws --version | aws-cli/2.x.x (minimum version 2) |
| AWS CDK CLI | cdk --version | 2.x.x (minimum version 2) |
| AgentCore CLI | agentcore --version | 1.0.3 (the labs are written for this version) |
| Kiro CLI | kiro-cli --version | A printed version string |
| uv | uv --version | A printed version string |
| uvx | uvx --version | A printed version string |
| git | git --version | A printed version string |
| jq | jq --version | A printed version string |
| Docker Engine | docker --version | A printed version string, without sudo |
| Docker Buildx | docker buildx version | A printed version string, without sudo |
| Docker daemon | docker ps | An empty container list, without sudo |
| AWS identity | aws sts get-caller-identity | Your team account ID and the assumed role ARN |

You can paste the whole block below to run every check at once (the output is long, so scroll up to see the first lines):

```
node --version
python3 --version
aws --version
cdk --version
agentcore --version
kiro-cli --version
uv --version
uvx --version
git --version
jq --version
docker --version
docker buildx version
docker ps
aws sts get-caller-identity
```

The toolchain pins AgentCore CLI 1.0.3 and every command in the labs is written for that version. Do not run `agentcore update` or `npm update -g @aws/agentcore` during the event.

If a check fails

If any command is not found, needs `sudo`, or reports a version below the minimum, contact the event facilitator. All tools are installed before your team account is handed to you, so there is nothing to wait for or install yourself.

Verify Environment Variables
Confirm the workshop environment variables are set:

```
echo "AWS Region: $AWS_REGION"
echo "Account ID: $ACCOUNT_ID"
echo "S3 Bucket: $S3_BUCKET_NAME"
echo "ECS Cluster: $ECS_CLUSTER"
echo "IDE URL: $IDE_URL"
```

Each line should print a non-empty value. If one is empty, open a new terminal and run the commands again. If it is still empty, contact the event facilitator.
`IDE_URL` is the address of your Kiro IDE Browser; later labs use `python3 -m webbrowser $IDE_URL/proxy/<port>/` to open local dev servers through the IDE's port proxy.

Ready to Go

Once all verifications pass, you are ready to configure Kiro for the labs. The Knowledge Base is created at the start of Lab 1.

Next Steps
Everything you need for this workshop is already in the browser. Proceed to Kiro IDE Browser to open the IDE, meet the chat panel and terminal, and confirm Kiro is signed in.

---

<!-- page: 02_getting-started__kiro-ide-browser -->
# Kiro IDE Browser

Your Development Environment
The Kiro IDE Browser is the Kiro IDE served from your web browser. It runs on an instance in your team's AWS account and is already signed in to Kiro with a team API key, so there is no Kiro account to create, no sign-in prompt, and nothing to install on your laptop. Your workshop files live in the `~/environment` workspace, which opens automatically.
To open it, copy the URL value from the Workshop Studio Event Outputs table (see AWS Event Setup) and paste it into a new browser tab.

Finding your way around

| Area | Where | What it is for |
| Explorer | Left sidebar | The files in your ~/environment workspace. Your agent project folder (CustomerServiceAgent/ for the guided sample) appears here after Lab 1 |
| Kiro chat panel | Right side | Describe what you want in plain English. Kiro reads and edits the files in your workspace, runs commands, and explains what it did |
| Terminal | Bottom of the editor | A bash shell on the instance, already in ~/environment, running as the participant user. Open it with Ctrl+Shift+` or Menu > Terminal > New Terminal |
| Editor | Centre | Opens files from the Explorer or from Kiro's chat responses. The welcome page lists the keyboard shortcuts |

Opening local web apps
The IDE proxies any local port under `/proxy/<port>/` on the same URL. The quickest way to open one from the terminal is `python3 -m webbrowser $IDE_URL/proxy/8888/` (8888 is the Lab 6 chat UI port). `agentcore dev --port 8081` serves the agent on 8081 without a web page; you test it with `agentcore invoke --local`, and the optional Agent Inspector from `agentcore dev --mode browser` is untested behind the proxy. Port 8080 is the IDE itself, so never reuse it.

Kiro is already signed in

The Kiro IDE and the Kiro CLI inside it are pre-authenticated for your team. You never sign in to Kiro during this workshop. If either one asks you to sign in, do not log in with your own account; contact the event facilitator.

Step 1: Two Ways to Talk to Kiro
You can use either interface during the labs. Both read the same workspace and the same steering files, so pick whichever you prefer and switch at any time.
The Kiro chat panel
The chat panel on the right is the quickest way to work. Type a request into Ask a question or describe a task, press Enter, and Kiro works directly in your `~/environment` files. The panel shows every file it reads or edits and every command it runs.
 
- Autopilot (toggle at the bottom right of the panel) lets Kiro apply changes without asking for approval on each step. Leave it on for the labs unless you want to review every edit. 
- Use New Session (the `+` at the top of the panel) when you move to a new lab so earlier context does not get in the way. 
- Start with a built-in agent at the top of a new session offers Spec, Plan, Bug Fix, and Quick Spec. The build challenges use Spec and Quick Spec to turn your intent into requirements, design, and tasks before Kiro writes code ([Kiro Specs](https://kiro.dev/docs/specs/)); Bug Fix is useful when a lab step misbehaves (see Troubleshooting With Kiro on the Getting Started page). 
The Kiro CLI in the terminal
Kiro CLI gives you the same assistant inside the terminal. Start it from your workspace folder:

Run the command:

```
kiro-cli chat
```

Trust Workspace

The first time you start `kiro-cli chat` in a new directory you are asked to trust the workspace. Select Trust, continue so Kiro can read and write files in `~/environment`. Kiro CLI opens on its V3 interface; stay on it, the labs are written for V3.

Useful commands inside the chat:

| Command | What it does |
| /clear | Clear the current conversation |
| /model | Switch between the available AI models |
| /tools | List the tools available, including MCP servers |
| /quit | Close the Kiro session |
| /spec new <name> | Start a spec (requirements, design, tasks) in the terminal |

Step 2: Understand Your Workspace
The `participant:~/environment$` folder holds only a `.kiro/` folder right now: it carries the three pre-provisioned Kiro skills, and the steering files you create on the next page land there too. In Lab 1, when you ask Kiro to scaffold your agent with `agentcore create`, your agent project folder (`CustomerServiceAgent/` for the guided sample) appears next to it and shows up in the Explorer.

```
participant:~/environment$
└── .kiro/
    └── skills/        (pre-provisioned; steering/ is added on the next page)
```

Why participant:~/environment$?

Every lab assumes you are working from `participant:~/environment$`. The terminal opens there, the Kiro chat panel edits files there, and the steering files you create on the next page live there. Keep this folder open as your workspace for the whole workshop.

Optional: Kiro Powers

Kiro Powers are pre-packaged integrations that bundle MCP servers with extra context. If you prefer them to the manual MCP configuration on the next page, open the Powers panel from the left sidebar and install:

| Power | Purpose |
| Strands | Strands Agents SDK documentation and code generation |
| AWS AgentCore | AgentCore CLI deployment guidance and documentation |

Choose either Powers or the manual `mcp.json` configuration on the next page, not both. The steering files on the next page are needed in either case.

Step 3: Confirm Kiro Can Reach a Model
Before moving on, make sure Kiro can list models without asking you to sign in:

```
kiro-cli chat --list-models
```

You should see at least one model listed.

Ready

Kiro is installed, signed in, and pointed at your workspace. Continue to Steering Files and MCP Servers to give Kiro the context it needs for the labs.

---

<!-- page: 03_getting-started__steering-and-mcp -->
# Steering, Skills and MCP Servers

Run these commands in the Kiro IDE Browser terminal

Every command on this page runs in the terminal of your Kiro IDE Browser. The steering files and MCP servers you create here, together with the pre-provisioned skills, are read by both the Kiro chat panel and the Kiro CLI, so you only set them up once.

What Are We Setting Up?
Before you start building your agent, you need to give Kiro three things:
 
- Steering files: Text files that tell Kiro how to build and deploy your agent correctly. Think of them as a cheat sheet that Kiro reads before answering your questions. Kiro (CLI and IDE) reads every file in `.kiro/steering/*.md` in the workspace at the start of a session. 
- Skills: Reusable, task-specific playbooks that Kiro activates on demand. Each skill lives at `.kiro/skills/<name>/SKILL.md` and is auto-discovered by both the Kiro CLI and the Kiro IDE chat; you invoke one by typing `/` in chat or by making a natural-language request that matches its description. This workshop ships three pre-provisioned skills used by the guided-sample paths in Lab 1 and Lab 6, you do not create them. The difference from steering: steering is always-on context Kiro reads at the start of every session, while a skill is invoked for a specific task when you ask for it.

|  | Steering files | Skills |
| When it applies | Always on, read at the start of every Kiro session | On demand, invoked for one task |
| Location | .kiro/steering/*.md | .kiro/skills/<name>/SKILL.md |
| Typical use | Standing rules (model IDs, deploy patterns, guardrails) | A full build playbook for one challenge (Lab 1, Lab 6) | 
- MCP servers: Connections to AWS documentation so Kiro can look up the latest information about the tools you are using. This workshop uses:

| MCP Server | What it gives Kiro |
| AWS MCP Server | Search and read any AWS documentation, plus AWS API access |
| AWS Bedrock AgentCore MCP Server | AgentCore CLI deployment docs and patterns |
| Strands Agents MCP Server | Strands SDK reference for building agents |
| Amazon ECS MCP Server   (read-only) | ECS and Fargate guidance for the Lab 6 chat UI deployment |

The `aws-mcp` server configured below is the [Agent Toolkit for AWS](https://aws.amazon.com/products/developer-tools/agent-toolkit-for-aws/)'s AWS MCP Server; see [Getting started with the AWS MCP Server](https://docs.aws.amazon.com/agent-toolkit/latest/userguide/getting-started-aws-mcp-server.html) for what it can do beyond this workshop. 
Specs are the fourth piece, and the one you create yourself in each build challenge: see [Kiro Specs](https://kiro.dev/docs/specs/) and the Lab 1 Challenge 1 page. Nothing to set up now; steering files apply to every spec Kiro writes. Hooks are optional automation (a shell command or a prompt that runs when Kiro saves a file or uses a tool). The Accelerate boxes in Labs 1 and 6 show one. See [Kiro Hooks](https://kiro.dev/docs/hooks/).

Why do I need this?

Without steering and MCP servers, Kiro still works, but it may not know the latest AgentCore CLI commands or deployment patterns. These configurations make it more accurate and helpful for this specific workshop.

Prerequisites

The MCP servers run with `uvx`, which requires `uv` (Python package runner). The Kiro IDE Browser has it pre-installed; run `uvx --version` in the terminal to confirm.

Part 1: Create the Steering File
The steering file lives inside your workspace folder. Kiro reads it automatically every time you start a chat session from that folder.
Step 1: Create the folder structure
Run this in your terminal:

```
mkdir -p ~/environment/.kiro/steering
```

Step 2: Create the steering file
Copy and paste the entire block below into your terminal. It creates a file that teaches Kiro the correct AgentCore deployment patterns:

```
cat > ~/environment/.kiro/steering/agentcore-deployment.md << 'STEERING_EOF'
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
STEERING_EOF
```

Step 3: Create the Strands agent coding steering file
Copy and paste this block to create a second steering file that teaches Kiro how to structure Strands agent code:

```
cat > ~/environment/.kiro/steering/strands-agent-coding.md << 'STEERING_EOF'
---
inclusion: always
---
# Strands Agent Coding Guide - for building AI agents

### Agent Framework
- Strands Agents SDK: Python-based agent framework for building AI agents
- Use Strands' tool decorator pattern for defining agent tools
- Leverage Strands' built-in model support (Amazon Bedrock as the LLM provider)
- Follow Strands' agent loop pattern: prompt → model → tool use → response

### Infrastructure & Deployment
- Amazon Bedrock AgentCore: managed infrastructure for hosting and running the agent in production
- Deploy with `agentcore deploy`; the runtime is named `agent` in `agentcore/agentcore.json`
- Use AgentCore's built-in observability and scaling

### MCP Servers (Development Tooling)
- Strands MCP Server: used by Kiro to assist with building the agent code
- AgentCore MCP Server: used by Kiro to assist with deployment to AgentCore

### Language & Runtime
- Python 3.12+
- Use type hints throughout
- Follow PEP 8 style conventions
- Use pyproject.toml for dependency management

## Architecture Guidelines

### Agent Structure

This is the layout `agentcore create --template agent-python-strands` produces, plus the modules you add:

CustomerServiceAgent/
├── agentcore/
│   ├── agentcore.json           # Runtime `agent`, memory `agentMemory`, gateways, envVars
│   ├── aws-targets.json         # Deployment targets (filled on first deploy)
│   ├── .env.local               # Local-only environment variables (gitignored)
│   └── cdk/                     # CDK app the CLI deploys
├── app/
│   └── agent/
│       ├── main.py              # Agent entry point (AgentCore handler, lazy _get_agent)
│       ├── parse.py             # Payload parsing (prompt, messages, actorId)
│       ├── model/
│       │   └── load.py          # Bedrock model client (inference profile ID)
│       ├── memory/
│       │   └── session.py       # AgentCore Memory session manager
│       ├── tools/               # Strands tool definitions you add
│       │   ├── __init__.py
│       │   └── retrieval.py     # Knowledge base retrieval tool
│       ├── prompts/
│       │   └── system_prompt.py # System prompt for customer service
│       ├── tests/               # pytest tests (pytest goes in [dependency-groups] dev)
│       └── pyproject.toml       # Runtime dependencies only in [project].dependencies
└── .gitignore

## Development Standards

### Code Patterns
- Define tools using @tool decorator from Strands SDK
- Use Pydantic models for input/output validation
- Keep the system prompt in a separate module for maintainability
- Handle edge cases: empty input, missing customer data, API failures

### Testing
- Unit tests for tool functions
- Integration tests with sample customer queries
- Test all tool paths (retrieval, billing, ticketing, escalation)
- Validate structured output schema compliance

### Deployment
- Package the agent for AgentCore deployment using agentcore deploy
- Use lazy initialization pattern to avoid cold start timeouts
- Configure appropriate timeout values for LLM inference
- Set up logging for audit trail of customer interactions
STEERING_EOF
```

Step 3b (optional): Use LangGraph instead of Strands
Run this step only if your team brings a LangGraph agent or its own code to Lab 7. Labs 1 to 6 and the Lab 1 guided skill (`build-customer-service-agent`) assume Strands, so do not run it if you plan to run that skill or to follow Part 1 first; you can come back to it right before Lab 7.
The block removes the Strands coding file and creates the LangGraph coding file in its place. The two must not both be present: Kiro would read conflicting rules and steer your code back to Strands.

```
rm -f ~/environment/.kiro/steering/strands-agent-coding.md
cat > ~/environment/.kiro/steering/langgraph-agent-coding.md << 'STEERING_EOF'
---
inclusion: always
---
# LangGraph Agent Coding Guide - for building AI agents

### Agent Framework
- LangGraph: build the agent as a `StateGraph` over a `TypedDict` state; `MessagesState` from langgraph.graph is the ready-made state with a `messages` list
- Nodes are plain functions that take the state and return only the keys they update
- Use explicit edges (`add_edge`) for a fixed flow and conditional edges (`add_conditional_edges`) for routing, for example model to tools or to END
- Compile the graph once (`builder.compile()`) and reuse the compiled graph for every request
- The `agent-python-langchain` template's main.py uses `langchain.agents.create_agent`, which returns a compiled graph; keep it for a plain tool-calling loop and move to your own `StateGraph` when the flow needs custom nodes or routing

### Model
- `ChatBedrockConverse` from langchain_aws with an inference-profile model ID, for example global.anthropic.claude-sonnet-4-6; discover the latest ID first (see agentcore-deployment.md), do NOT hardcode a stale one
- The template's model/load.py uses `init_chat_model(MODEL_ID, model_provider="bedrock_converse")`, which returns the same class
- Other providers go through their LangChain chat model classes (for example `ChatAnthropic`, `ChatOpenAI`) with the API key stored as an AgentCore credential (`agentcore add credentials api-key`)

### Tools
- Define tools with the `@tool` decorator from langchain_core.tools; the docstring is required, it becomes the tool description
- Attach them with `model.bind_tools(tools)` and execute them with `ToolNode(tools)` from langgraph.prebuilt
- Route with `tools_condition` from langgraph.prebuilt: it sends the flow to the "tools" node when the model returned tool calls, otherwise to END
- AgentCore Gateway tools arrive over MCP: use `MultiServerMCPClient` from langchain_mcp_adapters.client with `{"transport": "streamable_http", "url": os.environ["AGENTCORE_GATEWAY_<NAME>_URL"]}` (NAME is the gateway name in upper case); `await client.get_tools()` once, on the first request inside the async entrypoint, and pass the result to `bind_tools` and `ToolNode`

### AgentCore Entry Point
- `from bedrock_agentcore.runtime import BedrockAgentCoreApp` (never from bedrock_agentcore directly)
- Build the graph lazily: a module-level `_graph = None` and a `get_graph()` that compiles on first call, so the process is ready in under 30 seconds
- The handler is an async generator decorated with `@app.entrypoint`; it reads `prompt` from the payload and streams the events of `graph.astream_events(..., version="v2")` back with `yield`
- Use `context.session_id` as the checkpointer `thread_id` in `config={"configurable": {...}}`, so one Runtime session is one conversation thread
- `app.run()` under `if __name__ == "__main__":`

Minimal main.py (lazy graph init and streaming entrypoint):

    from bedrock_agentcore.runtime import BedrockAgentCoreApp
    from langchain_aws import ChatBedrockConverse
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode, tools_condition

    from tools.portfolio import get_portfolio_summary

    MODEL_ID = "global.anthropic.claude-sonnet-4-6"  # discover the latest ID first
    app = BedrockAgentCoreApp()
    _graph = None

    def get_graph():
        global _graph
        if _graph is None:
            tools = [get_portfolio_summary]
            model = ChatBedrockConverse(model_id=MODEL_ID).bind_tools(tools)
            builder = StateGraph(MessagesState)
            builder.add_node("model", lambda state: {"messages": [model.invoke(state["messages"])]})
            builder.add_node("tools", ToolNode(tools))
            builder.add_edge(START, "model")
            builder.add_conditional_edges("model", tools_condition)
            builder.add_edge("tools", "model")
            _graph = builder.compile(checkpointer=InMemorySaver())
        return _graph

    @app.entrypoint
    async def invoke(payload, context):
        prompt = payload.get("prompt", "")
        config = {"configurable": {"thread_id": context.session_id or "default-session"}}
        inputs = {"messages": [{"role": "user", "content": prompt}]}
        async for event in get_graph().astream_events(inputs, config, version="v2"):
            yield event

    if __name__ == "__main__":
        app.run()

### Memory
- `InMemorySaver` (as in the main.py above) keeps conversation history for the life of the process only
- To keep state across sessions in AgentCore Memory, declare a memory (`agentcore add memory --name agentMemory`, then `agentcore deploy`) and use `AgentCoreMemorySaver(os.environ["MEMORY_AGENTMEMORY_ID"])` from langgraph_checkpoint_aws as the checkpointer, with `actor_id` next to `thread_id` in `configurable`
- Read the end-user identity from `actorId` in the payload, as the Strands template's parse.py does, and pass it as `actor_id`

### Infrastructure & Deployment
- Amazon Bedrock AgentCore: managed infrastructure for hosting and running the agent in production
- Deploy with `agentcore deploy`; the runtime is named `agent` in `agentcore/agentcore.json` (or the name you passed to `agentcore add runtime`)
- Use AgentCore's built-in observability and scaling

### MCP Servers (Development Tooling)
- LangChain documentation MCP servers (docs-langchain, reference-langchain): used by Kiro to look up LangChain and LangGraph APIs
- AgentCore MCP Server: used by Kiro to assist with deployment to AgentCore

### Language & Runtime
- Python 3.12+
- Use type hints throughout
- Follow PEP 8 style conventions
- Use pyproject.toml for dependency management

## Architecture Guidelines

### Agent Structure

This is the layout `agentcore create --template agent-python-langchain` produces (runtime `agent`), plus the modules you add. Your own code registered with `agentcore add runtime --name <YourAgentName>` lives in app/<YourAgentName>/ with the same shape:

<YourAgentName>/
├── agentcore/
│   ├── agentcore.json           # Runtime `agent`, memories, gateways, envVars
│   ├── aws-targets.json         # Deployment targets (filled on first deploy)
│   ├── .env.local               # Local-only environment variables (gitignored)
│   └── cdk/                     # CDK app the CLI deploys
├── app/
│   └── agent/
│       ├── main.py              # Entry point (BedrockAgentCoreApp, lazy get_graph)
│       ├── graph.py             # StateGraph definition and compile
│       ├── nodes/               # One module per node function
│       ├── tools/               # LangChain @tool definitions and the MCP client
│       ├── prompts/
│       │   └── system_prompt.py # System prompt
│       ├── model/
│       │   └── load.py          # Bedrock chat model (inference profile ID)
│       ├── tests/               # pytest tests (pytest goes in [dependency-groups] dev)
│       └── pyproject.toml       # Runtime dependencies only in [project].dependencies
└── .gitignore

### Dependencies
Runtime dependencies in [project].dependencies of app/agent/pyproject.toml (all of them ship py3-none-any wheels, so they install on ARM64):
- langgraph, langchain, langchain-core, langchain-aws
- bedrock-agentcore
- aws-opentelemetry-distro, opentelemetry-instrumentation-langchain
- langchain-mcp-adapters, only when the agent calls Gateway tools
- langgraph-checkpoint-aws, only when the checkpointer is AgentCore Memory
Keep pytest and other dev tools in [dependency-groups] dev.

## Development Standards

### Code Patterns
- Keep each node small and pure: read from the state, return the updated keys
- Use Pydantic models for tool input/output validation
- Keep the system prompt in a separate module for maintainability
- Handle edge cases: empty input, missing data, API failures

### Observability
- ALWAYS keep `UNIFIED_TRACES_DESTINATION_ENABLED` set to `true` as an entry in the runtime's `envVars` list in `agentcore/agentcore.json` (see agentcore-deployment.md)
- LangChain and LangGraph spans (model calls, tool calls, graph nodes) are captured by opentelemetry-instrumentation-langchain under the ADOT distro the Runtime starts; no code change is needed

### Testing
- Unit test each node function and each tool with a fixed input state
- One integration test that invokes the compiled graph with a sample prompt and checks the final message
- Validate structured output schema compliance

### Deployment
- Package the agent for AgentCore deployment using agentcore deploy
- Use lazy initialization pattern to avoid cold start timeouts
- Configure appropriate timeout values for LLM inference
- Set up logging for audit trail of user interactions
STEERING_EOF
```

Step 4: Verify the files were created

```
ls ~/environment/.kiro/steering/
```

You should see `agentcore-deployment.md` and `strands-agent-coding.md` listed (or `langgraph-agent-coding.md` in place of the Strands file if you ran Step 3b).

What do these steering files do?

When you run `kiro-cli chat` from `~/environment/`, Kiro automatically reads these files. They tell Kiro:

agentcore-deployment.md:

- Which AgentCore CLI 1.0.3 commands to use for creating, deploying and invoking agents 
- That it MUST scaffold projects with the AgentCore CLI (never by hand): `agentcore create --template agent-python-strands` by default, the `agent-python-langchain` template when you name LangGraph, or `agentcore add runtime` for code you bring 
- The correct model ID format (a common source of errors) 
- The correct import path to avoid cold start timeouts 
- The `envVars` entry that routes traces to CloudWatch 
- How to troubleshoot common deployment failures 

strands-agent-coding.md:

- How to structure a Strands agent project 
- The `@tool` decorator pattern for defining tools 
- That Python 3.12+ with type hints is required 
- The expected project layout for this workshop (runtime code in `app/agent/`) 

langgraph-agent-coding.md (optional, created in Step 3b in place of the Strands file):

- How to structure a LangGraph agent: a `StateGraph` with nodes, edges and a compiled graph built lazily inside the AgentCore entry point 
- LangChain `@tool`, `ToolNode` and `tools_condition` for tools, and `MultiServerMCPClient` for Gateway tools 
- The runtime dependency list that installs on ARM64, and the same observability rule as the Strands file 

You do not need to remember any of this. Kiro will follow these rules automatically when you ask it to build and deploy your agent.

Part 2: Configure MCP Servers
MCP servers connect Kiro to external documentation. With these configured, Kiro can look up the latest AWS, Strands SDK, and AgentCore information while helping you build.
What each server provides

| MCP Server | What it gives Kiro |
| aws-mcp | Search and read any AWS documentation, plus AWS API access |
| strands-agents | Strands SDK reference for building agents |
| bedrock-agentcore-mcp-server | AgentCore CLI deployment docs and patterns |
| awslabs.ecs-mcp-server | Read-only ECS and Fargate guidance for Lab 6 |

LangGraph users (optional)

If you ran Step 3b, add the two documentation servers that LangChain hosts, so Kiro can look up LangChain and LangGraph APIs while it builds. They use the remote-server form of `mcp.json`; add them inside `mcpServers` in `~/.kiro/settings/mcp.json`, next to the existing entries:

```
"docs-langchain": { "url": "https://docs.langchain.com/mcp" },
"reference-langchain": { "url": "https://reference.langchain.com/mcp" }
```

Both servers are documented at [Use these docs with your AI tools](https://docs.langchain.com/use-these-docs). Leave `strands-agents` in place; Kiro only uses it when it writes Strands code.

Step 1: Verify the configuration file
View the pre-configured server definitions:

```
cat ~/.kiro/settings/mcp.json
```

You should see all four servers defined. The `aws-mcp` entry is installed with the Kiro IDE Browser image; the other three are added by the workshop bootstrap:

```
{
  "mcpServers": {
    "aws-mcp": {
      "command": "uvx",
      "timeout": 100000,
      "transport": "stdio",
      "args": [
        "mcp-proxy-for-aws@latest",
        "https://aws-mcp.us-east-1.api.aws/mcp",
        "--metadata",
        "INSTALL_SOURCE=aws-cli"
      ]
    },
    "strands-agents": {
      "command": "uvx",
      "args": ["strands-agents-mcp-server"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    },
    "bedrock-agentcore-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.amazon-bedrock-agentcore-mcp-server@latest"],
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    },
    "awslabs.ecs-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "awslabs-ecs-mcp-server",
        "--with",
        "fastmcp>=2.10,<3",
        "ecs-mcp-server"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "FASTMCP_LOG_FILE": "/tmp/ecs-mcp-server.log",
        "ALLOW_WRITE": "false",
        "ALLOW_SENSITIVE_DATA": "false"
      },
      "autoApprove": [
        "ecs_resource_management",
        "ecs_troubleshooting_tool",
        "validate_ecs_express_mode_prerequisites",
        "wait_for_service_ready",
        "aws_knowledge_aws___search_documentation",
        "aws_knowledge_aws___read_documentation",
        "aws_knowledge_aws___recommend",
        "aws_knowledge_aws___get_regional_availability",
        "aws_knowledge_aws___list_regions"
      ]
    }
  }
}
```

Step 2: Verify the servers are working
Start a Kiro chat session from the workspace:

```
cd ~/environment
kiro-cli chat
```

Then type this command inside the chat:

```
/tools
```

You should see a list that includes tools from `aws-mcp`, `strands-agents`, `bedrock-agentcore-mcp-server`, and `awslabs.ecs-mcp-server`.

First time loading

MCP servers may take 2-3 minutes to initialize on their first launch. If they do not appear after running `/tools`, exit with `/quit` and start a new session. They should appear on the second attempt.

Step 3: Exit Kiro Chat

```
/quit
```

Part 3: Verify the Pre-Provisioned Skills
The three guided-sample skills are installed automatically by the workshop toolchain bootstrap, there is nothing to create here. You only confirm they are present.
Step 1: List the skills

```
ls ~/environment/.kiro/skills/
```

You should see all three: `build-customer-service-agent` (the Lab 1 guided sample), `build-chat-ui` (the Lab 6 Challenge 1 guided sample), and `deploy-chat-ui-to-ecs` (the Lab 6 Challenge 2 guided sample).
Step 2: Review a skill
Each skill is a single `SKILL.md` file. Open one to see the build playbook Kiro will follow:

```
cat ~/environment/.kiro/skills/build-customer-service-agent/SKILL.md
```

Step 3: See the skills in Kiro chat
Start a chat session from the workspace and type `/` to list the available skills as slash commands:

```
cd ~/environment
kiro-cli chat
```

```
/
```

All three skills appear in the list. You can invoke one by selecting it, or just describe the task in plain English and Kiro will activate the matching skill.

Skills missing?

If `ls ~/environment/.kiro/skills/` does not show all three skills, the toolchain bootstrap did not finish. Contact your event facilitator, do not try to create the skills by hand.

How each build challenge works

Every build challenge in the labs can be done three ways, and all three converge on the same result so the later labs work unchanged:

- Build your own agent with Kiro Specs: give Kiro your intent inside the lab's guardrails, review and approve the requirements, design, and tasks it drafts, then let Kiro execute the tasks and verify each one. 
- Guided sample with a Kiro skill: invoke the pre-provisioned skill (type `/` in chat) that carries the full build playbook. 
- Quick Spec with the sample brief: expand the sample brief in the lab and paste it into a Quick Spec; you still review requirements and tasks before Kiro builds. 

This is spec-driven development with [Kiro Specs](https://kiro.dev/docs/specs/): your intent becomes requirements with testable acceptance criteria, a design, and a task list you approve before Kiro writes code, then Kiro executes the tasks and you verify.

Summary
After completing this page, your workspace should look like this:

```
~/environment/
└── .kiro/
    ├── steering/
    │   ├── agentcore-deployment.md    (deployment rules for Kiro)
    │   ├── strands-agent-coding.md    (agent coding patterns for Kiro)
    │   └── langgraph-agent-coding.md  (optional, Step 3b: replaces strands-agent-coding.md for LangGraph teams)
    └── skills/                        (pre-provisioned by the bootstrap)
        ├── build-customer-service-agent/SKILL.md  (Lab 1 guided sample)
        ├── build-chat-ui/SKILL.md                 (Lab 6 Challenge 1 guided sample)
        └── deploy-chat-ui-to-ecs/SKILL.md         (Lab 6 Challenge 2 guided sample)

~/.kiro/
└── settings/
    └── mcp.json                       (MCP server connections)
```

Important

In Lab 1, when you ask Kiro to scaffold your agent project using `agentcore create`, your agent project folder (`CustomerServiceAgent/` for the guided sample, with the runtime code in `CustomerServiceAgent/app/agent/`) will be created inside `~/environment/`. Since you are already working from this directory, Kiro will have access to the steering file for all subsequent prompts.

Quick reference: what you set up

| What | Where | Purpose |
| AgentCore steering | ~/environment/.kiro/steering/agentcore-deployment.md | Teaches Kiro the correct deployment patterns and CLI commands |
| Strands steering | ~/environment/.kiro/steering/strands-agent-coding.md | Teaches Kiro how to structure Strands agent code |
| LangGraph steering (optional) | ~/environment/.kiro/steering/langgraph-agent-coding.md | Teaches Kiro how to structure LangGraph agent code; created in Step 3b in place of the Strands file |
| MCP config | ~/.kiro/settings/mcp.json | Connects Kiro to AWS and SDK documentation |
| Agent build skill | ~/environment/.kiro/skills/build-customer-service-agent/SKILL.md | Lab 1 guided sample: full agent build playbook (invoke with /) |
| Chat UI build skill | ~/environment/.kiro/skills/build-chat-ui/SKILL.md | Lab 6 Challenge 1 guided sample: full chat-UI build playbook (invoke with /) |
| Chat UI deploy skill | ~/environment/.kiro/skills/deploy-chat-ui-to-ecs/SKILL.md | Lab 6 Challenge 2 guided sample: deploy the chat UI to ECS Fargate (invoke with /) |

Setup complete

Kiro CLI now has the context it needs to help you build and deploy your agent. The steering files ensure Kiro will use `agentcore create` to scaffold your project and follow the correct deployment patterns. Proceed to Lab 1 to start building.
---

<!-- page: 04_lab-1-build-agent -->
# Lab 1: Build Your Agent

Lab 1: Build Your First AI Agent
Your Mission
Build a functional AI customer service agent for AnyCompany Telecom with Kiro, using Kiro's spec-driven workflow: your intent becomes requirements, a design, and a task list you review before Kiro builds. You'll create a Strands SDK agent with a system prompt, connect it to a Knowledge Base for RAG-powered support responses, deploy it to Amazon Bedrock AgentCore Runtime, and test it with real customer queries.
Challenge 1 offers two paths to the same agent: build it with Kiro Specs, reviewing the requirements, design, and tasks before Kiro writes code, or run a pre-provisioned Kiro skill that builds it end to end.
By the end of this lab, you'll have a production-ready agent deployed on AgentCore that can answer telecom support questions using knowledge base retrieval.
What You'll Build
 
- A Strands SDK agent with a customer service persona for AnyCompany Telecom, scaffolded from the AgentCore CLI `agent-python-strands` template 
- A Knowledge Base retrieval tool that pulls information from telecom support documents 
- A deployed AgentCore Runtime endpoint serving your agent at scale, together with the AgentCore Memory the template declares (Lab 2 inspects and tunes it) 
Prerequisites
Before starting this lab, ensure you have:
 
- Access to your development environment (the Kiro IDE Browser) 
- All verification commands passing from the Getting Started section 
- Your Knowledge Base ID (run `create_knowledge_base` if you haven't already) 

Knowledge Base Setup

If you haven't created your Knowledge Base yet, run the following command in your terminal:

```
create_knowledge_base
```

Note the Knowledge Base ID from the output. You'll need it when building your agent.

Lab Structure
This lab is organized into three challenges:
 
- Create the Agent: Build the Strands SDK agent with system prompt and KB tool 
- Deploy to AgentCore: Deploy your agent to AgentCore Runtime 
- Test Your Agent: Verify the agent responds with telecom-specific knowledge 

Challenge Approach

Each build challenge states a goal and what the change must cover, and you can meet it three ways: write your own brief and start a Spec (or a Quick Spec when short on time), review `requirements.md` and `tasks.md` against the Verification section, then let Kiro execute; run the pre-provisioned Kiro skill (type `/` in chat) that carries the full build playbook; or paste the sample brief from the expandable section into a Quick Spec. All three converge on the same agent. Test challenges need no spec.

- Challenge 1: Create the Agent
- Challenge 2: Deploy to AgentCore
- Challenge 3: Test Your Agent

---

<!-- page: 05_lab-1-build-agent__create-agent -->
# Challenge 1: Create the Agent

Challenge 1: Create Your Customer Service Agent
Mission
Create the AnyCompany Telecom customer service agent that:
 
- Has a system prompt defining the agent's persona 
- Includes a Knowledge Base retrieval tool against the workshop Knowledge Base 
- Uses the correct model ID format for Amazon Bedrock 
- Follows the AgentCore project structure so it can be deployed in the next challenge 
What You'll Need
 
- Knowledge Base ID: From the `create_knowledge_base` script you ran during setup 
- AgentCore CLI: Already installed in your environment (`agentcore --version` to verify) 
- Kiro: Either Kiro CLI (`kiro-cli chat`) or Kiro IDE open in your workspace 
Create Knowledge base (Optional)
If you don't want to provision the knowledge base with the `create_knowledge_base` command, you can create your own Knowledge base using your own prompt.

Write the brief yourself first

Compose your own spec brief from the bullets below before expanding the sample. The point is to state intent and acceptance criteria, not to find the right words for Kiro.

What your spec must cover
 
- The build must create a Bedrock Knowledge Base in this AWS account for an AnyCompany Telecom support agent. 
- The Knowledge Base must be usable by the agent as a retrieval source (the agent always searches it before answering customer questions). 
- The content scope must cover telecom plans, billing, and troubleshooting so the agent can provide specific plan details, pricing, and resolution steps. 
Each of these should appear as an acceptance criterion in `requirements.md`; the agent you build next is the test.
Start a spec
In the Kiro chat panel open a new session and choose Quick Spec (or Spec if you want to approve requirements, design, and tasks separately), or run `/spec new create-knowledge-base` in `kiro-cli chat` from your agent project folder. Paste your brief, then review `requirements.md` against the bullets above. When the task list looks right, tell Kiro "Run all tasks for this spec".

Sample spec brief

Paste this into Quick Spec (or after `/spec new create-knowledge-base`).

```
I am building a production-grade AI customer service agent for AnyCompany Telecom. The
agent will be tested for its ability to use a knowledge base. I have not created the
knowledge base yet.
The agent is an "AnyCompany Telecom Support Assistant" that:
- Is professional, helpful, and knowledgeable about telecom plans, billing, and
  troubleshooting
- Always searches the knowledge base before answering customer questions
- Provides specific plan details, pricing, and resolution steps
- Acknowledges when it does not have enough information
- Offers to escalate to a human agent for complex issues
Create the knowledge base for me in this AWS account.

Turn this into a spec: write the requirements with acceptance criteria that include
every constraint above, then the design, then the task list. Ask me clarifying
questions before drafting. Wait for my approval before executing the tasks.
```

Pick one path below. Both paths build the same agent and end in the same place: a scaffolded, customized `CustomerServiceAgent` project in `~/environment` that Labs 2 to 6 build on.
 
- Build with Kiro Specs: build the agent with Kiro's spec-driven workflow: requirements, design, and tasks you review before any code is written 
- Guided sample: run the pre-provisioned `build-customer-service-agent` skill, which carries the full build playbook 

- 
- 

Build with Kiro Specs: requirements, design, tasks

In this path you build the AnyCompany Telecom customer service agent with Kiro using a [Kiro Specs](https://kiro.dev/docs/specs/) workflow. A spec turns your intent into three reviewable documents: a `requirements.md` with user stories and acceptance criteria, a `design.md` with the technical approach, and a `tasks.md` with an ordered implementation plan. You approve each document before Kiro writes a line of code, then Kiro executes the tasks one at a time and you verify each result. Kiro does the heavy lifting; you stay in control of every decision that matters.

Time box: target 20 to 25 minutes for this challenge. Use Quick Spec if you are short on time: it generates requirements, design, and tasks in one pass after a few clarifying questions, and you still review the task list before Kiro builds.

The spec workflow in this challenge

- Start a spec (~2 min). In the chat panel open a new session and choose Spec from "Start with a built-in agent" (or Quick Spec if short on time), or run `/spec new customer-service-agent` in `kiro-cli chat`. When asked, pick Build a Feature and the Requirements workflow. 
- Requirements (~5 min). Paste the brief below. Kiro drafts `requirements.md` with user stories and acceptance criteria. Check that every constraint in the brief appears as an acceptance criterion. Reply "looks good" to approve, or give specific feedback such as "Add an acceptance criterion for the model ID format". 
- Design (~3 min). Click Generate Tech Design. Review `design.md`: the import path, lazy init, the Knowledge Base tool, and model ID discovery. Approve or give feedback. 
- Tasks (~2 min). Click Generate Task List. Review `tasks.md`; tasks should be ordered so each builds on the previous. 
- Execute (~10 min). Tell Kiro "Run all tasks for this spec", or start tasks one at a time to review each result. Kiro runs tests at checkpoints and fixes failures. When done, run "Before you continue". 

Where the spec lives

The spec files land in `~/environment/.kiro/specs/<name>/` (`requirements.md`, `design.md`, `tasks.md`). You can open them in the Explorer and edit them directly; Kiro picks up your edits.

Your spec brief

Paste this brief into Kiro chat after you start the spec. Replace the optional placeholder with your own design choices or delete that line, and keep the constraints unchanged so each one becomes an acceptance criterion.

```
I want to build a production-grade AI customer service agent for AnyCompany
Telecom: an "AnyCompany Telecom Support Assistant" with this persona:

- Professional, helpful, knowledgeable about telecom plans, billing, and
  troubleshooting
- Always searches the knowledge base before answering customer questions
- Provides specific plan details, pricing, and resolution steps
- Acknowledges when it doesn't have enough information
- Offers to escalate to a human agent for complex issues

My design choices: [OPTIONAL: your own tone, response format, or structured outputs]

Non-negotiable constraints (the rest of the workshop depends on these):

- Project named "CustomerServiceAgent", created with
  `agentcore create --name CustomerServiceAgent --template agent-python-strands`
  in ~/environment (never scaffold the folder structure manually)
- Framework Strands, model provider Bedrock (the template default); keep the
  AgentCore Memory named agentMemory that the template declares
- Entrypoint app/agent/main.py imports from bedrock_agentcore.runtime, uses lazy
  initialization, an async streaming handler, and the template's parse_payload
- At least one tool: a Knowledge Base retrieval tool against the workshop
  Knowledge Base (use my KNOWLEDGE_BASE_ID variable, otherwise discover the KB
  named anycompany-telecom-kb)
- Use the latest Claude Sonnet inference-profile ID (prefixed, e.g.
  global.anthropic.claude-sonnet-...) in app/agent/model/load.py; discover it,
  do not hardcode a stale ID
- Keep UNIFIED_TRACES_DESTINATION_ENABLED set to true as an entry in the
  runtime's envVars list in agentcore/agentcore.json
- Grant the deployed runtime bedrock:Retrieve on the Knowledge Base ARN and
  bedrock:RetrieveAndGenerate (no resource type, so on "\*") through the
  runtime's additionalPolicies list in agentcore/agentcore.json (a policy file
  under app/agent/policies/), not by editing IAM roles by hand

Turn this into a spec: write the requirements with acceptance criteria that
include every constraint above, then the design, then the task list. Ask me
clarifying questions before drafting. Wait for my approval of each document
before executing the tasks.
```

While Kiro executes the tasks, review each result against the constraints in the brief. Confirm the project name, the template command, import path, model ID, Knowledge Base tool, and the `envVars` entry match those constraints as they are created. It is much cheaper to correct early than after the full build.

Before you continue
Whichever path you took, confirm the project is set up correctly before moving on:

```
cd ~/environment/CustomerServiceAgent
# Entrypoint exists
ls app/agent/main.py
# Entrypoint uses the runtime import
grep -r "bedrock_agentcore.runtime" app/agent/*.py
# A Knowledge Base retrieval reference is present
grep -rni "retrieve\|knowledge" app/agent/ --include="*.py" --exclude-dir=.venv
# The template's memory is still declared
grep -A2 '"memories"' agentcore/agentcore.json
# Observability env var is set
grep -A3 envVars agentcore/agentcore.json

# The runtime role will be allowed to query the Knowledge Base
grep -A1 additionalPolicies agentcore/agentcore.json && grep -l 'bedrock:Retrieve' app/agent/policies/*.json
```

If something is off, fix it now with Kiro before proceeding. Labs 2 to 6 depend on this exact project.

Accelerate: add a hook that runs your tests on every save

Hooks are optional automation that Kiro runs on an event such as saving a file: a shell command or a prompt, defined in a JSON file under `.kiro/hooks/`. See [Kiro Hooks](https://kiro.dev/docs/hooks/).

The hook below runs your agent's unit tests every time you save a Python file, so a regression shows up immediately. Create it:

```
mkdir -p ~/environment/CustomerServiceAgent/.kiro/hooks
cat > ~/environment/CustomerServiceAgent/.kiro/hooks/test-on-save.json << 'HOOK_EOF'
{
"version": "v1",
"hooks": [
{
"name": "test-on-save",
"description": "Run agent unit tests when a Python file is saved",
"trigger": "PostFileSave",
"matcher": "\\.py$",
"action": {
"type": "command",
"command": "cd ~/environment/CustomerServiceAgent/app/agent && uv run --with pytest python -m pytest -q 2>&1 | tail -5"
},
"timeout": 120
}
]
}
HOOK_EOF
```

The command runs in `app/agent`, where the template's `pyproject.toml` and virtual environment live; `uv run --with pytest` adds pytest for the run without putting it in the runtime dependencies. Kiro reads `.kiro/hooks/` in the workspace, so the hook is active for the IDE chat panel and Kiro CLI alike; remove the file to disable it.

This box is optional and not needed to finish the lab.

Step 3: Test Locally (Optional)
Before deploying, you can test the agent locally (open another terminal in parallel):

```
cd ~/environment/CustomerServiceAgent
agentcore dev --port 8081
```

This starts a headless local development server for the runtime `agent` on port 8081 and keeps running until you stop it with `Ctrl+C`. Always pass `--port 8081`: the default port, 8080, is used by the Kiro IDE Browser itself. In another terminal, send a request to it:

```
cd ~/environment/CustomerServiceAgent
agentcore invoke --runtime agent --local --port 8081 --payload '{"prompt":"What plans does AnyCompany Telecom offer?"}'
```

The payload is JSON: `prompt` is the user message. The response streams to the terminal.

Agent Inspector (optional, untested behind the IDE proxy)

`agentcore dev --mode browser --port 8081 --ui-port 8082` also starts the Agent Inspector web UI on port 8082. It is written for a local browser (`http://localhost:8082`) and has not been tested through the IDE's `/proxy/<port>/` path, so the labs use headless `agentcore dev` plus `agentcore invoke --local`.

Kiro CLI users: See sample output from testing the agent locally

Here's what `agentcore dev` looks like when testing via Kiro CLI in the Kiro IDE Browser:

Local testing

Local testing requires AWS credentials to access Bedrock models and the Knowledge Base. If you get permission errors, you can skip this step and test after deploying in Challenge 2.

Verification
Confirm your agent project is properly structured:

```
cd ~/environment/CustomerServiceAgent
# Check the project structure
ls agentcore/
ls app/agent/
# Verify the runtime, the memory and the envVars entry
cat agentcore/agentcore.json
# Verify the model ID uses an inference profile
grep "global\." app/agent/model/load.py
```

Expected Output

You should see:

- `agentcore/` directory containing `agentcore.json`, `aws-targets.json` and `cdk/` 
- `app/agent/` directory containing `main.py`, `parse.py`, `model/`, `memory/` and `pyproject.toml` 
- In `agentcore.json`: `runtimes[0].name` is `agent`, `memories[0].name` is `agentMemory`, and the runtime has an `envVars` entry with `UNIFIED_TRACES_DESTINATION_ENABLED` set to `true` 
- The grep for `global.` shows the inference-profile model ID in `model/load.py` 

Note

Your exact code and structure may vary depending on the path and prompts you used. The key requirements are: (1) valid AgentCore project structure created by `agentcore create --template agent-python-strands`, (2) customized `app/agent/main.py` with a customer service system prompt, (3) a knowledge base retrieval tool connected to your KB ID, and (4) the `agentMemory` memory still declared.

---

<!-- page: 06_lab-1-build-agent__deploy-agent -->
# Challenge 2: Deploy to AgentCore

Challenge 2: Deploy Your Agent to AgentCore Runtime
Mission
Deploy your Strands SDK agent to Amazon Bedrock AgentCore Runtime using the AgentCore CLI. Once deployed, your agent will be available as a managed endpoint with auto-scaling, session management, and production-grade reliability.
What You'll Need
 
- Completed agent code from Challenge 1 (`app/agent/main.py`, your tool module, `app/agent/pyproject.toml`) 
- AgentCore CLI installed and configured (`agentcore` command available) 
- AWS credentials configured in your environment 
- Working directory set to your agent project folder 

No spec needed here

This challenge runs and verifies what you already built; it changes no code, so run the commands directly or ask Kiro in chat. Specs are for changes to the agent, its tools, or its infrastructure.

Ideas for Your Approach
Think about what's needed to deploy an agent to AgentCore:
 
- The `agentcore deploy` command packages your agent code and deploys everything declared in `agentcore/agentcore.json`: the runtime `agent` and the memory `agentMemory` 
- AgentCore needs to know your entry point and how to invoke your agent (the runtime's `entrypoint` and `codeLocation` in `agentcore.json`) 
- Your agent's dependencies (`app/agent/pyproject.toml`) get packaged automatically for ARM64 Linux 
- The deployment process creates a runtime endpoint that serves your agent 
The AgentCore CLI handles most of the deployment complexity. Run `agentcore --help` and `agentcore deploy --help` to understand the available options before looking at the sample request.
Explore the CLI

```
# Check AgentCore CLI is available
agentcore --version

# See available commands
agentcore --help

# See deploy options
agentcore deploy --help
```

Sample request to Kiro

```
Deploy my Strands SDK agent to Amazon Bedrock AgentCore Runtime. My agent is in
~/environment/CustomerServiceAgent/. Package and deploy it, then confirm it is running
with agentcore status.
```

Kiro CLI users: See sample deployment output

Here's what the deployment looks like when triggered via Kiro CLI:

Hint: Deployment Commands

The basic deployment flow is:

```
# Navigate to your agent directory
cd ~/environment/CustomerServiceAgent

# Deploy to AgentCore Runtime
agentcore deploy
```

The `agentcore deploy` command will:

- Create the default deployment target from your AWS account and region (first run only) and bootstrap CDK in the account (first run only) 
- Package your Python code and dependencies 
- Deploy a CloudFormation stack with the runtime `agent`, its execution role, and the memory `agentMemory` 
- Return when the deployment is ready 

The first deploy takes 5 to 8 minutes (CDK bootstrap, the memory and the runtime endpoint); later deploys take about 5 minutes. There is no confirmation prompt. For verbose CDK output, run `agentcore --debug deploy`. A successful deploy prints:

```
created default deployment target: account <ACCOUNT_ID>, region us-east-1 (agentcore/aws-targets.json)
verifying AWS account <ACCOUNT_ID>
synthesizing CloudFormation templates
enabling CloudWatch Transaction Search
bootstrapping aws://<ACCOUNT_ID>/us-east-1
deploying AgentCore-CustomerServiceAgent-default (usually takes a few minutes)
deployed project 'CustomerServiceAgent' to target 'default'
next step:
  agentcore invoke
```

The first line and the `bootstrapping` line appear on the first deploy only: the CLI creates the deployment target and the `CDKToolkit` stack once per account. `enabling CloudWatch Transaction Search` is the CLI switching on the CloudWatch feature that Lab 5 relies on.

Verification
After deployment completes, verify your agent is running:

```
# Check deployment status
agentcore status
```

Expected Output

```
$ agentcore status
 ── resources
 ❯ ▾agent agent
     ├─ runtime  agent deployed
     └─ memory   agentMemory deployed
[↑↓/jk] navigate  [←→] collapse/expand  [enter] open  [esc] back  [ctrl+c] quit
```

In a terminal `agentcore status` is an interactive tree; press `Ctrl+C` to leave (`Esc` opens the filter, it does not exit) it. When the output is not a terminal (a script, a Kiro tool call), or with `--json`, it prints the same information as JSON:

```
{
  "projectName": "CustomerServiceAgent",
  "target": "default",
  "region": "us-east-1",
  "resources": [
    {
      "resourceType": "runtime",
      "name": "agent",
      "deploymentState": "deployed",
      "arn": "arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:runtime/CustomerServiceAgent_default_agent-<agent-id>"
    },
    {
      "resourceType": "memory",
      "name": "agentMemory",
      "deploymentState": "deployed",
      "arn": "arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:memory/CustomerServiceAgent_default_agentMemory-<memory-id>"
    }
  ]
}
```

`agentcore status` lists every resource declared in `agentcore/agentcore.json` with its deployment state: the runtime `agent` and the memory `agentMemory` both show `deployed` together with their ARNs. A resource that shows `local-only` is declared but not yet deployed; run `agentcore deploy` again.

Note

Use `agentcore status --json` when you need the runtime ARN in a script (Lab 6 reads it from `.resources[] | select(.resourceType=="runtime") | .arn`).

Troubleshooting Deployment Failures
If your deployment fails, work through this checklist:

Troubleshooting Checklist

IAM Permission Errors

Symptom: Error messages mentioning "AccessDenied", "not authorized", or "insufficient permissions"

Resolution:

- Verify your AWS credentials are active: `aws sts get-caller-identity` 
- Ensure you're using the workshop-provided credentials (not personal credentials) 
- Check that your session token hasn't expired (re-copy from Workshop Studio if needed) 

```
# Verify credentials
aws sts get-caller-identity

# If expired, re-export credentials from Workshop Studio event page
export AWS_ACCESS_KEY_ID="<new-key>"
export AWS_SECRET_ACCESS_KEY="<new-secret>"
export AWS_SESSION_TOKEN="<new-token>"
```

A Failed First Deploy Left CDKToolkit Behind

Symptom: `agentcore deploy` stops with `The shared CDKToolkit stack is in 'ROLLBACK_COMPLETE'. Resolve that stack manually before deploying this project`, or with `The resources [StagingBucket] already exist in your account`

Cause: The first deploy in an account creates the CDK bootstrap stack `CDKToolkit`. If that creation fails (for example on a permission error), CloudFormation rolls the stack back but keeps it, and the AgentCore CLI refuses to deploy until it is gone. A rollback can also leave the bootstrap's S3 bucket behind.

Resolution: delete the failed stack and the leftover bucket, then run `agentcore deploy` again. The bucket name ends in your account ID and Region, so the second command fails harmlessly if there is nothing to remove.

```
aws cloudformation delete-stack --stack-name CDKToolkit &&
aws cloudformation wait stack-delete-complete --stack-name CDKToolkit
aws s3 rb "s3://cdk-hnb659fds-assets-${ACCOUNT_ID}-${AWS_REGION}" --force 2>/dev/null || true
agentcore deploy
```

If the deploy fails on the same permission error a second time, contact your facilitator: the participant role needs the KMS and S3 permissions the bootstrap uses, and they are part of the workshop's IAM policy.

Model Access Errors

Symptom: Error messages mentioning "model not found", "model access not granted", or "ResourceNotFoundException"

Resolution:

- Confirm you're using the correct model ID format: `global.anthropic.claude-sonnet-4-6` 
- Verify the model is enabled in your account's Bedrock Model Access page 
- Ensure you're in the correct AWS region (`us-east-1`) 

```
# Check current region
echo $AWS_DEFAULT_REGION

# List available foundation models
aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'claude')].modelId" --output table
```

Dependency Packaging Errors

Symptom: Error messages about missing modules, import failures, or package installation issues

Resolution:

- Verify `app/agent/pyproject.toml` lists every runtime package in `[project].dependencies`, and only runtime packages (dev or test dependencies may lack ARM64 wheels and break the build; put pytest in a `[dependency-groups] dev` table instead) 
- Ensure no local-only dependencies (file paths, environment-specific packages) 
- Check Python version compatibility (Python 3.10+) 

```
# Resolve the dependencies the way the deploy will (uv; the IDE's system Python has no pip)
cd ~/environment/CustomerServiceAgent/app/agent
uv sync

# Verify the entrypoint imports cleanly
uv run python -c "import main" 2>&1 || echo "Import error, check your code"
```

General Debugging

```
cd ~/environment/CustomerServiceAgent

# Re-run deployment with verbose CDK output
agentcore --debug deploy

# Check the runtime logs from the last 15 minutes
agentcore logs runtime --since 15m
```

---

<!-- page: 07_lab-1-build-agent__test-agent -->
# Challenge 3: Test Your Agent

Challenge 3: Test Your Deployed Agent
Mission
Invoke your deployed agent with sample customer queries and verify it responds with AnyCompany Telecom-specific information sourced from the Knowledge Base. This confirms your agent is:
 
- Successfully deployed and reachable on AgentCore Runtime 
- Connecting to the Bedrock Knowledge Base for RAG retrieval 
- Returning relevant telecom support information 
What You'll Need
 
- Deployed agent from Challenge 2 (`agentcore status` shows the runtime `agent` as `deployed`) 
- AgentCore CLI: specifically the `agentcore invoke --runtime agent --payload '{"prompt":"..."}'` command 
- Sample queries related to AnyCompany Telecom services 

No spec needed here

This challenge runs and verifies what you already built; it changes no code, so run the commands directly or ask Kiro in chat. Specs are for changes to the agent, its tools, or its infrastructure.

Ideas for Your Approach
Think about how to validate your agent works end-to-end:
 
- Use `agentcore invoke` to send messages to your deployed agent 
- Ask questions that require Knowledge Base retrieval (plan details, billing FAQ, troubleshooting) 
- Check that responses contain specific AnyCompany Telecom information (plan names, pricing, policies) 
- Try different query types to test the agent's knowledge breadth 

Test it yourself first

Think about what a real AnyCompany Telecom customer might ask. Try crafting your own test queries before looking at the sample ones below. Good test queries are ones where you can verify the answer comes from the Knowledge Base.

Test Your Agent
Run the commands from your project folder (`~/environment/CustomerServiceAgent`). `agentcore invoke` sends a JSON payload to the deployed runtime named `agent`; `prompt` is the user message and the response streams to the terminal as raw server-sent events, one `data:` line per model event, followed by a `status=200 ...` summary line:

```
data: {"event": {"messageStart": {"role": "assistant"}}}
data: {"event": {"contentBlockStart": {"start": {"toolUse": {"toolUseId": "<id>", "name": "list_plans", "type": "tool_use"}}, "contentBlockIndex": 0}}}
data: {"event": {"contentBlockDelta": {"delta": {"text": "AnyCompany"}, "contentBlockIndex": 0}}}
data: {"event": {"contentBlockDelta": {"delta": {"text": " Telecom has three internet plans"}, "contentBlockIndex": 0}}}
...
data: {"event": {"messageStop": {"stopReason": "end_turn"}}}
data: {"event": {"metadata": {"usage": {"inputTokens": 448, "outputTokens": 227, "totalTokens": 675}, "metrics": {"latencyMs": 2597}}}}
status=200 content-type=text/event-stream; charset=utf-8 runtime-session-id=<uuid> ... complete=true bytes=4037
```

The answer is spread over the `contentBlockDelta.delta.text` fragments. To read it as prose, pipe the output through `jq`. The filter also prints any `error` event the runtime returns, so a failed invocation shows its message instead of a blank line (the `status=200` summary line reports the HTTP transport, not whether the agent succeeded):

```
agentcore invoke --runtime agent --payload '{"prompt":"What plans does AnyCompany Telecom offer?"}' \
  | sed -n 's/^data: //p' | jq -rj '.event.contentBlockDelta.delta.text // (.error | select(. != null) | "ERROR: \(.)\n") // empty'; echo
```

The expected outputs on this and the following pages show the assembled prose, not the raw `data:` lines.

```
cd ~/environment/CustomerServiceAgent
# Basic invocation
agentcore invoke --runtime agent --payload '{"prompt":"What plans does AnyCompany Telecom offer?"}'
```

Sample Test Queries: Click to reveal

Try these queries to validate different aspects of your agent:

```
# Test plan information retrieval
agentcore invoke --runtime agent --payload '{"prompt":"What are the differences between Basic, Premium, and Enterprise plans?"}'

# Test billing FAQ retrieval
agentcore invoke --runtime agent --payload '{"prompt":"How do overage charges work on the Basic plan?"}'

# Test troubleshooting knowledge
agentcore invoke --runtime agent --payload '{"prompt":"My internet connection keeps dropping. What troubleshooting steps should I follow?"}'

# Test escalation policy knowledge
agentcore invoke --runtime agent --payload '{"prompt":"When should a case be escalated to a human agent?"}'

# Test general customer service behavior
agentcore invoke --runtime agent --payload '{"prompt":"Hi, I am a new customer. Can you tell me about your service plans and pricing?"}'
```

The payload is single-quoted, so write prompts without apostrophes (use "I am" instead of "I'm") or the shell ends the string early.

Hint: What to Look For in Responses

Your agent's responses should demonstrate:

- Knowledge Base retrieval: Responses mention specific plan names (Basic, Premium, Enterprise), pricing details, or troubleshooting steps from the KB documents 
- Professional persona: The agent responds as an AnyCompany Telecom support representative, not a generic AI 
- Relevant information: Answers are specific to the question asked and reference telecom-related content 
- Appropriate limitations: The agent acknowledges when it needs more information or offers to escalate 

If responses are generic (not mentioning AnyCompany Telecom specifics), the Knowledge Base tool may not be configured correctly. Check:

- Your Knowledge Base ID matches the one from `create_knowledge_base` output 
- The KB sync completed successfully 
- The retrieval tool is properly registered with the agent 

Verification
Run this validation sequence to confirm your agent is working correctly:

```
cd ~/environment/CustomerServiceAgent
# Step 1: Confirm the runtime and the memory are deployed
agentcore status

# Step 2: Invoke with a query that requires KB retrieval
agentcore invoke --runtime agent --payload '{"prompt":"What plans does AnyCompany Telecom offer and what are their prices?"}'

# Step 3: Verify response contains telecom-specific content
# Look for: plan names, pricing, features from your KB documents
```

Expected Output

Status check:

```
$ agentcore status
 ── resources
 ❯ ▾agent agent
     ├─ runtime  agent deployed
     └─ memory   agentMemory deployed
[↑↓/jk] navigate  [←→] collapse/expand  [enter] open  [esc] back  [ctrl+c] quit
```

In a terminal `agentcore status` is an interactive tree; press `Ctrl+C` to leave (`Esc` opens the filter, it does not exit) it. When the output is not a terminal (a script, a Kiro tool call), or with `--json`, it prints the same information as JSON:

```
{
  "projectName": "CustomerServiceAgent",
  "target": "default",
  "region": "us-east-1",
  "resources": [
    {
      "resourceType": "runtime",
      "name": "agent",
      "deploymentState": "deployed",
      "arn": "arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:runtime/CustomerServiceAgent_default_agent-<agent-id>"
    },
    {
      "resourceType": "memory",
      "name": "agentMemory",
      "deploymentState": "deployed",
      "arn": "arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:memory/CustomerServiceAgent_default_agentMemory-<memory-id>"
    }
  ]
}
```

Sample invocation response (assembled text):

```
AnyCompany Telecom offers three service plans:

1. **Basic Plan** - Designed for light users with essential connectivity needs.
   Includes standard data allowance and basic support.

2. **Premium Plan** - For customers who need more data, faster speeds,
   and priority support access.

3. **Enterprise Plan** - Our top-tier offering with unlimited data,
   dedicated support, and SLA guarantees.

I'd be happy to provide more details about any specific plan, including
pricing and features. Which plan interests you?
```

Results May Vary

Your agent's exact response will differ based on:

- The system prompt you wrote 
- The model's interpretation of your KB documents 
- The specific wording of your query 

The key validation is that the response contains AnyCompany Telecom-specific information (plan names, features, policies) that could only come from the Knowledge Base, not generic AI responses.

Troubleshooting

Common Issues

The invoke returns a single `error` event mentioning `aws-marketplace:Subscribe` or `aws-marketplace:ViewSubscriptions`:

The deployed agent runs under the AgentCore runtime role, and Anthropic models on Amazon Bedrock need a one-time AWS Marketplace agreement in the account before any role can invoke them. The workshop bootstrap accepts the agreements when your team account is prepared; if that step did not run, accept them yourself. The command uses your participant role, which has the Marketplace permissions, and skips models that are already enabled:

```
enable_anthropic_models
```

A new agreement takes 2 to 6 minutes to propagate; until then the invoke keeps returning `AccessDeniedException`. Wait, then run the invoke again. A rerun of the command reports already-enabled models as skipped, not failed. Local invokes (`agentcore invoke --local`) worked before this because they run under your participant role, not the runtime role.

The response is empty but the summary line says `status=200`:

The summary line reports the HTTP transport. Run the invoke without the `jq` filter and read the `data:` lines; an `{"error": ...}` event carries the reason.

Every answer says the agent cannot look up plan details, and `agentcore logs runtime --since 15m` shows `AccessDeniedException` on the `Retrieve` or `RetrieveAndGenerate` operation for the runtime role:

The runtime role the AgentCore CLI creates can invoke models and use memory, nothing else. The retrieval tool needs `bedrock:Retrieve`, declared in the project so every deploy carries it. Check that `agentcore/agentcore.json` lists `"additionalPolicies": ["policies/knowledge-base-retrieve.json"]` on the runtime and that `app/agent/policies/knowledge-base-retrieve.json` allows `bedrock:Retrieve` on `arn:aws:bedrock:*:*:knowledge-base/*` and `bedrock:RetrieveAndGenerate` on `*` (the Challenge 1 "Before you continue" check covers both files). If either is missing, ask Kiro to add them, then run `agentcore deploy` again; the policy attaches to the role during the deploy. Local invokes do not show this error because they run as your participant role.

The response does not mention AnyCompany Telecom plans, prices, or policies:

Confirm the Knowledge Base ID in the retrieval tool matches `create_knowledge_base` output (`cat ~/environment/kb-output.json`), and that the system prompt tells the agent to search the knowledge base before answering. Check `agentcore logs runtime --since 15m` for a retrieval error.

Testing locally from the Kiro IDE Browser

To test code changes before a redeploy, start the headless local dev server with `agentcore dev --port 8081` (port 8080 is reserved by the Kiro IDE Browser) and send requests to it from a second terminal:

```
agentcore invoke --runtime agent --local --port 8081 --payload '{"prompt":"What plans does AnyCompany Telecom offer?"}'
```

The optional Agent Inspector web UI (`agentcore dev --mode browser --port 8081 --ui-port 8082`) is written for a local browser and has not been tested through the IDE's `/proxy/<port>/` path.

Lab 1 Summary
In this lab you:
 
- Created a Strands SDK agent with a customer service system prompt 
- Connected the agent to a Knowledge Base for RAG-powered responses 
- Deployed the agent to AgentCore Runtime 
- Tested the agent with customer queries and verified KB retrieval 
Your agent is now running in production on AgentCore Runtime, together with the AgentCore Memory the template declared. In the next lab, you inspect, test and tune that memory so the agent remembers customers across conversations.

What's Next

In Lab 2, you inspect the memory `agentMemory` that the `agent-python-strands` template created (a SEMANTIC strategy for facts per user and an EPISODIC strategy for episodes per session), tune how the agent retrieves it, and prove that it remembers what customers told it in previous sessions.

---

<!-- page: 08_lab-2-add-memory -->
# Lab 2: Add Memory to Your Agent

Add Memory to Your Agent
Your agent already has Amazon Bedrock AgentCore Memory: the `agent-python-strands` template you used in Lab 1 declared a memory named `agentMemory` with a SEMANTIC strategy (facts per user) and an EPISODIC strategy (episodes per session), and `agentcore deploy` created it next to the runtime. In this lab you inspect that memory, tune how the agent retrieves it, and prove that the agent (the AnyCompany Telecom support agent in the guided sample) remembers customer conversations across sessions.
What You'll Learn
 
- How AgentCore Memory provides short-term and long-term conversation persistence 
- How the template wires the memory into the agent (`agentcore/agentcore.json`, `app/agent/memory/session.py`, the `MEMORY_AGENTMEMORY_ID` variable) 
- How session IDs enable within-session context retention (short-term memory) 
- How the SEMANTIC strategy enables cross-session recall (long-term memory) 
- How to inspect memories, records and events with `agentcore memory` 
- How to validate memory works by conducting a multi-session test 
Why Memory Matters
Without memory, your agent treats every message as a brand-new conversation. It can't:
 
- Follow up on earlier questions in the same conversation 
- Remember customer details shared in previous interactions 
- Build context over time to provide more personalized support 
AgentCore Memory solves this by providing:
 
- Short-term memory: Automatically retains conversation context within a session (linked by session ID) 
- Long-term memory: Stores and retrieves relevant information across different sessions using semantic search (SEMANTIC strategy) 
Prerequisites
 
- Completed Lab 1 (agent deployed; `agentcore status` lists `agent` and `agentMemory` as `deployed`) 
- AgentCore CLI installed and authenticated 

Challenge Format

Each challenge states a goal and what the change must cover. You write a short brief, start a Quick Spec, review `requirements.md` and `tasks.md` against the Verification section, then let Kiro execute. Sample briefs are in expandable sections. Test challenges need no spec.

- Challenge 1: Inspect and Tune Memory
- Challenge 2: Test Memory with Multi-Session Recall

---

<!-- page: 09_lab-2-add-memory__add-memory -->
# Challenge 1: Inspect and Tune Memory

Challenge 1: Inspect and Tune Memory
Your Goal: Inspect the AgentCore Memory the template created for your agent, tune how the agent retrieves and uses remembered facts, then redeploy so the agent remembers conversations within and across sessions.

Write the brief yourself first

Compose your own spec brief from the bullets below before expanding the sample. The point is to state intent and acceptance criteria, not to find the right words for Kiro.

Mission
Your AnyCompany Telecom agent was scaffolded from the `agent-python-strands` template, which declares an AgentCore Memory named `agentMemory` in `agentcore/agentcore.json` and wires it into the agent in `app/agent/memory/session.py`. Lab 1 deployed it with the runtime. Your mission is to:
 
- Inspect the memory: understand the two strategies the template configured and how the memory ID reaches the agent code 
- Tune retrieval and the system prompt: so the agent pulls more remembered facts per request and uses them instead of asking the customer again 
- Redeploy the agent: so the tuned configuration takes effect 
Context
AgentCore Memory has two components, and the template configured both:

| Memory Type | Behavior | How the template configures it |
| Short-term | Retains context within a single session | Raw events in the current session, stored under the EPISODIC namespace /episodes/{actorId}/{sessionId}. The session is the --session-id you pass to agentcore invoke |
| Long-term | Recalls information across sessions | SEMANTIC strategy: facts are extracted asynchronously after each turn into /users/{actorId}/facts and retrieved by similarity to the current prompt (top_k=3 in memory/session.py) |

How the pieces connect:
 
- `agentcore/agentcore.json` declares the memory under `memories` with its `strategies`. `agentcore deploy` creates it and injects its ID into the runtime as the `MEMORY_AGENTMEMORY_ID` environment variable. 
- `app/agent/memory/session.py` reads that variable and builds an `AgentCoreMemorySessionManager` with a `retrieval_config` per namespace (`top_k`, `relevance_score`). 
- `app/agent/main.py` passes the session manager to the Strands `Agent`, keyed by the `session_id` from the request context and the `actorId` from the payload (`default` when the payload has none). 
Read the public developer guide for the strategy details: [AgentCore Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html).
What your spec must cover
 
- The memory stays the `agentMemory` the template declared (SEMANTIC and EPISODIC strategies); the spec does not create a second memory. 
- The retrieval configuration in `app/agent/memory/session.py` is tuned: `top_k` for the facts namespace goes from 3 to 5, `relevance_score` stays at 0.0. 
- The system prompt tells the agent to use remembered customer facts (name, plan, reported issues) without asking for them again. 
- The agent must retain context within a single session (short-term memory) and recall relevant details across sessions (long-term memory). 
- The change is complete when the agent is redeployed, `agentcore status` shows `agent` and `agentMemory` as `deployed`, and `agentcore memory record list` shows at least one fact after the Challenge 2 test. 
Each of these should appear as an acceptance criterion in `requirements.md`; the Verification section at the bottom of this page is the test.

Hint: how the memory reaches your code

- The CDK app the CLI deploys adds one environment variable per memory to every runtime: `MEMORY_<NAME>_ID` with the name upper-cased. For `agentMemory` that is `MEMORY_AGENTMEMORY_ID`. 
- `AgentCoreMemorySessionManager` (from `bedrock_agentcore.memory.integrations.strands`) does two things on every turn: it writes the user and assistant messages as events into the session, and it retrieves records from each namespace in `retrieval_config` and adds them to the agent's context. 
- Long-term facts are extracted by the SEMANTIC strategy asynchronously, so a fact told in one session appears in `/users/{actorId}/facts` about a minute later. 
- `agentcore memory list`, `agentcore memory get --id <memoryId>`, `agentcore memory record list --id <memoryId> --namespace <ns>` and `agentcore memory event list --id <memoryId> --actor-id <actor> --session-id <session>` let you look inside without any code. 

Start a spec
In the Kiro chat panel open a new session and choose Quick Spec (or Spec if you want to approve requirements, design, and tasks separately), or run `/spec new tune-memory` in `kiro-cli chat` from your agent project folder. Paste your brief, then review `requirements.md` against the bullets above and `tasks.md` for the redeploy step. When the task list looks right, tell Kiro "Run all tasks for this spec".

Sample spec brief

Paste this into Quick Spec (or after `/spec new tune-memory`).

```
My AgentCore agent in ~/environment/CustomerServiceAgent already has the memory
agentMemory that the agent-python-strands template declared (SEMANTIC and EPISODIC
strategies). Do not add another memory. Tune it so the agent remembers customers
across sessions: in app/agent/memory/session.py raise top_k for the facts namespace
from 3 to 5 and keep relevance_score at 0.0; update the system prompt so the agent
uses remembered customer facts (name, plan, reported issues) instead of asking for
them again. The change is complete when the agent is redeployed and
`agentcore status` shows agent and agentMemory as deployed.

Turn this into a spec: write the requirements with acceptance criteria that include
every constraint above, then the design, then the task list. Ask me clarifying
questions before drafting. Wait for my approval before executing the tasks.
```

Manual Steps (CLI Commands)

Run every command from `~/environment/CustomerServiceAgent`.

Step 1: Inspect the memory the template declared

```
cat agentcore/agentcore.json
```

Look at the `memories` block: one memory named `agentMemory`, `eventExpiryDuration` 30 days, a SEMANTIC strategy with the namespace `/users/{actorId}/facts`, and an EPISODIC strategy with the namespace `/episodes/{actorId}/{sessionId}`.

Step 2: Tune retrieval and the system prompt

In `app/agent/memory/session.py`, change the facts namespace entry to retrieve five facts:

```
retrieval_config = {
    f"/users/{actor_id}/facts": RetrievalConfig(top_k=5, relevance_score=0.0),
    f"/episodes/{actor_id}/{session_id}": RetrievalConfig(top_k=5, relevance_score=0.0),
}
```

In `app/agent/main.py`, add to `DEFAULT_SYSTEM_PROMPT`:

```
Use the facts you remember about the customer (name, plan, reported issues) instead of asking for them again.
```

Step 3: Redeploy the agent

```
agentcore deploy
```

Step 4: Check status

```
agentcore status
```

If your project has no memory

A project created without the Strands template, or one where the `memories` block was removed, needs the memory added first:

```
agentcore add memory --name agentMemory --strategies SEMANTIC,EPISODIC
agentcore deploy
```

The code must then read `MEMORY_AGENTMEMORY_ID` and build an `AgentCoreMemorySessionManager` the way the template's `app/agent/memory/session.py` does; copy that module from a template project if yours lacks it.

Verification
After redeploying, confirm the runtime and the memory are deployed, then inspect the memory itself:

```
cd ~/environment/CustomerServiceAgent
agentcore status
agentcore memory list --json
```

Copy the memory ID (`CustomerServiceAgent_default_agentMemory-...`) from the list and describe it:

```
agentcore memory get --id <memoryId>
```

Expected Output

`agentcore status`:

```
 ── resources
 ❯ ▾agent agent
     ├─ runtime  agent deployed
     └─ memory   agentMemory deployed
```

(`agentcore status --json` prints the same two resources with `"deploymentState": "deployed"` and their ARNs.)

`agentcore memory list` is interactive in a terminal (press `Ctrl+C` to leave (`Esc` opens the filter, it does not exit)); in a script or a Kiro tool call it needs `--json`. `agentcore memory list --json`:

```
{
  "memories": [
    {
      "createdAt": "2026-11-17T17:56:32.144Z",
      "updatedAt": "2026-11-17T17:56:32.495Z",
      "arn": "arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:memory/CustomerServiceAgent_default_agentMemory-<memory-id>",
      "id": "CustomerServiceAgent_default_agentMemory-<memory-id>",
      "status": "ACTIVE"
    }
  ]
}
```

`agentcore memory get --id CustomerServiceAgent_default_agentMemory-<memory-id>` (trimmed):

```
{
  "memory": {
    "id": "CustomerServiceAgent_default_agentMemory-<memory-id>",
    "name": "CustomerServiceAgent_default_agentMemory",
    "eventExpiryDuration": 30,
    "status": "ACTIVE",
    "strategies": [
      {
        "name": "agentMemory_Episodic",
        "type": "EPISODIC",
        "namespaces": ["/episodes/{actorId}/{sessionId}"],
        "configuration": {
          "type": "EPISODIC",
          "reflection": {
            "episodicReflectionConfiguration": {
              "namespaces": ["/episodes/{actorId}"]
            }
          }
        },
        "status": "ACTIVE"
      },
      {
        "name": "agentMemory_Semantic",
        "type": "SEMANTIC",
        "namespaces": ["/users/{actorId}/facts"],
        "status": "ACTIVE"
      }
    ]
  }
}
```

Note

The key indicators are that `agent` and `agentMemory` both show `deployed`, and that the memory's strategies list contains one SEMANTIC and one EPISODIC strategy. Facts and events appear only after you talk to the agent in Challenge 2.

Troubleshooting

Common Issues

`agentcore memory` command not recognized:

- Confirm the CLI version with `agentcore --version`; the labs are written for 1.0.3 (`npm install -g @aws/agentcore@1.0.3`) 
- Verify you're in the project directory (`~/environment/CustomerServiceAgent`) 

`agentcore status` shows `agentMemory` as `local-only`:

- The memory is declared but not deployed yet; run `agentcore deploy` and check again 

Deployment fails after the change:

- Check that your IAM role has permissions for Bedrock AgentCore memory operations 
- Review error messages with: `agentcore --debug deploy` 
- Check the runtime logs with: `agentcore logs runtime --since 15m` 

The agent still asks for facts it was told before:

- Confirm `MEMORY_AGENTMEMORY_ID` reaches the runtime: `agentcore logs runtime --since 15m` should show no "memory" warnings 
- Long-term facts are extracted asynchronously; wait about 60 seconds between the session that states a fact and the session that asks about it

---

<!-- page: 10_lab-2-add-memory__test-memory -->
# Challenge 2: Test Memory with Multi-Session Recall

Challenge 2: Validate Memory with a 2-Session Test
Your Goal: Verify that your agent's memory works correctly by conducting a 2-session test. In the first session, introduce a specific detail. In the second session, ask about that detail. The agent should recall it without being told again.

Test it yourself first

Before looking at the solution below, try designing your own 2-session test. Think about what kind of detail you'd introduce in session 1 and how you'd query for it in session 2.

No spec needed here

This challenge runs and verifies what you already built; it changes no code, so run the commands directly or ask Kiro in chat. Specs are for changes to the agent, its tools, or its infrastructure.

Mission
Your agent now has both short-term and long-term memory configured and tuned. Your mission is to:
 
- Test short-term memory: Send multiple messages in the same session and verify the agent references earlier context 
- Test long-term memory: Start a completely new session and verify the agent recalls information from the previous session 
- Confirm cross-session recall: Ask about a detail that was only mentioned in session 1, while in session 2 
- Look inside the memory: list the facts the SEMANTIC strategy extracted with `agentcore memory record list` 
Understanding Session IDs
Each `agentcore invoke` sends one message. When you pass `--session-id`, AgentCore uses that ID to:
 
- Group messages within the same session (short-term memory, the EPISODIC namespace `/episodes/{actorId}/{sessionId}`) 
- Extract facts for future retrieval (long-term memory via the SEMANTIC strategy, namespace `/users/{actorId}/facts`) 
Different session IDs represent different conversations. The SEMANTIC strategy enables the agent to recall relevant information even when the session ID changes. The payload in this lab carries no `actorId`, so every session belongs to the actor `default`; Lab 4 scopes memory per customer by sending `actorId`.
Ideas for Your Test
 
- In session 1, tell the agent something specific about a customer (e.g., a name, an issue, a preference) 
- In session 2, ask about that detail without repeating it 
- The agent should find the relevant memory and reference it in its response 

Hint: Session ID Usage

Use the `--session-id` flag with `agentcore invoke` to control which session your message belongs to. Run the commands from `~/environment/CustomerServiceAgent`:

```
# Session 1 - every command with this session id shares short-term context
agentcore invoke --runtime agent --session-id memory-session-one-anycompany-telecom --payload '{"prompt":"..."}'

# Session 2 - a completely new session
agentcore invoke --runtime agent --session-id memory-session-two-anycompany-telecom --payload '{"prompt":"..."}'
```

Within each session, all your messages are automatically kept in context (short-term memory). Across sessions, the SEMANTIC strategy retrieves relevant past memories. The payload is single-quoted JSON, so write prompts without apostrophes.

Sample 2-Session Test

Session 1: Introduce a specific detail

```
agentcore invoke --runtime agent --session-id memory-session-one-anycompany-telecom --payload '{"prompt":"Hi, I am calling about my account. My name is Carlos Rivera and I have the Premium plan."}'
```

Then send a follow-up in the same session:

```
agentcore invoke --runtime agent --session-id memory-session-one-anycompany-telecom --payload '{"prompt":"I would like to note that I prefer to be contacted by email rather than phone for any follow-ups."}'
```

Wait about 60 seconds: long-term facts are extracted asynchronously after each turn.

Session 2: Query for the detail

```
agentcore invoke --runtime agent --session-id memory-session-two-anycompany-telecom --payload '{"prompt":"Do you have any notes about how Carlos Rivera prefers to be contacted?"}'
```

The agent should recall from its long-term memory that Carlos Rivera prefers email contact, even though this is a completely new session.

Verification Steps
Run the following 2-session test from `~/environment/CustomerServiceAgent` to validate memory:
Step 1: First session, introduce a detail

```
agentcore invoke --runtime agent --session-id memory-test-session-1-anycompany-telecom --payload '{"prompt":"I am a customer named Sarah Chen. I have slow internet between 7 and 9 PM. I have the Enterprise plan."}'
```

Wait for the agent's response, then wait about 60 seconds for the fact extraction. In the live test the facts were extracted 60 seconds after the first turn, but the second session only recalled them on a retry about two minutes later: if Step 2 answers "I don't have any information on Sarah Chen", run Step 3 to confirm the records exist, then repeat Step 2 with a new session ID.
Step 2: Second session, query for the detail

```
agentcore invoke --runtime agent --session-id memory-test-session-2-anycompany-telecom --payload '{"prompt":"What do you know about the internet issue Sarah Chen reported?"}'
```

Step 3: Look at the extracted facts
Copy the memory ID from `agentcore memory list --json`, then list the facts for the actor `default`:

```
agentcore memory list --json
agentcore memory record list --id <memoryId> --namespace /users/default/facts
```

You can also list the raw events of the first session:

```
agentcore memory event list --id <memoryId> --actor-id default --session-id memory-test-session-1-anycompany-telecom
```

Expected Results

Expected Output: Session 1

```
I understand you're experiencing slow internet speeds during peak hours (7-9 PM), Sarah.
As an Enterprise plan customer, you should be receiving priority bandwidth allocation.
Let me help you troubleshoot this issue...
```

Note

The exact response will vary based on your agent's system prompt and knowledge base content. The key point is that the agent acknowledges and engages with the information you provided.

Expected Output: Session 2

```
Here's what I have on file for Sarah Chen:
- Plan: Enterprise internet, $129.99/month
- Included: 1 Gbps speeds, a dedicated account manager, and an SLA
- Issue: Slow internet speeds between 7 and 9 PM
I don't have any other account details...
```

Note

The important thing is that the agent recalls the detail about Sarah Chen from the previous session without you repeating it. The exact phrasing will differ, but the agent should reference the slow internet speeds during peak hours and/or the Enterprise plan.

Expected Output: Memory records

```
{
  "memoryRecordSummaries": [
    {
      "memoryRecordId": "mem-<uuid>",
      "content": {
        "text": "Sarah Chen experiences slow internet speeds between 7 and 9 PM."
      },
      "memoryStrategyId": "agentMemory_Semantic-<id>",
      "namespaces": ["/users/default/facts/"],
      "createdAt": "2026-11-17T18:07:41.708Z"
    },
    {
      "memoryRecordId": "mem-<uuid>",
      "content": {
        "text": "Sarah Chen is a customer with the Enterprise internet plan, which costs $129.99/month and includes 1 Gbps speeds, a dedicated account manager, and an SLA."
      },
      "memoryStrategyId": "agentMemory_Semantic-<id>",
      "namespaces": ["/users/default/facts/"],
      "createdAt": "2026-11-17T18:07:41.708Z"
    }
  ]
}
```

`agentcore memory event list` prints one `events[]` entry per stored turn with `actorId`, `sessionId`, `eventId` and `eventTimestamp` (8 events for the two-turn first session, including the tool call and result).

Note

Each record is one fact the SEMANTIC strategy extracted (for example the customer's name, plan and reported issue). If the list is empty, wait another minute and run the command again.

Short-Term Memory Test (Bonus)
To also verify short-term memory (within-session context), send two messages in a single session:

```
agentcore invoke --runtime agent --session-id short-term-test-session-anycompany-telecom --payload '{"prompt":"My account number is CUST-005."}'
agentcore invoke --runtime agent --session-id short-term-test-session-anycompany-telecom --payload '{"prompt":"What account number did I just mention?"}'
```

The agent should reply with `CUST-005`, demonstrating it retains context within the same session.
Lab Completion Checklist
You've completed Lab 2 when you achieve:
 
- Memory inspected: `agentcore memory list` shows `agentMemory` with SEMANTIC and EPISODIC strategies 
- Agent Redeployed: `agentcore status` shows `agent` and `agentMemory` as `deployed` with the tuned retrieval configuration 
- Short-Term Memory Works: Agent references earlier messages within the same session 
- Long-Term Memory Works: Agent recalls details from session 1 when queried in session 2 
- 2-Session Test Passed: Introduced a detail in one session, confirmed recall in another, and `agentcore memory record list` shows the extracted fact 
Troubleshooting

Common Issues

Agent doesn't recall previous session:

- Wait about 60 seconds between sessions: facts are extracted asynchronously 
- Verify memory is deployed: `agentcore status` shows `agentMemory` as `deployed` 
- Check whether the fact exists: `agentcore memory record list --id <memoryId> --namespace /users/default/facts` 
- Try a more specific query in session 2 that closely matches what was discussed in session 1 

Agent repeats generic responses without memory context:

- Confirm the `SEMANTIC` strategy is in the `memories` block of `agentcore/agentcore.json` 
- Redeploy if you made changes: `agentcore deploy` 
- Check logs for memory retrieval errors: `agentcore logs runtime --since 15m` 

Session ID not working:

- Ensure you're using the `--session-id` flag with the same value on every message of a session 
- Each session ID must be a unique string (at least 33 characters, for example `memory-session-one-anycompany-telecom`) 
- Don't reuse the same session ID if you want to test cross-session recall

---

<!-- page: 11_lab-3-scale-tools -->
# Lab 3: Scale Agent Tools with Gateway

Scale Agent Tools with Gateway
In this lab, you'll connect your agent (the AnyCompany Telecom support agent in the guided sample) to real backend systems through Amazon Bedrock AgentCore Gateway. By the end of this lab, your agent will be able to look up customer billing information, create and query support tickets, and escalate cases to human agents. All of this happens through MCP (Model Context Protocol) tool calls routed via the Gateway.
What You'll Learn
 
- How AgentCore Gateway connects your agent to external tools via MCP protocol 
- How to configure your agent to use the Gateway endpoint for tool routing 
- How to invoke billing tools (get_billing_info, get_billing_history) 
- How to invoke ticketing tools (create_ticket, query_tickets, update_ticket) 
- How to invoke the escalation tool (escalate_to_human) 
- How to validate that tool responses match seeded backend data 
Why AgentCore Gateway Matters
So far, your agent can answer questions using its knowledge base and remember conversations. But a production customer service agent needs to take action, looking up real account data, creating tickets, and routing complex cases to humans.
AgentCore Gateway provides:
 
- MCP Protocol Routing: Routes tool calls from your agent to the correct backend service using the Model Context Protocol standard 
- Centralized Tool Management: All tools are registered at a single Gateway endpoint; no need to embed tool logic in the agent itself 
- Error Handling: Returns structured error responses when backends are unavailable or inputs are invalid, without crashing the agent session 
- Scalability: Handles concurrent tool invocations across multiple agent sessions 
Architecture
In this lab, you'll first create the backend systems using the `create_backend_systems` command. This provisions:

| MCP Endpoint | Tools | Backend |
| POST /billing/get_billing_info | Get customer account & balance | DynamoDB (billing table) |
| POST /billing/get_billing_history | Get billing history | DynamoDB (billing table) |
| POST /ticketing/create_ticket | Create a support ticket | DynamoDB (tickets table) |
| POST /ticketing/query_tickets | Query customer tickets | DynamoDB (tickets table) |
| POST /ticketing/update_ticket | Update ticket status | DynamoDB (tickets table) |
| POST /escalation/escalate_to_human | Escalate to human agent | DynamoDB (tickets table) |

After running `create_backend_systems`, the API Gateway URL is available in your environment as `$API_GATEWAY_URL`.
Prerequisites
 
- Completed Lab 2 (agent deployed, memory inspected and tuned) 
- AgentCore CLI installed and authenticated 
- Run `create_backend_systems` to create the backend infrastructure (see Challenge 1) 

Challenge Format

Each challenge states a goal and what the change must cover. You write a short brief, start a Quick Spec, review `requirements.md` and `tasks.md` against the Verification section, then let Kiro execute. Sample briefs are in expandable sections. Test challenges need no spec.

- Challenge 1: Connect Agent to AgentCore Gateway
- Challenge 2: Test All Gateway Tools

---

<!-- page: 12_lab-3-scale-tools__connect-gateway -->
# Challenge 1: Connect Agent to AgentCore Gateway

Challenge 1: Connect Your Agent to AgentCore Gateway
Your Goal: Create an AgentCore Gateway that exposes your backend Lambda functions as MCP tools, then connect your agent to the Gateway so it can access billing, ticketing, and escalation tools.

First: Create the Backend Systems

Before starting this challenge, run the following command to create the backend infrastructure (DynamoDB tables, Lambda functions, and seed data). This takes about 2 minutes:

```
create_backend_systems
```

This creates 3 Lambda functions (`billing-mcp`, `ticketing-mcp`, `escalation-mcp`) that serve as your backend tool implementations.

Write the brief yourself first

Compose your own spec brief from the bullets below before expanding the sample. The point is to state intent and acceptance criteria, not to find the right words for Kiro.

Mission
Your AnyCompany Telecom agent can answer questions and remember conversations, but it can't yet interact with real backend systems. Your mission is to:
 
- Create an AgentCore Gateway: Add a gateway with Lambda function targets to your project 
- Define tool schemas: Create JSON files describing each tool's inputs so the Gateway knows how to route calls 
- Connect the agent: Update your agent code to use the Gateway's MCP endpoint 
- Redeploy: Deploy the full stack including the new Gateway 
Context
AgentCore Gateway acts as a managed MCP server that exposes your Lambda functions as tools your agent can discover and invoke:

```
Agent → AgentCore Gateway (MCP) → Lambda Functions → DynamoDB
```

The Gateway uses the `lambdaFunctionArn` target type to invoke your Lambdas directly, no API Gateway intermediary needed. The CDK automatically:
 
- Creates the Gateway with an IAM role 
- Grants `lambda:InvokeFunction` permissions to the Gateway role 
- Injects the Gateway URL as an environment variable into your agent runtime 
The tools available through the Gateway are listed below. Every parameter not marked optional is required by the Lambda handler, so mark it `required` in the tool schema file:

| Tool | Lambda Function | Parameters |
| get_billing_info | billing-mcp | customer_id |
| get_billing_history | billing-mcp | customer_id, months (optional) |
| create_ticket | ticketing-mcp | customer_id, subject, description, priority (optional, default Medium) |
| query_tickets | ticketing-mcp | customer_id, status (optional) |
| update_ticket | ticketing-mcp | customer_id, ticket_id, status (optional), notes (optional) |
| escalate_to_human | escalation-mcp | customer_id, ticket_id, reason, context (optional) |

What your spec must cover
 
- The gateway must be named `ToolGateway`, use protocol type `MCP`, and expose the 3 backend Lambda functions (`billing-mcp`, `ticketing-mcp`, `escalation-mcp`) as MCP tools the agent can call. Keep the name short: the CDK composes `CustomerServiceAgent_default_<gateway>` and rejects names longer than 48 characters. 
- The gateway must use the `lambdaFunctionArn` target type, not the `apiGateway` type, because the Lambdas use AWS_PROXY integration which does not produce a valid OpenAPI spec. 
- The gateway must have 3 targets in `agentcore.json`, each referencing a Lambda ARN and a `toolSchemaFile`, with tool schema JSON files that define the input schema for each tool (`billing-mcp`: `get_billing_info`, `get_billing_history`; `ticketing-mcp`: `create_ticket`, `query_tickets`, `update_ticket`; `escalation-mcp`: `escalate_to_human`). 
- The agent's MCP client must read the CDK-injected gateway URL environment variable (`AGENTCORE_GATEWAY_TOOLGATEWAY_URL`). 
- The agent code opens the MCP client lazily (inside `_get_agent` in `app/agent/main.py`) and adds the Gateway tools to the agent's tool list. 
- The change is complete when the full stack is redeployed and `agentcore status` shows the gateway `deployed` with 3 targets. 
Each of these should appear as an acceptance criterion in `requirements.md`; the Verification section at the bottom of this page is the test.

Hint: Why lambdaFunctionArn instead of apiGateway?

AgentCore Gateway supports multiple target types. The `apiGateway` target type parses the OpenAPI spec exported from API Gateway, but Lambda Proxy integrations (`AWS_PROXY`) don't include `responses` in their OpenAPI export, causing validation failures.

The `lambdaFunctionArn` target type bypasses this by invoking Lambdas directly with inline tool schemas you define. This is simpler and more reliable for Lambda-backed tools.

Your `agentcore.json` gateway config should look like:

```
{
  "name": "ToolGateway",
  "targets": [
    {
      "name": "BillingTools",
      "targetType": "lambdaFunctionArn",
      "lambdaFunctionArn": {
        "lambdaArn": "arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:billing-mcp",
        "toolSchemaFile": "billing-tools.json"
      }
    }
  ]
}
```

Start a spec
In the Kiro chat panel open a new session and choose Quick Spec (or Spec if you want to approve requirements, design, and tasks separately), or run `/spec new connect-gateway` in `kiro-cli chat` from your agent project folder. Paste your brief, then review `requirements.md` against the bullets above and `tasks.md` for the redeploy step. When the task list looks right, tell Kiro "Run all tasks for this spec".

Sample spec brief

Paste this into Quick Spec (or after `/spec new connect-gateway`).

```
Create an AgentCore Gateway named "ToolGateway" with protocol type MCP that exposes my
3 backend Lambda functions as MCP tools the agent can call.

The Lambda functions are:
- billing-mcp (tools: get_billing_info, get_billing_history)
- ticketing-mcp (tools: create_ticket, query_tickets, update_ticket)
- escalation-mcp (tool: escalate_to_human)

Constraints:
- Use the "lambda-function-arn" gateway target type (not api-gateway type) since my
  Lambdas use AWS_PROXY integration which doesn't produce a valid OpenAPI spec.
- Configure 3 targets in agentcore.json with targetType "lambdaFunctionArn", each
  referencing a Lambda ARN and a toolSchemaFile, with tool schema JSON files that
  define the input schema for each tool.
- The agent's MCP client must read the CDK-injected gateway URL env var
  (AGENTCORE_GATEWAY_TOOLGATEWAY_URL).
- Add the MCP client as app/agent/mcp_client.py and open it lazily inside _get_agent in
  app/agent/main.py, extending the agent's tools with the Gateway tools.
- My account ID is available via `aws sts get-caller-identity` and the region is us-east-1.
- The change is complete when the full stack is redeployed and `agentcore status` shows
  the gateway deployed with 3 targets.

Turn this into a spec: write the requirements with acceptance criteria that include
every constraint above, then the design, then the task list. Ask me clarifying
questions before drafting. Wait for my approval before executing the tasks.
```

Manual Steps (CLI Commands)

Step 1: Add the AgentCore Gateway to your project

```
# or cd ~/environment/<YourAgentName>
cd ~/environment/CustomerServiceAgent
agentcore add gateway --name ToolGateway --protocol-type MCP --authorizer-type NONE --exception-level debug
```

`--protocol-type MCP` makes the injected Gateway URL the complete MCP endpoint (it ends in `/mcp`); without it the URL is a bare origin and the Strands MCP client fails with `Connection closed`. The protocol type cannot be changed on an existing gateway, so set it now. `--exception-level` accepts only the lowercase value `debug`; it makes the Gateway return detailed error messages while you develop. The name stays short on purpose: the CDK names the AWS resource `CustomerServiceAgent-default-ToolGateway` and rejects composed names longer than 48 characters.

Step 2: Edit `agentcore/agentcore.json`

Replace the gateway targets section with `lambdaFunctionArn` targets. Each target needs a Lambda ARN and a `toolSchemaFile` pointing to a JSON file with tool definitions.

Get your account ID:

```
aws sts get-caller-identity --query Account --output text
```

Update the targets in `agentcore.json`:

```
"targets": [
  {
    "name": "BillingTools",
    "targetType": "lambdaFunctionArn",
    "lambdaFunctionArn": {
      "lambdaArn": "arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:billing-mcp",
      "toolSchemaFile": "billing-tools.json"
    }
  },
  {
    "name": "TicketingTools",
    "targetType": "lambdaFunctionArn",
    "lambdaFunctionArn": {
      "lambdaArn": "arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:ticketing-mcp",
      "toolSchemaFile": "ticketing-tools.json"
    }
  },
  {
    "name": "EscalationTools",
    "targetType": "lambdaFunctionArn",
    "lambdaFunctionArn": {
      "lambdaArn": "arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:escalation-mcp",
      "toolSchemaFile": "escalation-tools.json"
    }
  }
]
```

Step 3: Create tool schema files

Create `billing-tools.json` in the project root (not in `agentcore/`):

```
[
  {
    "name": "get_billing_info",
    "description": "Get current billing information for a customer",
    "inputSchema": {
      "type": "object",
      "properties": {
        "customer_id": {
          "type": "string",
          "description": "The customer ID (e.g. CUST-001)"
        }
      },
      "required": ["customer_id"]
    }
  },
  {
    "name": "get_billing_history",
    "description": "Get billing history for a customer over recent months",
    "inputSchema": {
      "type": "object",
      "properties": {
        "customer_id": { "type": "string", "description": "The customer ID" },
        "months": {
          "type": "integer",
          "description": "Number of months of history (default 6)"
        }
      },
      "required": ["customer_id"]
    }
  }
]
```

Create `ticketing-tools.json` and `escalation-tools.json` similarly with their respective tool definitions.

Important

Tool schema files must be placed in the project root directory (same level as `agentcore/` and `app/`), not inside the `agentcore/` folder. The CDK resolves the `toolSchemaFile` path relative to the project root.

Alternative to editing the JSON by hand: `agentcore add gateway-target` appends one target to the gateway from a file that holds a single target object. For example, with `billing-target.json` in the project root containing the `BillingTools` object above:

```
agentcore add gateway-target --gateway ToolGateway --target-configuration file://billing-target.json
```

Repeat for the ticketing and escalation targets. The result in `agentcore.json` is the same.

Step 4: Create `app/agent/mcp_client.py`

The template has no MCP client module, so add one next to `main.py`. It opens a Strands `MCPClient` against the CDK-injected gateway URL (the `mcp` package is already installed as a dependency of `strands-agents`):

```
import os
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

def get_streamable_http_mcp_client() -> MCPClient | None:
    endpoint = os.environ.get("AGENTCORE_GATEWAY_TOOLGATEWAY_URL", "")
    if not endpoint:
        return None
    return MCPClient(lambda: streamablehttp_client(endpoint))
```

Then wire it into `app/agent/main.py` inside `_get_agent`, so the client opens lazily on the first request and its tools are added to the agent:

```
from mcp_client import get_streamable_http_mcp_client

@lru_cache(maxsize=128)
def _get_agent(session_id: str, actor_id: str) -> Agent:
    agent_tools = list(tools)
    mcp_client = get_streamable_http_mcp_client()
    if mcp_client is not None:
        mcp_client.start()
        agent_tools.extend(mcp_client.list_tools_sync())
    return Agent(
        model=load_model(),
        session_manager=get_memory_session_manager(session_id, actor_id),
        conversation_manager=_make_conversation_manager(),
        system_prompt=DEFAULT_SYSTEM_PROMPT,
        tools=agent_tools,
    )
```

Step 5: Deploy

```
agentcore deploy
```

Verification
After deploying, confirm the Gateway is deployed:

```
agentcore status
```

Expected Output

```
$ agentcore status
 ── resources
 ❯ ▾agent agent
   │ ├─ runtime  agent deployed
   │ └─ memory   agentMemory deployed
   ▾project shared resources
     └─▾gateway  ToolGateway deployed
       ├─ gateway-target BillingTools deployed
       ├─ gateway-target TicketingTools deployed
       └─ gateway-target EscalationTools deployed
[↑↓/jk] navigate  [←→] collapse/expand  [enter] open  [esc] back  [ctrl+c] quit
```

`agentcore status` is interactive in a terminal (press `Ctrl+C` to leave (`Esc` opens the filter, it does not exit) it). `agentcore status --json` prints the same tree as JSON, which is what Kiro and scripts should read:

```
{
  "projectName": "CustomerServiceAgent",
  "target": "default",
  "region": "us-east-1",
  "resources": [
    {
      "resourceType": "runtime",
      "name": "agent",
      "deploymentState": "deployed",
      "arn": "arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:runtime/CustomerServiceAgent_default_agent-<agent-id>"
    },
    {
      "resourceType": "memory",
      "name": "agentMemory",
      "deploymentState": "deployed",
      "arn": "arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:memory/CustomerServiceAgent_default_agentMemory-<memory-id>"
    },
    {
      "resourceType": "gateway",
      "name": "ToolGateway",
      "deploymentState": "deployed",
      "arn": "arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:gateway/customerserviceagent-default-toolgateway-<gateway-id>",
      "children": [
        {
          "resourceType": "gateway-target",
          "name": "BillingTools",
          "deploymentState": "deployed",
          "id": "<target-id>"
        },
        {
          "resourceType": "gateway-target",
          "name": "TicketingTools",
          "deploymentState": "deployed",
          "id": "<target-id>"
        },
        {
          "resourceType": "gateway-target",
          "name": "EscalationTools",
          "deploymentState": "deployed",
          "id": "<target-id>"
        }
      ]
    }
  ]
}
```

The status tree lists the runtime `agent`, the memory `agentMemory` and the gateway `ToolGateway` as `deployed`, with the three targets (`BillingTools`, `TicketingTools`, `EscalationTools`) nested under the gateway.

You can also verify the Gateway exists in your account (the AWS resource name is `CustomerServiceAgent-default-ToolGateway`):

```
aws bedrock-agentcore-control list-gateways --query 'items[].{name:name,status:status,protocolType:protocolType}'
```

```
[
  {
    "name": "CustomerServiceAgent-default-ToolGateway",
    "status": "READY",
    "protocolType": "MCP"
  }
]
```

Note

The Gateway URL is automatically injected as `AGENTCORE_GATEWAY_TOOLGATEWAY_URL` into your agent runtime (together with `AGENTCORE_GATEWAY_TOOLGATEWAY_ARN` and `AGENTCORE_GATEWAY_TOOLGATEWAY_AUTH_TYPE`). You don't need to set this manually.

Troubleshooting

Common Issues

CDK synth fails with "Cannot find asset":

- Tool schema files (`*-tools.json`) must be in the project root, not in `agentcore/` 
- Verify: `ls ~/environment/CustomerServiceAgent/*-tools.json` (or `~/environment/<YourAgentName>/` if you chose your own name) 

Validation error "unknown keys: lambdaArn":

- The `lambdaArn` field must be nested inside a `lambdaFunctionArn` object: 

```
"lambdaFunctionArn": {
  "lambdaArn": "arn:aws:lambda:...",
  "toolSchemaFile": "billing-tools.json"
}
``` 
- NOT at the top level of the target 

"Failed to parse OpenAPI specification: responses is missing":

- This means you're using `targetType: "apiGateway"`, switch to `"lambdaFunctionArn"` instead 
- Lambda Proxy (`AWS_PROXY`) integrations don't export valid OpenAPI specs 

Synth fails with "The field Gateway name is 51 characters long but must be less than or equal to 48 characters":

- The CDK composes `<project>_default_<gateway>`; with the project `CustomerServiceAgent` the gateway name must be 12 characters or fewer. Use `ToolGateway`. 

Agent returns `MCPClientInitializationError: the client initialization failed` and the runtime log ends with `McpError: Connection closed`:

- The gateway was added without `--protocol-type MCP`, so `AGENTCORE_GATEWAY_TOOLGATEWAY_URL` is a bare origin without `/mcp`. The protocol type cannot be changed in place: set `agentCoreGateways` to `[]` in `agentcore/agentcore.json`, run `agentcore deploy`, then add the gateway again with `--protocol-type MCP`, restore the targets and deploy. 

Tool call returns `{"statusCode": 404, ... "Unknown path: "}`:

- The backend Lambdas predate the Gateway branch in their handlers. Run `create_backend_systems` again (it updates the function code in place) and retry. 

Gateway shows `local-only`:

- The gateway is declared but the deploy has not published it yet: run `agentcore deploy`, wait for it to finish, and check `agentcore status` again 
- Or run `agentcore --debug deploy` to see verbose deployment output 

Agent can't find tools at runtime:

- Check that `app/agent/mcp_client.py` reads `AGENTCORE_GATEWAY_TOOLGATEWAY_URL` 
- Ensure `_get_agent` in `app/agent/main.py` starts the MCP client and extends the tools list with `list_tools_sync()` 
- Verify the gateway is `deployed`: check with `agentcore status` 
- Look for connection errors in `agentcore logs runtime --since 15m`

---

<!-- page: 13_lab-3-scale-tools__test-tools -->
# Challenge 2: Test All Gateway Tools

Challenge 2: Test Billing, Ticketing, and Escalation Tools
Your Goal: Invoke your agent and verify that all tools connected through AgentCore Gateway work correctly. Retrieve billing information for a known customer, create a support ticket, query tickets back, and test escalation to a human agent.

Test it yourself first

Before looking at the solutions below, try interacting with your agent naturally. Ask it to look up billing info, create a ticket, or escalate an issue. See if it correctly invokes the tools through the Gateway.

No spec needed here

This challenge runs and verifies what you already built; it changes no code, so run the commands directly or ask Kiro in chat. Specs are for changes to the agent, its tools, or its infrastructure.

Mission
Your agent is now connected to the backend systems via AgentCore Gateway. Your mission is to:
 
- Test billing tools: Ask the agent to retrieve billing info for customer `CUST-001` (Sarah Chen, Premium plan) and verify the data matches seeded records 
- Test ticketing tools: Ask the agent to create a new support ticket, then query tickets to confirm it was created 
- Test escalation: Ask the agent to escalate a case to a human agent and verify the handoff 
Test Data Reference
Your environment has seeded data (created by `create_backend_systems`). Here's what you should expect for customer `CUST-001`:

| Field | Expected Value |
| Customer ID | CUST-001 |
| Name | Sarah Chen |
| Plan | Premium |
| Account Status | Active |

This customer has billing records and existing tickets in the system that your agent should be able to retrieve.
Part 1: Test Billing Tools

Hint: Testing get_billing_info

Start an agent session and ask a natural language question about a customer's billing. The agent should recognize it needs to call the `get_billing_info` tool and route the request through the Gateway.

Use customer `CUST-001` (Sarah Chen) since this is a known seeded record you can validate against.

Sample Conversation: Billing

Run the commands from `~/environment/CustomerServiceAgent`. Each `agentcore invoke` sends one message; the same `--session-id` keeps the messages in one conversation.

```
agentcore invoke --runtime agent --session-id tools-test-billing-session-anycompany --payload '{"prompt":"Can you look up the billing information for customer CUST-001?"}'
```

The agent should call `get_billing_info` with `customer_id: CUST-001` and return Sarah Chen's account details including her Premium plan, balance, and usage information.

Follow up with billing history in the same session:

```
agentcore invoke --runtime agent --session-id tools-test-billing-session-anycompany --payload '{"prompt":"Show me the billing history for this customer."}'
```

The agent should call `get_billing_history` and return past billing records.

Expected Output: Billing

```
> Can you look up the billing information for customer CUST-001?

I've retrieved the billing information for customer CUST-001. Here are the details:

- **Customer:** Sarah Chen
- **Plan:** Premium
- **Account Status:** Active
- **Current Balance:** $149.99
- **Plan Charges:** $99.99/month
- **Usage Charges:** $50.00

The account is in good standing with no overdue payments.
```

Note

The exact values (balance, charges) will match what's in your seeded DynamoDB data. The response wording will vary based on your agent's system prompt, but the data values should be consistent with the seeded records.

Part 2: Test Ticketing Tools

Hint: Testing create_ticket and query_tickets

Ask the agent to create a ticket for a customer, providing a subject and description. Then ask it to list all tickets for that customer. The newly created ticket should appear in the results.

This tests two tools in sequence: `create_ticket` followed by `query_tickets`.

Sample Conversation: Ticketing

Continue in a new session.

Create a ticket:

```
agentcore invoke --runtime agent --session-id tools-test-ticketing-session-anycompany --payload '{"prompt":"Create a support ticket for customer CUST-001 with subject Internet speed issue and description Customer reports slow download speeds during evening hours. Set priority to Medium."}'
```

The agent should call `create_ticket` and confirm the ticket was created with a ticket ID.

Query tickets back:

```
agentcore invoke --runtime agent --session-id tools-test-ticketing-session-anycompany --payload '{"prompt":"Show me all tickets for customer CUST-001."}'
```

The agent should call `query_tickets` and return a list that includes both the existing seeded tickets and the one you just created.

Expected Output: Ticketing

Create ticket response:

```
> Create a support ticket for customer CUST-001 with subject "Internet speed issue"
> and description "Customer reports slow download speeds during evening hours."
> Set priority to Medium.

I've created a new support ticket for customer CUST-001:

- **Ticket ID:** TKT-001-XXXX
- **Subject:** Internet speed issue
- **Priority:** Medium
- **Status:** Open
- **Created:** [current timestamp]

The ticket has been logged in the system.
```

Query tickets response:

```
> Show me all tickets for customer CUST-001.

Here are the tickets for customer CUST-001 (Sarah Chen):

1. **TKT-001-0001**: [Existing seeded ticket subject]
   - Status: Open | Priority: High | Created: 2024-XX-XX

2. **TKT-001-XXXX**: Internet speed issue
   - Status: Open | Priority: Medium | Created: [just now]
```

Note

The ticket IDs and exact details will vary. The important validation is that: (1) the ticket you just created appears in the query results, and (2) previously seeded tickets for CUST-001 are also returned.

Part 3: Test Escalation Tool

Hint: Testing escalate_to_human

Ask the agent to handle a situation that warrants human intervention, such as a refund request or an unresolved issue after multiple attempts. The agent should recognize this needs escalation and call the `escalate_to_human` tool.

You can either let the agent decide when to escalate naturally, or explicitly ask it to escalate.

Sample Conversation: Escalation

Continue in a new session and send a message that warrants escalation:

```
agentcore invoke --runtime agent --session-id tools-test-escalation-session-anycompany --payload '{"prompt":"Customer CUST-001 is requesting a full refund of $149.99 for this month charges due to repeated service outages. I have already tried troubleshooting and the issue persists. Please escalate this to a human agent for review."}'
```

The agent should call `escalate_to_human` with the customer ID, the ticket ID (the Lambda requires one: the agent may first call `query_tickets` or `create_ticket` to get it), a reason, and context about the issue.

Expected Output: Escalation

```
> Customer CUST-001 is requesting a full refund of $149.99 for this month's charges
> due to repeated service outages. I've already tried troubleshooting and the issue
> persists. Please escalate this to a human agent for review.

I've escalated this case to a human agent for review. Here are the escalation details:

- **Customer:** CUST-001 (Sarah Chen)
- **Reason:** Refund request due to repeated service outages
- **Context:** Customer requesting $149.99 refund, troubleshooting already attempted
- **Status:** Escalated to human agent

A human support specialist will review this case and follow up with the customer.
The case reference has been logged for tracking.
```

Note

The exact response will depend on your agent's system prompt. The key validation is that the agent successfully invoked the `escalate_to_human` tool and confirmed the handoff.

Validation Checklist
Run through these checks to confirm all tools are working:
Billing validation:

```
agentcore invoke --runtime agent --session-id validate-billing-session-anycompany-01 --payload '{"prompt":"Get billing info for customer CUST-001 and tell me their plan name and account status."}'
```

Confirm the response includes: Plan: Premium, Status: Active
Ticketing validation:

```
agentcore invoke --runtime agent --session-id validate-ticketing-session-anycompany-01 --payload '{"prompt":"Create a ticket for CUST-001 with subject Test ticket and description Validation test with Low priority. Then query all tickets for CUST-001."}'
```

Confirm: (1) Ticket is created with an ID returned, (2) Query results include the new ticket
Lab Completion Checklist
You've completed Lab 3 when you achieve:
 
- Gateway Connected: `agentcore status` shows `ToolGateway` as `deployed` with 3 targets, and the agent reads `AGENTCORE_GATEWAY_TOOLGATEWAY_URL` 
- Billing Tool Works: `get_billing_info` returns correct data for CUST-001 (Sarah Chen, Premium plan) 
- Ticketing Tools Work: `create_ticket` creates a ticket and `query_tickets` retrieves it 
- Escalation Tool Works: `escalate_to_human` successfully hands off a case 
- Data Matches: Retrieved billing information matches seeded DynamoDB records 
- Error Handling: Agent continues conversation even if an invalid customer ID is used (e.g., try `CUST-999`) 
Bonus Challenge: Test Error Handling
Try invoking the agent with an invalid customer ID to verify error handling:

```
agentcore invoke --runtime agent --session-id error-test-session-anycompany-telecom-01 --payload '{"prompt":"Look up billing information for customer INVALID-ID."}'
```

The agent should receive an error response from the Gateway (customer not found) and handle it gracefully, informing you that the customer wasn't found rather than crashing.

Expected Error Handling

```
> Look up billing information for customer INVALID-ID.

I wasn't able to find billing information for customer "INVALID-ID." This customer
ID doesn't appear to exist in our system. Could you double-check the customer ID
and try again? Customer IDs typically follow the format CUST-XXX.
```

Note

The agent should gracefully handle the error and continue the conversation. It should NOT crash, disconnect, or terminate the session. This validates that AgentCore Gateway returns structured error responses that the agent can interpret.

Troubleshooting

Common Issues

Agent doesn't call any tools:

- Verify the Gateway is deployed: `agentcore status` shows `ToolGateway` as `deployed` with 3 targets 
- Check that `_get_agent` in `app/agent/main.py` starts the MCP client and adds `list_tools_sync()` to the tools 
- Try being more explicit in your request: "Use the get_billing_info tool to look up CUST-001" 
- Review agent logs for tool invocation attempts: `agentcore logs runtime --since 15m` 

Tool call returns timeout:

- Lambda cold starts can cause the first invocation to be slow (up to 5 seconds) 
- Try the request again. Subsequent calls should be faster 
- Verify the backend is reachable through the REST API that `create_backend_systems` created (`API_GATEWAY_URL` is set in your terminal): `curl -X POST $API_GATEWAY_URL/billing/get_billing_info -H "Content-Type: application/json" -d '{"customer_id": "CUST-001"}'` 

Tool returns empty or incorrect data:

- Verify you have run `create_backend_systems` to create and seed the DynamoDB tables 
- Check the customer ID format (e.g., `CUST-001`, not `cust-001`) 
- Test the backend directly to isolate whether the issue is in the agent or the backend: 

```
curl -X POST $API_GATEWAY_URL/billing/get_billing_info \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "CUST-001"}'
``` 

Escalation tool not recognized:

- Ensure the `EscalationTools` target is in the gateway's `targets` list in `agentcore/agentcore.json` and that `escalation-tools.json` defines `escalate_to_human` 
- Verify the Lambda function is deployed: `aws lambda get-function --function-name escalation-mcp --query Configuration.FunctionName` 
- Redeploy after any change to the targets: `agentcore deploy`
---

<!-- page: 14_lab-4-identity -->
# Lab 4: Identity Management

Provide Identity Management to Your Agent
In this lab, you scope every tool call your agent makes (the AnyCompany Telecom support agent in the guided sample) to the customer the request belongs to. The customer identity arrives with each request, and the agent enforces that it only touches that customer's billing, tickets, and escalations, preventing cross-customer data leakage.
What You'll Learn
 
- How the customer identity reaches the agent: as `actorId` in the invoke payload (the template's `parse.py` reads it and the memory namespaces already use it) or as the Runtime user ID 
- How to enforce the boundary in code with a Strands hook that cancels any Gateway tool call for another customer 
- How to invoke the agent as a specific customer 
- How to verify that cross-customer access is denied without terminating the conversation 
Why Identity Matters
Your agent currently has access to all customer records in the backend systems. Without identity enforcement:
 
- Any caller could query another customer's billing data 
- Support tickets from other customers could be exposed 
- Usage charges could leak across customer boundaries 
Scoping by the request identity solves this:
 
- Scoping data access: Billing, ticket, and escalation tool calls are checked against the authenticated customer before they reach the Gateway 
- Denying cross-customer access: Requests for another customer's data return an access-denied indication without exposing any data 
- Preserving session continuity: Access denials don't terminate the conversation; the agent handles the boundary and continues 
In production, Amazon Bedrock AgentCore Identity carries the identity in a JWT validated by an inbound authorizer on the runtime and manages outbound credentials for the tools (`agentcore add credentials`). The lab enforces the same boundary from the identity in the request so you can test it from the CLI. See [AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html).
Prerequisites
 
- Completed Lab 3 (agent connected to backend systems via MCP Gateway, billing/ticketing/escalation tools working) 
- AgentCore CLI installed and authenticated 
- At least 2 customer personas available (created by `create_backend_systems` in Lab 3, e.g., CUST-001, CUST-002) 

Challenge Format

Each challenge states a goal and what the change must cover. You write a short brief, start a Quick Spec, review `requirements.md` and `tasks.md` against the Verification section, then let Kiro execute. Sample briefs are in expandable sections. Test challenges need no spec.

- Challenge 1: Scope Data Access to the Authenticated Customer
- Challenge 2: Test Cross-Customer Data Isolation

---

<!-- page: 15_lab-4-identity__configure-identity -->
# Challenge 1: Scope Data Access to the Authenticated Customer

Challenge 1: Scope Data Access to the Authenticated Customer
Your Goal: Make the agent treat the customer identity that arrives with each request as the only customer whose billing, tickets, and escalations it may touch.

Write the brief yourself first

Compose your own spec brief from the bullets below before expanding the sample. The point is to state intent and acceptance criteria, not to find the right words for Kiro.

Mission
Your agent currently has unrestricted access to all customer data through the MCP Gateway tools. Your mission is to:
 
- Enforce the boundary in code: cancel any Gateway tool call whose `customer_id` differs from the request's identity before it reaches the Gateway 
- Tell the agent who it serves: the system prompt states the authenticated customer ID and forbids other customers' data 
- Redeploy the agent: apply the change so it takes effect on the running agent 
Context
The customer identity arrives with every request:
 
- As `actorId` in the invoke payload: `agentcore invoke --runtime agent --payload '{"prompt":"...","actorId":"CUST-001"}'`. The template's `app/agent/parse.py` already reads it, and the memory namespaces (`/users/{actorId}/facts`) already use it, so memory is scoped per customer as soon as you send it. 
- Or as the Runtime user ID: `agentcore invoke --user-id CUST-001` sets the `X-Amzn-Bedrock-AgentCore-Runtime-User-Id` header. The template does not read it; the lab uses `actorId`. 
- In production, the identity is a claim in a JWT validated by an inbound authorizer on the runtime (`agentcore add runtime --authorizer-type CUSTOM_JWT`), and `agentcore add credentials api-key|oauth` manages the outbound credentials the tools need. See [AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html). 
What scoping changes:

| Behavior | Without scoping | With scoping |
| Billing queries | Returns any customer's billing data | Returns only the authenticated customer's billing data |
| Ticket queries | Returns any customer's tickets | Returns only the authenticated customer's tickets |
| Usage charges | Part of any customer's billing history | Part of the authenticated customer's billing history only |
| Cross-customer request | Data is returned freely | Access-denied indication returned; no data exposed |
| Session after denial | N/A | Conversation continues normally |

Every Gateway tool takes a `customer_id` input. The agent compares it with the request's `actorId` before the call leaves the agent: a Strands hook on `BeforeToolCallEvent` cancels the call and returns an access-denied message as the tool result, so the model answers the customer without any foreign data.
What your spec must cover
 
- Every Gateway tool call whose `customer_id` input differs from the request's `actorId` is canceled before it reaches the Gateway and returns an access-denied result to the model. 
- The denial does not end the conversation; the authenticated customer's own data remains accessible in the same session. 
- The system prompt states the authenticated customer ID and forbids requesting other customers' data. 
- Memory stays scoped to the same `actorId` (the template already does this; the spec must not break it). 
- The change is complete when the agent is redeployed and the Verification below passes. 
Each of these should appear as an acceptance criterion in `requirements.md`; the Verification section at the bottom of this page is the test.

Hint: Strands hooks

Strands Agents SDK lets you observe and modify the agent loop with hooks. A `HookProvider` registers callbacks for events such as `BeforeToolCallEvent`; the event carries `tool_use` (name and `input`) and a `cancel_tool` attribute. Setting `event.cancel_tool = "<message>"` skips the tool and feeds the message back to the model as the tool result.

Because `_get_agent` in `app/agent/main.py` already receives `actor_id`, you can build the hook with the request's identity and pass it as `hooks=[...]` to `Agent(...)`.

Documentation: [Strands hooks](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/hooks/).

Start a spec
In the Kiro chat panel open a new session and choose Quick Spec (or Spec if you want to approve requirements, design, and tasks separately), or run `/spec new scope-customer-access` in `kiro-cli chat` from your agent project folder. Paste your brief, then review `requirements.md` against the bullets above and `tasks.md` for the redeploy step. When the task list looks right, tell Kiro "Run all tasks for this spec".

Sample spec brief

Paste this into Quick Spec (or after `/spec new scope-customer-access`).

```
Enforce per-customer data access on my agent in ~/environment/CustomerServiceAgent.
The customer identity arrives as actorId in the invoke payload (app/agent/parse.py
already reads it). I need the agent to:
- Cancel any Gateway tool call whose customer_id differs from the request's actorId
  before it reaches the Gateway, returning an access-denied result to the model
  (use a Strands BeforeToolCallEvent hook built with the request's actor_id)
- Keep the conversation going after a denial; the authenticated customer's own
  billing, tickets, and escalations must remain accessible in the same session
- State the authenticated customer ID in the system prompt and forbid requesting
  other customers' data
- Keep the memory scoped to the same actorId (do not change memory/session.py)

The change is complete when the agent is redeployed and a request authenticated as
CUST-001 for CUST-002's billing returns an access-denied answer with no CUST-002 data.

Turn this into a spec: write the requirements with acceptance criteria that include
every constraint above, then the design, then the task list. Ask me clarifying
questions before drafting. Wait for my approval before executing the tasks.
```

Manual Steps (CLI Commands)

Run every command from `~/environment/CustomerServiceAgent`.

Step 1: Create `app/agent/scope.py`

```
from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

class CustomerScopeHook(HookProvider):
    """Cancel any tool call that targets a customer other than the authenticated one."""

    def __init__(self, actor_id: str) -> None:
        self.actor_id = actor_id

    def register_hooks(self, registry: HookRegistry, **kwargs) -> None:
        registry.add_callback(BeforeToolCallEvent, self._check_customer)

    def _check_customer(self, event: BeforeToolCallEvent) -> None:
        requested = (event.tool_use.get("input") or {}).get("customer_id")
        if requested and requested != self.actor_id:
            event.cancel_tool = (
                f"Access denied: this session is authenticated as {self.actor_id} "
                f"and cannot access data for {requested}."
            )
```

Step 2: Register the hook in `app/agent/main.py`

Import the hook and pass it to the agent inside `_get_agent`, together with the customer ID in the system prompt:

```
from scope import CustomerScopeHook

@lru_cache(maxsize=128)
def _get_agent(session_id: str, actor_id: str) -> Agent:
    ...
    return Agent(
        model=load_model(),
        session_manager=get_memory_session_manager(session_id, actor_id),
        conversation_manager=_make_conversation_manager(),
        system_prompt=(
            f"{DEFAULT_SYSTEM_PROMPT}\n\nThe authenticated customer is {actor_id}. "
            "Never request another customer's data."
        ),
        tools=agent_tools,
        hooks=[CustomerScopeHook(actor_id)],
    )
```

Step 3: Redeploy the agent

```
agentcore deploy
```

Step 4: Check status

```
agentcore status
```

Verification
After redeploying, invoke the agent as CUST-001 and ask for its own billing details:

```
cd ~/environment/CustomerServiceAgent
agentcore invoke --runtime agent --session-id scope-test-session-anycompany-cust001 --payload '{"prompt":"What are my current billing details?","actorId":"CUST-001"}'
```

The agent should return billing data for CUST-001 only.

Expected Output

```
Hi Sarah, here are your current billing details.
- Account status: Active
- Plan: Premium
- Billing period: April 2024
- Plan charges: $79.99
- Usage charges: $12.01
- Total due: $92.00
- Due date: April 15, 2024
- Payment status: Pending
I can also pull your billing history or help with anything else on your account.
```

(Assembled from the `contentBlockDelta` text fragments; the stream also shows a `toolUse` block named `BillingTools___get_billing_info`.)

Note

Your exact output will vary depending on the seeded data for CUST-001. The key indicator is that the agent returns data specific to CUST-001 and does not include any other customer's records. Challenge 2 tests the denial.

Troubleshooting

Common Issues

`agentcore invoke` rejects the payload:

- Confirm the CLI version with `agentcore --version`; the labs are written for 1.0.3 (`npm install -g @aws/agentcore@1.0.3`) 
- The payload is one JSON object in single quotes: `'{"prompt":"...","actorId":"CUST-001"}'` 

Agent returns another customer's data despite the hook:

- Confirm the agent was redeployed after the change: `agentcore deploy` 
- Confirm `hooks=[CustomerScopeHook(actor_id)]` is passed to `Agent(...)` in `_get_agent` 
- Confirm the Gateway tool inputs use the key `customer_id` (see the tool schema files from Lab 3) 

`actorId` missing from the payload:

- The template falls back to `default`, so the agent is not scoped to any customer; always send `actorId` 

Deployment fails after the change:

- Check the import path in `main.py`: `from scope import CustomerScopeHook` (the file sits next to `main.py`) 
- Review error messages: `agentcore --debug deploy` and `agentcore logs runtime --since 15m` 

Not sure which customer IDs to use:

- The seeded data includes CUST-001 through CUST-010 
- Each has billing records and support tickets you can query

---

<!-- page: 16_lab-4-identity__test-isolation -->
# Challenge 2: Test Cross-Customer Data Isolation

Challenge 2: Verify Cross-Customer Access is Denied
Your Goal: Authenticate as one customer (CUST-001) and attempt to access another customer's data (CUST-002). Verify that the agent returns an access-denied response without exposing any data and that the conversation continues normally after the denial.

Test it yourself first

Before looking at the solution below, try designing your own cross-customer isolation test. Think about how you would authenticate as one customer and then request a different customer's data.

No spec needed here

This challenge runs and verifies what you already built; it changes no code, so run the commands directly or ask Kiro in chat. Specs are for changes to the agent, its tools, or its infrastructure.

Mission
Your agent now scopes every tool call to the request identity. Your mission is to:
 
- Authenticate as Customer A (CUST-001): Invoke the agent with `actorId` set to CUST-001 
- Request Customer B's data (CUST-002): Ask the agent for CUST-002's billing, tickets, or usage charges 
- Verify access-denied: Confirm the agent denies the request without leaking any of CUST-002's data 
- Verify session continuity: Confirm the conversation continues normally after the denial (the agent doesn't crash or terminate) 
- Verify own data still accessible: After the denied request, confirm CUST-001's own data is still retrievable 
Understanding Identity Isolation
When scoping is enforced, every request in a session authenticated as CUST-001 (`actorId`) resolves like this:

| Request | Result |
| "Show my billing" | CUST-001 billing |
| "Show my tickets" | CUST-001 tickets |
| "Show CUST-002 billing" | Access denied, no CUST-002 data returned |
| "Show CUST-002 tickets" | Access denied, no CUST-002 data returned |
| Any follow-up after a denial | Session continues, CUST-001 data served |

Key behaviors to validate:
 
- Access-denied responses contain no data from the requested customer 
- The conversation does not terminate, and you can continue asking questions 
- Your own data remains accessible after a denied request 
Ideas for Your Test
 
- Authenticate as CUST-001, then explicitly ask for CUST-002's billing information 
- Try all three data categories: billing, tickets, and usage charges (part of the billing history) 
- After receiving access-denied, ask for your own (CUST-001) data to verify the session continues 
- Try different phrasing to ensure the identity boundary holds 

Hint: Sending the identity with each request

Pass the customer identity as `actorId` in the payload, and keep the same `--session-id` across the steps so the conversation continues. Run the commands from `~/environment/CustomerServiceAgent`:

```
agentcore invoke --runtime agent --session-id isolation-test-session-anycompany-cust001 --payload '{"prompt":"...","actorId":"CUST-001"}'
```

The template's `parse.py` reads `actorId`, the memory namespaces use it, and the hook you added in Challenge 1 compares it with the `customer_id` of every tool call. `agentcore invoke --user-id CUST-001` sets the Runtime user ID header instead; the template does not read that header, so the lab uses the payload form.

To test cross-customer access, ask about another customer by their ID within the same session.

Sample Test Sequence

Step 1: Verify own data access works

```
agentcore invoke --runtime agent --session-id isolation-sample-session-anycompany-cust001 --payload '{"prompt":"What are my current billing details?","actorId":"CUST-001"}'
```

You should see CUST-001's billing information returned successfully.

Step 2: Attempt cross-customer access

```
agentcore invoke --runtime agent --session-id isolation-sample-session-anycompany-cust001 --payload '{"prompt":"Can you show me the billing details for customer CUST-002?","actorId":"CUST-001"}'
```

You should receive an access-denied response with no CUST-002 data exposed.

Step 3: Verify session continuity

After the access-denied response, ask a follow-up question in the same session:

```
agentcore invoke --runtime agent --session-id isolation-sample-session-anycompany-cust001 --payload '{"prompt":"OK, can you show me my own support tickets instead?","actorId":"CUST-001"}'
```

The agent should respond normally with CUST-001's ticket data, proving the session wasn't terminated by the denial.

Validation Steps
Run the following test from `~/environment/CustomerServiceAgent` to validate cross-customer isolation across all three data categories. Every command uses the session `isolation-test-session-anycompany-cust001` (session IDs must be at least 33 characters) and the identity CUST-001.
Step 1: Verify own billing access

```
agentcore invoke --runtime agent --session-id isolation-test-session-anycompany-cust001 --payload '{"prompt":"Show me my billing history.","actorId":"CUST-001"}'
```

Confirm you see CUST-001's billing records.
Step 2: Attempt to access CUST-002's billing

```
agentcore invoke --runtime agent --session-id isolation-test-session-anycompany-cust001 --payload '{"prompt":"Show me the billing details for customer CUST-002.","actorId":"CUST-001"}'
```

Confirm: access-denied response, no CUST-002 data shown.
Step 3: Attempt to access CUST-002's tickets

```
agentcore invoke --runtime agent --session-id isolation-test-session-anycompany-cust001 --payload '{"prompt":"What support tickets does customer CUST-002 have?","actorId":"CUST-001"}'
```

Confirm: access-denied response, no CUST-002 ticket data shown.
Step 4: Attempt to access CUST-002's usage records

```
agentcore invoke --runtime agent --session-id isolation-test-session-anycompany-cust001 --payload '{"prompt":"Show me the usage records for CUST-002.","actorId":"CUST-001"}'
```

Confirm: access-denied response, no CUST-002 usage data shown (usage charges live in the billing history).
Step 5: Verify session still works, query own data

```
agentcore invoke --runtime agent --session-id isolation-test-session-anycompany-cust001 --payload '{"prompt":"Show me my own support tickets.","actorId":"CUST-001"}'
```

Confirm: CUST-001's tickets are returned successfully, proving the session was not terminated.
Expected Results

Expected Output: Own Data Access (Step 1)

```
Here is your billing history for the last four months.
| Period  | Plan charges | Usage charges | Total  | Due date     | Status  |
| 2024-04 | $79.99       | $12.01        | $92.00 | Apr 15, 2024 | Pending |
| 2024-03 | $79.99       | $7.26         | $87.25 | Mar 15, 2024 | Paid    |
| 2024-02 | $79.99       | $14.51        | $94.50 | Feb 15, 2024 | Paid    |
| 2024-01 | $79.99       | $10.00        | $89.99 | Jan 15, 2024 | Paid    |
Your April bill of $92.00 is still pending. It's due on April 15.
```

(The stream shows a `toolUse` block named `BillingTools___get_billing_history` before the text.)

Note

The specific billing amounts and periods depend on the seeded data for CUST-001. The important thing is that data is returned and it all belongs to CUST-001.

Expected Output: Cross-Customer Denied (Steps 2 to 4)

```
I can't show you billing details for CUST-002. I can only access the account you're
signed in to, which is CUST-001. If CUST-002 is your account, please sign in to it
directly. The account holder can also contact us themselves.
I can still help with your own account, such as your April bill, your plan, or any
support tickets.
```

In the live test the model refused from the system prompt alone, so no `toolUse` block appears in the stream. If the model does call a tool with `customer_id: CUST-002`, the `CustomerScopeHook` cancels it and the tool result the model sees is `Access denied: this session is authenticated as CUST-001 and cannot access data for CUST-002.` Either way no CUST-002 amount (for example `$39.99` or `$44.50`) appears.

Note

The exact wording will vary, but the response must: (1) NOT contain any of CUST-002's actual data, (2) indicate access was denied, and (3) the conversation should remain active for follow-up questions.

Expected Output: Session Continuity (Step 5)

```
You have three support tickets on file.
| Ticket      | Subject                       | Priority | Status   | Last updated |
| TKT-001-002 | Billing discrepancy February  | High     | Open     | Mar 1, 2024  |
| TKT-001-001 | Slow internet speeds          | Medium   | Resolved | Feb 12, 2024 |
| TKT-001-003 | Request plan upgrade info     | Low      | Resolved | Jan 16, 2024 |
Open ticket: TKT-001-002 is about a charge for a premium sports package you didn't
subscribe to. You asked for a $14.51 credit. It hasn't been updated since March 1.
I can escalate this ticket to a human agent so it gets reviewed. Would you like me to do that?
```

(The stream shows a `toolUse` block named `TicketingTools___query_tickets`.)

Note

This confirms the session survived the access-denied responses. The agent is able to continue serving the authenticated customer's requests normally.

Lab Completion Checklist
You've completed Lab 4 when you achieve:
 
- Scoping enforced in code: a `BeforeToolCallEvent` hook built with the request's `actorId` cancels any tool call for another `customer_id` 
- Agent Redeployed: `agentcore status` shows the runtime `agent` as `deployed` with the change 
- Own Data Accessible: Authenticated as CUST-001, you can retrieve CUST-001's billing, tickets, and usage charges 
- Cross-Customer Denied (Billing): Requesting CUST-002's billing returns access-denied with no data 
- Cross-Customer Denied (Tickets): Requesting CUST-002's tickets returns access-denied with no data 
- Cross-Customer Denied (Usage): Requesting CUST-002's usage returns access-denied with no data 
- Session Continuity: After receiving access-denied, the conversation continues and your own data is still accessible 
Troubleshooting

Common Issues

Agent returns CUST-002's data instead of denying access:

- Confirm `app/agent/scope.py` exists and `hooks=[CustomerScopeHook(actor_id)]` is passed to `Agent(...)` in `_get_agent` 
- Confirm you redeployed after the change: `agentcore deploy` 
- Check that `actorId` is in the payload of every request; without it the template uses `default` and nothing is scoped 
- Verify the tool input key is `customer_id` in the Lab 3 tool schema files 

Access is denied for all queries, including own data:

- Verify you're passing the correct customer ID format (e.g., `CUST-001`, not `cust-001` or `1`) 
- Check that the `actorId` matches the format used in your DynamoDB records 

Session terminates after access-denied:

- This indicates an error in the agent code; a canceled tool call should return a message, not raise 
- Check agent logs for the traceback: `agentcore logs runtime --since 15m` 
- Ensure the agent's system prompt instructs it to handle access-denied results gracefully 

Not sure what data is seeded for each customer:

- CUST-001 through CUST-010 are available in the database (created by `create_backend_systems` in Lab 3) 
- Each customer has at least 1 billing record and 1 ticket 
- You can verify directly with: `aws dynamodb query --table-name billing --key-condition-expression "customerId = :id" --expression-attribute-values '{":id":{"S":"CUST-001"}}'`

---

<!-- page: 17_lab-5-observability -->
# Lab 5: Observability

Observe Your Agent
In this lab, you route the OpenTelemetry traces of your AnyCompany Telecom agent to Amazon CloudWatch with Amazon Bedrock AgentCore Observability. Once routed, you can inspect traces that show exactly how the agent processes requests, including model inference, tool calls, and knowledge base retrieval, all captured as individual spans with timing data.
What You'll Learn
 
- How AgentCore Runtime instruments your agent with OpenTelemetry by default and how to route spans to CloudWatch 
- How to view traces using `agentcore traces runtime list` 
- How to navigate to CloudWatch logs for your agent runtime 
- How to identify individual span durations for tool calls and model inference 
- How to stream agent logs in real-time with `agentcore logs runtime --tail` 
- How to correlate log entries with trace spans 
Why Observability Matters
Your agent now handles customer queries, accesses backend systems, enforces identity, and maintains memory. When something goes wrong or performance degrades, you need visibility into what happened:
 
- Which tool calls are slow? A billing lookup taking 3 seconds vs 300ms tells you where to optimize 
- Where did the agent get stuck? Traces show reasoning steps, so you can see where the model decided to call a tool or escalate 
- What went wrong? Error spans pinpoint failures to a specific tool call, model inference, or retrieval operation 
- Is memory retrieval adding latency? You can measure the cost of semantic memory lookups in each request 
AgentCore Observability provides:
 
- OpenTelemetry tracing: Industry-standard trace format with spans for every agent operation 
- CloudWatch integration: Traces and logs are stored in CloudWatch for long-term analysis 
- Real-time log streaming: Watch agent activity live as requests are processed 
- Span-level timing: Millisecond-precision durations for each operation 
Prerequisites
 
- Completed Lab 4 (agent deployed with per-customer scoping) 
- AgentCore CLI installed and authenticated 
- Agent deployed (`agentcore status` shows the runtime `agent` as `deployed`) 
- Enable CloudWatch Transaction Search in your account and send trace segments to Amazon CloudWatch Logs. Without Transaction Search, AgentCore cannot deliver spans to the agent's log group. For more information, see [Enabling CloudWatch Transaction Search](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-configure.html#observability-configure-builtin-cw). 

Challenge Format

Each challenge states a goal and what the change must cover. You write a short brief, start a Quick Spec, review `requirements.md` and `tasks.md` against the Verification section, then let Kiro execute. Sample briefs are in expandable sections. Test challenges need no spec.

- Challenge 1: Send Traces to CloudWatch
- Challenge 2: View Traces and Stream Logs

---

<!-- page: 18_lab-5-observability__enable-tracing -->
# Challenge 1: Send Traces to CloudWatch

Challenge 1: Send Your Agent's Traces to CloudWatch
Your Goal: Route your agent's OpenTelemetry traces to its CloudWatch log group so every request produces a trace with spans for model calls, tool calls, Knowledge Base retrieval, and memory operations.

Write the brief yourself first

Compose your own spec brief from the bullets below before expanding the sample. The point is to state intent and acceptance criteria, not to find the right words for Kiro.

Mission
Your agent is already instrumented: AgentCore Runtime starts it under OpenTelemetry. What is missing is the destination. Your mission is to:
 
- Route traces to CloudWatch: set the environment variable that makes the runtime export spans to the agent's log group 
- Redeploy the agent: apply the configuration so it takes effect on the running agent 
- Verify traces arrive: confirm a test invocation shows up in `agentcore traces runtime list` and the log group exists 
Context
Two settings control tracing for a runtime created with the AgentCore CLI:

| Setting | Default | What it does |
| instrumentation.enableOtel (runtime in agentcore.json) | true | The runtime starts app/agent/main.py under opentelemetry-instrument; aws-opentelemetry-distro is already in app/agent/pyproject.toml |
| UNIFIED_TRACES_DESTINATION_ENABLED (runtime envVars) | not set | When true, spans are delivered to the agent's log group /aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT, where agentcore traces reads them |

CloudWatch Transaction Search must be enabled in the account (see the Lab prerequisites). When both are in place, every request produces a trace with spans for:

| Component | What Gets Traced |
| Model inference | Each call to the foundation model, including prompt construction and response generation |
| Tool invocations | Every MCP tool call (get_billing_info, create_ticket, escalate_to_human, etc.) |
| KB retrieval | Knowledge base queries and document retrieval operations |
| Memory operations | Short-term and long-term memory reads and writes |
| Agent reasoning | The orchestration logic that decides which tools to call |

Each trace contains multiple spans, one per operation, with a start time and duration, an operation name, a status, and attributes. Reference: [Configure observability](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-configure.html).
What your spec must cover
 
- `UNIFIED_TRACES_DESTINATION_ENABLED` set to `true` as an entry in the runtime's `envVars` list in `agentcore/agentcore.json`. 
- The agent is redeployed with the change. 
- A test invocation produces at least one trace in `agentcore traces runtime list`, and the log group `/aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT` exists. 
Each of these should appear as an acceptance criterion in `requirements.md`; the Verification section at the bottom of this page is the test.

Hint: where envVars sits in agentcore.json

Environment variables for a runtime are a list of `name`/`value` objects on the runtime entry, next to `name`, `entrypoint` and `codeLocation`:

```
"runtimes": [
  {
    "name": "agent",
    "...": "...",
    "envVars": [
      { "name": "UNIFIED_TRACES_DESTINATION_ENABLED", "value": "true" }
    ]
  }
]
```

If you followed the Lab 1 guardrail, the entry is already there and this challenge is a verification. If it is missing, add it and redeploy.

Start a spec
In the Kiro chat panel open a new session and choose Quick Spec (or Spec if you want to approve requirements, design, and tasks separately), or run `/spec new route-traces` in `kiro-cli chat` from your agent project folder. Paste your brief, then review `requirements.md` against the bullets above and `tasks.md` for the redeploy step. When the task list looks right, tell Kiro "Run all tasks for this spec".

Sample spec brief

Paste this into Quick Spec (or after `/spec new route-traces`).

```
Route the OpenTelemetry traces of my AgentCore agent in ~/environment/CustomerServiceAgent
to CloudWatch. Tracing instrumentation is already on by default; make sure
UNIFIED_TRACES_DESTINATION_ENABLED is set to true as an entry in the runtime's envVars
list in agentcore/agentcore.json, then redeploy. The change is complete when a test
invocation produces at least one trace in `agentcore traces runtime list` and the log
group /aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT exists.

Turn this into a spec: write the requirements with acceptance criteria that include
every constraint above, then the design, then the task list. Ask me clarifying
questions before drafting. Wait for my approval before executing the tasks.
```

Manual Steps (CLI Commands)

Run every command from `~/environment/CustomerServiceAgent`.

Step 1: Add the environment variable to the runtime

Edit `agentcore/agentcore.json` and make sure the runtime `agent` has this entry:

```
"runtimes": [
  {
    "name": "agent",
    "...": "...",
    "envVars": [
      { "name": "UNIFIED_TRACES_DESTINATION_ENABLED", "value": "true" }
    ]
  }
]
```

Step 2: Redeploy the agent

```
agentcore deploy
```

Step 3: Generate a trace

```
agentcore invoke --runtime agent --session-id trace-test-session-anycompany-cust001 --payload '{"prompt":"What are my current billing details?","actorId":"CUST-001"}'
```

Step 4: List the traces

Wait 30 to 90 seconds, then:

```
agentcore traces runtime list --since 15m
```

Step 5: Confirm the log group exists

```
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/ --query "logGroups[].logGroupName" --output text
```

Verification
After redeploying, generate a trace by invoking the agent with a question that triggers a tool call:

```
cd ~/environment/CustomerServiceAgent
agentcore invoke --runtime agent --session-id trace-test-session-anycompany-cust001 --payload '{"prompt":"What are my current billing details?","actorId":"CUST-001"}'
```

Wait 30 to 90 seconds, then check that traces were generated and that the log group exists:

```
agentcore traces runtime list --since 15m
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/ --query "logGroups[].logGroupName" --output text
```

You should see at least one trace entry corresponding to your request.

Expected Output

Traces list output:

```
TRACE ID                          TIMESTAMP             SESSION ID
6afcaa820790f3943efee5706cb457ba  2026-11-17 19:27:09Z  trace-test-session-anycompany-cust001
6afcaa3c390030127eda39a460b50066  2026-11-17 19:25:57Z  isolation-test-session-anycompany-cust001
6afcaa381cb6af8625d3f3c8107bca43  2026-11-17 19:25:46Z  isolation-test-session-anycompany-cust001
```

The list shows one row per trace: trace ID, timestamp and the session ID you passed to `agentcore invoke`. It does not show durations or span counts; download a trace with `agentcore traces runtime get <trace-id>` for those.

Log groups output:

```
/aws/bedrock-agentcore/runtimes/CustomerServiceAgent_default_agent-<agent-id>-DEFAULT
```

The log group name is the runtime ID (from the ARN in `agentcore status --json`) followed by `-DEFAULT`, the endpoint name.

Note

Your trace IDs and timestamps will differ. The key indicator is that a trace with your session ID appears in the list after you invoke the agent. In the live test traces were listed 60 seconds after the invocation.

Troubleshooting

Common Issues

`agentcore traces` command not recognized:

- Confirm the CLI version with `agentcore --version`; the labs are written for 1.0.3 (`npm install -g @aws/agentcore@1.0.3`) 
- The subcommand is `agentcore traces runtime list`; verify you're in the project directory 

No traces appear after invoking the agent:

- Confirm the `envVars` entry is in `agentcore/agentcore.json` and that you redeployed after adding it: `agentcore deploy` 
- Traces appear 30 to 90 seconds after the invocation; run `agentcore traces runtime list --since 15m` again 
- Confirm CloudWatch Transaction Search is enabled in the account (Lab prerequisites) 

Deployment fails after the change:

- Check that `envVars` is a list of `{ "name": ..., "value": ... }` objects, not a map 
- Review error messages: `agentcore --debug deploy` and `agentcore logs runtime --since 15m` 

Traces list returns empty:

- Make sure you invoked the agent at least once after the redeploy 
- Try a query that triggers a tool call (e.g., billing query) rather than a simple greeting 
- Allow up to 90 seconds for trace data to become available

---

<!-- page: 19_lab-5-observability__view-traces -->
# Challenge 2: View Traces and Stream Logs

Challenge 2: Inspect Traces and Stream Agent Logs
Your Goal: Execute a test query against your agent, retrieve the resulting trace, navigate to the CloudWatch log group, identify tool invocation spans with their durations, and stream live agent logs using the CLI.

Test it yourself first

Before looking at the hints or solutions below, try exploring the trace data on your own. Think about where traces are stored, how to find span durations, and how to correlate log entries with trace spans.

No spec needed here

This challenge runs and verifies what you already built; it changes no code, so run the commands directly or ask Kiro in chat. Specs are for changes to the agent, its tools, or its infrastructure.

Mission
Your agent now routes its traces to CloudWatch and is generating traces for every interaction. Your mission is to:
 
- Execute a test query: Invoke the agent with a request that triggers multiple tool calls 
- Retrieve the trace: Use `agentcore traces runtime list` to find the trace for your request and `agentcore traces runtime get` to download it 
- Navigate to CloudWatch: Find the agent's log group at `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT` 
- Identify span durations: Locate individual spans for tool calls and model inference, noting their duration in milliseconds 
- Stream live logs: Use `agentcore logs runtime --tail` to watch agent activity in real-time 
- Correlate logs with traces: Match a log entry to a corresponding trace span 
Context
When your agent processes a request, the trace captures the full execution flow:

```
Trace: a1b2c3d4-e5f6-7890-abcd-ef1234567890
├── span: agent.orchestrate (total: 1,245ms)
│   ├── span: model.invoke (duration: 450ms)
│   │   └── Foundation model inference
│   ├── span: tool.get_billing_info (duration: 312ms)
│   │   └── MCP tool call to billing service
│   ├── span: model.invoke (duration: 380ms)
│   │   └── Model processes tool result
│   └── span: memory.write (duration: 103ms)
│       └── Store interaction in memory
```

Each span tells you:
 
- What happened: The operation name (model call, tool call, memory access) 
- How long it took: Duration in milliseconds 
- Whether it succeeded: Status code and error details (if any) 
- Where to find more detail: CloudWatch log entries are correlated by trace ID 
The CloudWatch log group `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT` contains:
 
- Structured log entries for each agent operation 
- Trace IDs embedded in log entries for correlation 
- Error details and stack traces when operations fail 
Ideas for Your Test
 
- Invoke the agent with a query that exercises multiple tools (e.g., ask about billing AND open tickets in one request) 
- Use `agentcore traces runtime list --since 15m` to find the most recent trace 
- Look for the trace with the most spans, as that's likely your multi-tool query 
- Download one trace with `agentcore traces runtime get <trace-id>` and read the spans in the JSON file 
- Use `agentcore logs runtime --tail` in a separate terminal to watch activity live while you invoke the agent 

Hint: Finding Span Durations

List the recent traces, then download one:

```
agentcore traces runtime list --since 15m
agentcore traces runtime get <trace-id>
```

The list shows trace IDs, timestamps and session IDs. `get` writes the trace's log records to `<trace-id>.json` in the current directory; span records carry `name`, `kind`, `durationNano` and `attributes`, log records carry `body`. Read it with:

```
jq '.[0]' <trace-id>.json
```

You can also open CloudWatch, go to Log groups, choose `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT`, and filter log entries by the trace ID. The CloudWatch GenAI Observability page shows the same trace as a timeline.

Hint: Streaming Logs

The `agentcore logs runtime` command searches or streams log entries from your agent:

```
# Live: follow new entries as they arrive (stop with Ctrl+C)
agentcore logs runtime --tail

# History: the last 15 minutes
agentcore logs runtime --since 15m
```

The live mode is similar to `docker logs -f` or `kubectl logs -f`. You'll see:

- Request received events 
- Model inference start/end events 
- Tool invocation events with parameters and results 
- Memory read/write events 
- Response sent events 

Each log entry includes a timestamp and often a trace ID that you can correlate with the traces list.

Sample Test Sequence

Run the commands from `~/environment/CustomerServiceAgent`.

Step 1: Execute a test query that triggers multiple operations

```
agentcore invoke --runtime agent --session-id trace-test-session-2-anycompany-cust001 --payload '{"prompt":"I would like to check my current billing status and also see if I have any open support tickets.","actorId":"CUST-001"}'
```

This should trigger both `get_billing_info` and `query_tickets` tool calls, generating a trace with multiple spans.

Step 2: Retrieve the trace

```
agentcore traces runtime list --since 15m
```

Find the most recent trace with multiple spans (5+ spans indicates multiple tool calls), then download it:

```
agentcore traces runtime get <trace-id>
jq '.[0]' <trace-id>.json | head -30
```

Step 3: Navigate to CloudWatch logs

Open the AWS Console and navigate to:

- CloudWatch, then Log groups, then `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT` 

Replace `{agent-id}` with your actual agent ID (the last segment of the runtime ARN in `agentcore status`).

In the log group, look for log entries correlated with the trace ID from Step 2.

Step 4: Identify span durations

In the downloaded JSON or the CloudWatch logs, look for span records with a name, a duration and a status, for example tool spans named after `get_billing_info` and `query_tickets` and model spans for the Bedrock calls. Note the duration of each tool invocation span in milliseconds.

Step 5: Stream live logs

In a separate terminal, start streaming:

```
cd ~/environment/CustomerServiceAgent
agentcore logs runtime --tail
```

Then in your first terminal, invoke the agent again:

```
agentcore invoke --runtime agent --session-id trace-test-session-2-anycompany-cust001 --payload '{"prompt":"What plan am I currently on?","actorId":"CUST-001"}'
```

Watch the logs stream in real-time as the agent processes the request. Stop with `Ctrl+C`.

Step 6: Correlate a log entry with a trace span

In the streamed logs, find an entry that mentions a trace ID. Then cross-reference that trace ID in `agentcore traces runtime list --since 15m` to see the full trace with all spans.

Validation
Complete the following steps from `~/environment/CustomerServiceAgent` to verify observability is fully working:
Step 1: Execute a multi-tool query

```
agentcore invoke --runtime agent --session-id trace-test-session-3-anycompany-cust001 --payload '{"prompt":"Check my billing status and show me my support tickets.","actorId":"CUST-001"}'
```

Step 2: Retrieve the trace and find a tool invocation span

```
agentcore traces runtime list --since 15m
agentcore traces runtime get <trace-id>
```

Locate the trace for your request. Confirm the downloaded JSON contains:
 
- At least one tool invocation span (for `get_billing_info` or `query_tickets`) 
- A duration value in milliseconds for that span 
Step 3: Navigate to CloudWatch log group
Open CloudWatch, then Log groups, then `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT`
Confirm log entries exist for your agent's recent activity.
Step 4: Stream logs in real-time

```
agentcore logs runtime --tail
```

Invoke the agent in another terminal and confirm you see live log output for the request processing.
Expected Results

Expected Output: Traces List

```
TRACE ID                          TIMESTAMP             SESSION ID
6afcaa820790f3943efee5706cb457ba  2026-11-17 19:27:09Z  trace-test-session-anycompany-cust001
6afcaa3c390030127eda39a460b50066  2026-11-17 19:25:57Z  isolation-test-session-anycompany-cust001
6afcaa381cb6af8625d3f3c8107bca43  2026-11-17 19:25:46Z  isolation-test-session-anycompany-cust001
```

The list shows one row per trace: trace ID, timestamp and the session ID you passed to `agentcore invoke`. It does not show durations or span counts; download a trace with `agentcore traces runtime get <trace-id>` for those.

The list itself has no span count: download the trace of the multi-tool query (billing + tickets) to see the most spans: `invoke_agent Strands Agents`, one `execute_event_loop_cycle` and one `chat` span per reasoning step, `execute_tool` and `mcp tools/call` spans for `BillingTools___get_billing_info` and `TicketingTools___query_tickets`, and the memory spans (`Bedrock AgentCore.ListEvents`, `RetrieveMemoryRecords`, `CreateEvent`).

Note

Your trace IDs and timestamps will vary. The key validation is that you can identify at least one `execute_tool` span with a duration in milliseconds in the downloaded trace.

Expected Output: Downloaded trace

`agentcore traces runtime get 6afcaa820790f3943efee5706cb457ba` prints:

```
Saved 57 records for trace 6afcaa820790f3943efee5706cb457ba
/home/participant/environment/CustomerServiceAgent/6afcaa820790f3943efee5706cb457ba.json
```

The file is a JSON array of CloudWatch log records; each record has `@timestamp`, `@ptr` and `@message`. The `@message` of a span record has `name`, `kind`, `startTimeUnixNano`, `endTimeUnixNano`, `durationNano`, `attributes` and the `traceId`; log-line records have `body` and `severityText` instead. `jq '.[0]' <trace-id>.json` shows a log record first (`"body": "Returning streaming response (generator)"`, `"scope": {"name": "bedrock_agentcore.app"}`), with `resource.attributes` such as `service.name`, `aws.log.group.names` and `cloud.resource_id` (the runtime ARN). To list the spans with their durations:

```
jq -r '.[]["@message"] | select(.name != null) | "\(.name)  \(.kind)  \(.durationNano / 1000000 | floor) ms"' <trace-id>.json
```

```
mcp tools/list  CLIENT  89 ms
Bedrock AgentCore.ListEvents  CLIENT  156 ms
Bedrock AgentCore.RetrieveMemoryRecords  CLIENT  274 ms
chat global.anthropic.claude-sonnet-5-5  CLIENT  722 ms
chat  INTERNAL  922 ms
execute_tool BillingTools___get_billing_info  INTERNAL  422 ms
mcp tools/call BillingTools___get_billing_info  CLIENT  421 ms
execute_event_loop_cycle  INTERNAL  1621 ms
chat global.anthropic.claude-sonnet-5-5  CLIENT  1236 ms
execute_event_loop_cycle  INTERNAL  1360 ms
Bedrock AgentCore.CreateEvent  CLIENT  119 ms
invoke_agent Strands Agents  INTERNAL  3496 ms
POST /invocations  SERVER  8803 ms
```

The one-tool billing query produced 23 spans: the `POST /invocations` server span, `invoke_agent Strands Agents`, two `execute_event_loop_cycle` spans (one per reasoning step), two `chat` model spans, the `execute_tool` and `mcp tools/call` spans for `BillingTools___get_billing_info`, and the memory calls (`ListEvents`, `RetrieveMemoryRecords`, `CreateEvent`).

Note

The exact fields depend on the instrumentation version. The key indicator is that span records contain a trace ID, a span name, timestamps and attributes that you can correlate with the traces list output.

Expected Output: Live Log Streaming

`agentcore logs runtime --tail` prints a header and then waits for new entries:

```
Streaming logs for Runtime 'agent' on target 'default'... (Ctrl+C to stop)
```

Entries arrive while a request is processed (same format as `agentcore logs runtime --since 15m`, one line per CloudWatch event, timestamp first):

```
2026-11-17T19:27:00.621Z  {"timestamp": "2026-11-17T19:27:00.621Z", "level": "INFO", "message": "Invoking Agent.....", "logger": "bedrock_agentcore.app", "requestId": "...", "sessionId": "trace-test-session-anycompany-cust001"}
2026-11-17T19:27:00.622Z  2026-11-17 19:27:00,622 INFO [bedrock_agentcore.app] [main.py:72] [trace_id=6afcaa820790f3943efee5706cb457ba span_id=... resource.service.name=CustomerServiceAgent_default_agent.DEFAULT trace_sampled=True] - Invoking with session_id=trace-test-session-anycompany-cust001 and actor_id=CUST-001
2026-11-17T19:27:09.298Z  - **Due date:** April 15, 2024
2026-11-17T19:27:09.300Z  {"resource":{"attributes":{"telemetry.sdk.language":"python", ... "service.name":"CustomerServiceAgent_default_agent.DEFAULT", ...}}, "scope":{...}, "name":"...", "traceId":"6afcaa820790f3943efee5706cb457ba", ...}
```

The JSON lines that start with `{"resource":{"attributes":...` are the OpenTelemetry span and log records that `UNIFIED_TRACES_DESTINATION_ENABLED=true` routes into this log group; the `trace_id=` field on the application log lines is how you correlate them with `agentcore traces runtime list`. A 15-minute window with a handful of invocations is around 700 lines.

Note

Streaming output appears in real-time as the agent processes requests. Press Ctrl+C to stop streaming. The format and level of detail may vary by AgentCore version.

Lab Completion Checklist
You've completed Lab 5 when you achieve:
 
- Traces routed: `UNIFIED_TRACES_DESTINATION_ENABLED` is set to `true` in the runtime's `envVars` and the agent is redeployed 
- Test Query Executed: You invoked the agent with a query that triggered at least one tool call 
- Trace Retrieved: `agentcore traces runtime list` shows a trace for your request 
- Tool Span Identified: You located a tool invocation span (for `get_billing_info` or `query_tickets`) within the downloaded trace 
- Duration Found: You identified the duration in milliseconds for the tool invocation span 
- CloudWatch Navigated: You found the agent's log group at `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT` 
- Logs Streamed: `agentcore logs runtime --tail` streams agent activity in real-time 
- Correlation Made: You matched a log entry with a corresponding trace span using the trace ID 
Troubleshooting

Common Issues

`agentcore traces runtime list` returns empty:

- Ensure you invoked the agent at least once after the redeploy 
- Wait 30 to 90 seconds for trace data to propagate, and widen the window with `--since 1h` 
- Confirm `envVars` in `agentcore/agentcore.json` contains `UNIFIED_TRACES_DESTINATION_ENABLED` set to `true` and that you redeployed 
- Try a query that triggers a tool call. Simple greetings may not generate enough spans 

Cannot find CloudWatch log group:

- The log group name follows the pattern: `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT` 
- Find your agent ID in the runtime ARN from `agentcore status` 
- Ensure you're looking in the correct AWS region 
- The log group is created automatically when the first trace is emitted 

`agentcore logs runtime --tail` shows no output:

- `--tail` streams new log entries and won't show historical data; use `--since 15m` for history 
- Invoke the agent in a separate terminal while streaming to see live output 
- Ensure the agent is deployed: `agentcore status` 
- Check network connectivity, as log streaming requires an active connection 

Spans don't show duration:

- Durations are recorded when a span completes. Check the span end time, not just the start 
- In the downloaded JSON, compare the start and end timestamps of a span record 

Can't correlate log entries with traces:

- Look for `traceId` or `trace` fields in log entries 
- The trace ID in the logs should match an entry in `agentcore traces runtime list` 
- Filter CloudWatch logs by trace ID using the Logs Insights query: `filter @message like /your-trace-id/`

---

<!-- page: 20_lab-6-building-ui -->
# Lab 6: Building UI App

Lab 6: Build and Deploy a Chat UI
Your Mission
Build a web-based chat interface for your AI agent, containerize it with Docker, and deploy it to the pre-provisioned ECS Fargate cluster. By the end of this lab, you'll have a production-ready chat UI that streams real-time responses from your AgentCore-deployed agent.
Your end users will interact with the AnyCompany Telecom support agent through this web interface, complete with streaming token display, multi-turn conversation support, and graceful error handling.
What You'll Build
 
- A web-based chat UI that streams tokens in real-time from your AgentCore endpoint 
- A Docker container packaging the application for deployment 
- A Fargate service running on the pre-provisioned ECS cluster with health checks 
- A production-ready experience with error handling and conversation persistence 
Prerequisites
Before starting this lab, ensure you have:
 
- A working agent deployed on AgentCore Runtime (Labs 1–5 completed) 
- Access to your development environment (the Kiro IDE Browser) 
- Docker available in your environment (`docker --version`) 
- The ECS cluster ARN from your stack outputs (`$ECS_CLUSTER`) 

Verify Prerequisites

Confirm your agent is still running and accessible:

```
# Verify agent is active
agentcore status

# Confirm ECS cluster is available
echo $ECS_CLUSTER
aws ecs describe-clusters --clusters $ECS_CLUSTER --query "clusters[0].status" --output text
```

Both commands should return successfully before proceeding.

Lab Structure
This lab is organized into three challenges:
 
- Build the Chat UI: Create a web application that streams tokens from your AgentCore endpoint 
- Deploy to ECS Fargate: Containerize and deploy to the pre-provisioned cluster 
- Test Your UI: Verify multi-turn conversations with context retention 

Challenge Approach

Each challenge states a goal and what the change must cover. You write a short brief, start a Quick Spec, review `requirements.md` and `tasks.md` against the Verification section, then let Kiro execute. Sample briefs are in expandable sections. Test challenges need no spec.

- Challenge 1: Build the Chat UI
- Challenge 2: Deploy to ECS Fargate
- Challenge 3: Test Your Chat UI

---

<!-- page: 21_lab-6-building-ui__build-ui -->
# Challenge 1: Build the Chat UI

Challenge 1: Build a Streaming Chat Interface
Mission
Build a web-based chat interface that:
 
- Connects to your deployed AgentCore Runtime endpoint 
- Streams tokens in real-time (incremental rendering as they arrive) 
- Supports multi-turn conversation with visible chat history 
- Handles errors gracefully when the agent is unavailable 
What You'll Need
 
- AgentCore endpoint: Your deployed agent's runtime ARN, from `agentcore status --json` in the agent project: `agentcore status --json | jq -r '.resources[] | select(.resourceType=="runtime") | .arn'` 
- A web framework: A Python framework (Flask, FastAPI, etc.) 
- Streaming support: The UI must render tokens incrementally, not wait for the full response 
- AWS credentials: For authenticating requests to AgentCore Runtime 
Pick exactly ONE path below. Both paths are equal alternatives and end in the same place: a chat UI running locally on port 8888 that Challenge 2 containerizes and deploys. Choose the one that matches your interests before you start:
 
- Build your own variant with Specs: design your own chat experience (layout, branding, extra features) using Kiro's spec-driven workflow: requirements, design, and tasks you review before any code is written 
- Guided sample: run the pre-provisioned `build-chat-ui` skill, which carries the full build playbook 
Naming guardrails (applies to BOTH paths)

Whichever path you choose, your chat UI must follow this fixed interface:

| Requirement | Value |
| App directory | ~/environment/chat-ui/ |
| Local port | 8888 (port 8080 is the Kiro IDE Browser, 8081 is agentcore dev, never reuse) |
| Health endpoint | /health returning HTTP 200 |
| Configuration | Reads AGENTCORE_ENDPOINT and AWS_REGION from the environment |
| Streaming | Streams tokens incrementally (not a single block after a delay) |
| Binding | Binds 0.0.0.0 |
| Proxy-safe paths | Relative asset/API paths so it works behind /proxy/8888/ |
| Dockerfile-ready | Structured so Challenge 2 can containerize and deploy it unchanged |

Why? Challenge 2 containerizes this exact app and deploys it to the pre-provisioned ECS Fargate cluster, referencing the directory, port, and `/health` endpoint verbatim. Stay within the guardrails and the deployment steps work unchanged, no matter how you design the experience.

- 
- 

Build with Kiro Specs: requirements, design, tasks

In this path you design your own chat experience and build it with Kiro using a [Kiro Specs](https://kiro.dev/docs/specs/) workflow. A spec turns your intent into three reviewable documents: a `requirements.md` with user stories and acceptance criteria, a `design.md` with the technical approach, and a `tasks.md` with an ordered implementation plan. You approve each document before Kiro writes a line of code, then Kiro executes the tasks one at a time and you verify each result. Kiro does the heavy lifting; you stay in control of every decision that matters.

Your design, within the guardrails: you decide the layout, branding, and any extra features such as conversation export, suggested questions, a typing indicator, or a theme switcher.

Time box: target 20–25 minutes for this challenge. Use Quick Spec if you are short on time: it generates requirements, design, and tasks in one pass after a few clarifying questions, and you still review the task list before Kiro builds.

The spec workflow in this challenge

- Start a spec (~2 min). In the chat panel open a new session and choose Spec from "Start with a built-in agent" (or Quick Spec if short on time), or run `/spec new chat-ui` in `kiro-cli chat`. When asked, pick Build a Feature and the Requirements workflow. 
- Requirements (~5 min). Paste the brief below. Kiro drafts `requirements.md` with user stories and acceptance criteria. Check every guardrail appears as an acceptance criterion. Reply "looks good" to approve, or give specific feedback such as "Add an acceptance criterion that the app listens on port 8888". 
- Design (~3 min). Click Generate Tech Design. Review `design.md`: port 8888, the `/health` endpoint, relative paths that work behind `/proxy/8888/`, and streaming. Approve or give feedback. 
- Tasks (~2 min). Click Generate Task List. Review `tasks.md`; tasks should be ordered so each builds on the previous. 
- Execute (~10 min). Tell Kiro "Run all tasks for this spec", or start tasks one at a time to review each result. Kiro runs tests at checkpoints and fixes failures. When done, run the Verification section. 

Where the spec lives

The spec files land in `~/environment/.kiro/specs/<name>/` (`requirements.md`, `design.md`, `tasks.md`). You can open them in the Explorer and edit them directly; Kiro picks up your edits.

Your spec brief

Compose your brief in Kiro chat. Include your design and paste the guardrails in verbatim so they become part of the plan. A template:

```
I want to build a web-based streaming chat UI for my AnyCompany Telecom support
agent. Here is my design: [YOUR LAYOUT, BRANDING, AND EXTRA FEATURES, e.g. a
two-column layout with a suggested-questions sidebar and a "download transcript"
button].

Non-negotiable constraints (the rest of the lab depends on these):

- Python web app in ~/environment/chat-ui/
- Reads AGENTCORE_ENDPOINT and AWS_REGION from the environment
- Calls AgentCore Runtime with streaming enabled and renders tokens
  incrementally in the browser
- Preserves conversation history on screen across turns, including on error
- Handles errors gracefully with a user-friendly inline message
- GET /health returns HTTP 200
- Listens on port 8888 (8080 is the Kiro IDE Browser, 8081 is agentcore dev)
- Binds 0.0.0.0
- Works behind a reverse proxy under a path prefix (/proxy/8888/): use relative
  asset and API paths throughout so nothing escapes the prefix
- A requirements.txt with the runtime dependencies
- Structured so it can be containerized for Amazon ECS Fargate in Challenge 2

Turn this into a spec: write the requirements with acceptance criteria that
include every constraint above, then the design, then the task list. Ask me
clarifying questions before drafting. Wait for my approval of each document
before executing the tasks.
```

While Kiro executes the tasks, review each result against the guardrails. Confirm the directory, port, `/health` endpoint, and relative paths match the guardrails as they are created. It is much cheaper to correct early than after the full build.

Verification
After Kiro generates your UI code, verify it works locally:

```
cd ~/environment/chat-ui
# Create a virtual environment and install dependencies with uv
# (the IDE's system Python has no pip and does not allow package installs)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
# Check syntax
python3 -c "import ast; ast.parse(open('app.py').read())" && echo "app.py syntax OK"
# Start the app locally (test that it boots)
timeout 5 python3 app.py || true
echo "App starts without import errors"
# Test health endpoint (in a separate terminal or after starting the app)
curl http://localhost:8888/health
```

Expected Output

```
{ "status": "healthy" }
```

Your application should start on port 8888 and respond to the `/health` endpoint.

To open the chat interface in your browser, open the proxied port:

```
python3 -m webbrowser $IDE_URL/proxy/8888/
```

`IDE_URL` is pre-set in the IDE terminal, and the IDE proxies local ports under `/proxy/<port>/`, so this opens the chat UI in the same browser session where the Kiro IDE is open. No security group change or local software is needed.

Why port 8888?

The Kiro IDE Browser itself listens on port 8080, and `agentcore dev` uses port 8081. The chat UI uses port 8888 so it never collides with either. Do not stop any process on port 8080; that is the IDE you are working in.

Note

Your exact implementation, framework choice, and file structure may vary depending on the path and prompts you used. The key requirements are: streaming token display, health check endpoint, error handling, and conversation history preservation.

Accelerate: add a hook that checks the health endpoint on every save

Hooks are optional automation that Kiro runs on an event such as saving a file: a shell command or a prompt, defined in a JSON file under `.kiro/hooks/`. See [Kiro Hooks](https://kiro.dev/docs/hooks/).

The hook below calls your `/health` endpoint every time you save a Python, HTML, or JavaScript file, so a broken app shows up immediately while it is running locally on port 8888:

```
mkdir -p ~/environment/chat-ui/.kiro/hooks
cat > ~/environment/chat-ui/.kiro/hooks/health-on-save.json << 'HOOK_EOF'
{
"version": "v1",
"hooks": [
{
"name": "health-on-save",
"description": "Check the chat UI health endpoint when a source file is saved",
"trigger": "PostFileSave",
"matcher": "\\.(py|html|js)$",
"action": {
"type": "command",
"command": "curl -sf http://localhost:8888/health || echo 'health check failed: is the app running on 8888?'"
},
"timeout": 30
}
]
}
HOOK_EOF
```

Kiro reads `.kiro/hooks/` in the workspace, so the hook is active for the IDE chat panel and Kiro CLI alike; remove the file to disable it.

This box is optional and not needed to finish the lab.

Troubleshooting

Common Issues

Import Errors

Symptom: ModuleNotFoundError when starting the app, or "No module named pip" when installing

Resolution:

```
# Make sure the virtual environment is active, then install with uv.
# Plain "pip install" fails on the IDE: the system Python has no pip.
source ~/environment/chat-ui/.venv/bin/activate
uv pip install -r requirements.txt
# If using uvicorn:
uv pip install "uvicorn[standard]"
```

AgentCore Connection Issues

Symptom: Error connecting to AgentCore endpoint

Resolution:

```
# Verify your agent is still deployed (run in the agent project)
cd ~/environment/CustomerServiceAgent
agentcore status
# Verify endpoint is set
echo $AGENTCORE_ENDPOINT
# Test direct invocation still works
agentcore invoke --runtime agent --payload '{"prompt":"Hello"}'
```

Port Already in Use

Symptom: Address already in use (0.0.0.0:8888)

Resolution:

```
# Find and stop the earlier chat UI process on port 8888 only
# (never target port 8080: that is the Kiro IDE Browser)
lsof -i :8888 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

---

<!-- page: 22_lab-6-building-ui__deploy-ecs -->
# Challenge 2: Deploy to ECS Fargate

Challenge 2: Containerize and Deploy to ECS Fargate
Mission
Containerize your chat UI application with Docker and deploy it to the pre-provisioned ECS Fargate cluster. Your deployment should:
 
- Package the application into a Docker container 
- Push the image to Amazon ECR 
- Create an ECS Fargate service on the pre-provisioned cluster (`$ECS_CLUSTER`) 
- Configure a health check endpoint so ECS can monitor container health 
- Make the UI accessible via a public URL 
What You'll Need
 
- Working chat UI from Challenge 1 (with `/health` endpoint) 
- Docker installed and running (`docker --version`) 
- ECS cluster ARN from environment variable `$ECS_CLUSTER` 
- AWS credentials configured for ECR and ECS operations 
- AgentCore endpoint that the container will connect to at runtime 
Two ways to do this challenge
 
- Guided: invoke the `deploy-chat-ui-to-ecs` skill. Type `/` in Kiro chat and select it, or just ask "Deploy my chat UI to ECS Fargate". Review the Dockerfile and `deploy.sh` the skill shows you before you approve the run. To read the playbook first, run `cat ~/environment/.kiro/skills/deploy-chat-ui-to-ecs/SKILL.md`. 
- Spec: write the brief and follow "Start a spec" below. Both paths must satisfy the same requirements in "What your spec must cover". 

Write the brief yourself first

Compose your own spec brief from the bullets below before expanding the sample. The point is to state intent and acceptance criteria, not to find the right words for Kiro.

What your spec must cover
 
- The build must produce a Dockerfile using a Python base image that installs dependencies from `requirements.txt`, copies the application code, exposes port 8888, and sets a health check hitting `/health`. 
- The build must push the image to an Amazon ECR repository named `agent-chat-ui`. 
- The deployment must register an ECS task definition with the Fargate launch type, 512 CPU and 1024 MB memory, container port 8888, environment variables `AGENTCORE_ENDPOINT` and `AWS_REGION`, a health check against `/health`, and task roles with permission to invoke the Bedrock AgentCore runtime. 
- The deployment must create or update an ECS service on the pre-provisioned cluster (`$ECS_CLUSTER`) with desired count 1, a public IP assigned, using the default VPC's public subnets and a security group in the default VPC that allows inbound TCP 8888. 
- All resources must be tagged `Workshop=anycompany-telecom-agent`. 
- The change is complete when the service reaches a running task with ACTIVE status and the `/health` endpoint on the public URL returns a healthy response. 
Each of these should appear as an acceptance criterion in `requirements.md`; the Verification section at the bottom of this page is the test.
Start a spec
In the Kiro chat panel open a new session and choose Quick Spec (or Spec if you want to approve requirements, design, and tasks separately), or run `/spec new deploy-chat-ui` in `kiro-cli chat` from your chat UI project folder. Paste your brief, then review `requirements.md` against the bullets above and `tasks.md` for the deploy step. When the task list looks right, tell Kiro "Run all tasks for this spec".

Sample spec brief

Paste this into Quick Spec (or after `/spec new deploy-chat-ui`).

```
Containerize my chat UI and deploy it to the pre-provisioned ECS Fargate cluster.

Requirements:
- A Dockerfile that uses python:3.11-slim as the base image, installs dependencies
  from requirements.txt, copies the application code, exposes port 8888, sets a health
  check (curl -f http://localhost:8888/health || exit 1), and runs the app
  (python app.py, or uvicorn if the app uses FastAPI).
- The image is pushed to an Amazon ECR repository named agent-chat-ui.
- An ECS task definition with the Fargate launch type, 512 CPU and 1024 MB memory,
  container port 8888, environment variables AGENTCORE_ENDPOINT and AWS_REGION, a health
  check against /health, and task execution and task roles with permission to invoke the
  Bedrock AgentCore runtime.
- An ECS service on the cluster referenced by the ECS_CLUSTER environment variable, with
  desired count 1, a public IP assigned, using the default VPC's public subnets and a
  security group in the default VPC that allows inbound TCP 8888.
- AWS_REGION defaults to us-east-1 if unset.
- All resources tagged Workshop=anycompany-telecom-agent.
- The change is complete when the service reaches a running task with ACTIVE status and
  the /health endpoint on the public URL returns a healthy response.

Turn this into a spec: write the requirements with acceptance criteria that include
every constraint above, then the design, then the task list. Ask me clarifying
questions before drafting. Wait for my approval before executing the tasks.
```

Hint: Deployment Steps

The containerization and deployment workflow follows these steps:

Step 1: Create the Dockerfile

```
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

CMD ["python", "app.py"]
```

Step 2: Build and push to ECR

```
# Get account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=${AWS_REGION:-us-east-1}
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/agent-chat-ui"

# Create ECR repo
aws ecr create-repository --repository-name agent-chat-ui --region $REGION 2>/dev/null || true

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Build and push
docker build -t agent-chat-ui .
docker tag agent-chat-ui:latest ${ECR_REPO}:latest
docker push ${ECR_REPO}:latest
```

Step 3: Create ECS task definition and service

Key task definition parameters:

- `networkMode`: awsvpc (required for Fargate) 
- `requiresCompatibilities`: FARGATE 
- `cpu`: "512", `memory`: "1024" 
- Container port mapping: 8888 
- Environment variables: `AGENTCORE_ENDPOINT`, `AWS_REGION` 
- Health check command: `["CMD-SHELL", "curl -f http://localhost:8888/health || exit 1"]` 

Key service network parameters (`awsvpcConfiguration`):

- Subnets: the public subnets of the account's default VPC 
- Security group: created in the default VPC, allowing inbound TCP 8888 
- `assignPublicIp`: ENABLED 

```
# Look up the default VPC and its subnets
DEFAULT_VPC_ID=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query "Vpcs[0].VpcId" --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$DEFAULT_VPC_ID --query "Subnets[].SubnetId" --output text | tr '\t' ',')
echo "Default VPC: $DEFAULT_VPC_ID"
echo "Subnets: $SUBNET_IDS"
```

Step 4: Access the service

After the service stabilizes, get the public IP:

```
TASK_ARN=$(aws ecs list-tasks --cluster $ECS_CLUSTER --service-name agent-chat-ui --query "taskArns[0]" --output text)
ENI_ID=$(aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text)
PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --query "NetworkInterfaces[0].Association.PublicIp" --output text)
echo "Chat UI available at: http://${PUBLIC_IP}:8888"
```

Verification
After deployment completes, verify your service is running:

```
# Check ECS service status
aws ecs describe-services --cluster $ECS_CLUSTER --services agent-chat-ui \
    --query "services[0].{Status:status,Running:runningCount,Desired:desiredCount}" \
    --output table

# Get the public URL
TASK_ARN=$(aws ecs list-tasks --cluster $ECS_CLUSTER --service-name agent-chat-ui --query "taskArns[0]" --output text)
ENI_ID=$(aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN \
    --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text)
PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID \
    --query "NetworkInterfaces[0].Association.PublicIp" --output text)

echo "Chat UI URL: http://${PUBLIC_IP}:8888"

# Test health endpoint
curl http://${PUBLIC_IP}:8888/health
```

Expected Output

```
------------------------------------------
|           DescribeServices             |
+---------+---------+--------------------+
| Desired | Running |      Status        |
+---------+---------+--------------------+
|    1    |    1    |      ACTIVE        |
+---------+---------+--------------------+

Chat UI URL: http://x.x.x.x:8888

{"status": "healthy"}
```

Your ECS service should show 1 running task with ACTIVE status. The health endpoint should return a successful response.

Note

It may take 2-3 minutes for the ECS service to stabilize and the task to reach a RUNNING state. If `runningCount` is 0, wait and check again. Check task logs if the task fails to start.

Troubleshooting

Common Issues

Docker Build Failures

Symptom: Docker build fails with dependency errors

Resolution:

```
# Verify Dockerfile syntax
docker build --no-cache -t agent-chat-ui .

# Check that requirements.txt resolves (uv; the IDE's system Python has no pip)
uv pip install --dry-run -r requirements.txt

# Ensure curl is available in the container (for healthcheck)
# Add to Dockerfile if using slim image:
# RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
```

ECR Push Failures

Symptom: Authorization errors when pushing to ECR

Resolution:

```
# Re-authenticate to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $(aws sts get-caller-identity --query Account --output text).dkr.ecr.${AWS_REGION}.amazonaws.com
```

ECS Task Keeps Restarting

Symptom: Running count stays at 0, tasks appear and disappear

Resolution:

```
# Check stopped task reason
TASK_ARN=$(aws ecs list-tasks --cluster $ECS_CLUSTER --service-name agent-chat-ui --desired-status STOPPED --query "taskArns[0]" --output text)
aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN --query "tasks[0].stoppedReason" --output text

# Check container logs
aws logs get-log-events --log-group-name /ecs/agent-chat-ui --log-stream-name $(aws logs describe-log-streams --log-group-name /ecs/agent-chat-ui --order-by LastEventTime --descending --limit 1 --query "logStreams[0].logStreamName" --output text) --limit 20
```

Common causes:

- Health check failing (ensure `/health` endpoint works and curl is installed) 
- Port mismatch (container must listen on 8888) 
- Missing environment variables (AGENTCORE_ENDPOINT not set) 

Security Group Blocking Access

Symptom: Service is running but you can't reach the URL

Resolution:

```
# Find the security group attached to the task
ENI_ID=$(aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text)
SG_ID=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --query "NetworkInterfaces[0].Groups[0].GroupId" --output text)

# Add inbound rule for TCP port 8888
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8888 --cidr 0.0.0.0/0
```

---

<!-- page: 23_lab-6-building-ui__test-ui -->
# Challenge 3: Test Your Chat UI

Challenge 3: Test Multi-Turn Conversation
Mission
Verify your deployed chat UI works end-to-end by:
 
- Accessing the UI via the ECS service URL 
- Conducting a 3-turn conversation with the agent 
- Confirming the agent retains context across turns (references earlier messages) 
- Testing error handling behavior when the agent is unavailable 
What You'll Need
 
- ECS service URL from the previous challenge (the public IP on port 8888) 
- A web browser to interact with the chat UI 
- AnyCompany Telecom test scenarios (customer queries about plans, billing, troubleshooting) 

No spec needed here

This challenge runs and verifies what you already built; it changes no code, so run the commands directly or ask Kiro in chat. Specs are for changes to the agent, its tools, or its infrastructure.

Validation: 3-Turn Conversation Test
Open your chat UI in a browser and have a multi-turn conversation to verify context retention. Use this test scenario:
Turn 1: Establish Context
Send a message that introduces specific information the agent should remember:

```
Hi, I'm Sarah from account CUST-003. I'm interested in upgrading
from my Basic plan to the Premium plan. Can you tell me what
additional features I'd get?
```

What to verify: The agent should respond with specific plan details from the knowledge base, including features of the Premium plan.
Turn 2: Build on Previous Context
Ask a follow-up that requires remembering Turn 1:

```
That sounds great. How much more per month would the Premium plan
cost compared to what I'm currently paying on Basic?
```

What to verify: The agent should reference the Premium plan (from Turn 1) and provide pricing comparison without you needing to re-state which plans you're comparing.
Turn 3: Verify Deep Context Retention
Ask a question that requires context from both previous turns:

```
OK, let's go ahead with the upgrade. Can you also check if I have
any outstanding billing issues before we process the change?
```

What to verify: The agent should:
 
- Acknowledge the upgrade request (context from Turns 1-2) 
- Reference the customer identity (Sarah / CUST-003 from Turn 1) 
- Check billing information for the specified customer 

Context Retention

The key indicator of success is that the agent maintains conversation context across all 3 turns. By Turn 3, the agent should still know who you are, what plan you're discussing, and what action you've requested, without you repeating that information.

Error Handling Test
Test that the UI handles agent failures gracefully:

How to Test Error Handling

To verify error handling behavior:

Option 1: Temporarily stop your agent

Commit your project first so you can restore the configuration afterwards (`agentcore create` initialized a git repository in the project):

```
# or cd ~/environment/<YourAgentName>
cd ~/environment/CustomerServiceAgent
git add -A && git commit -q -m "Before error-handling test" || true
# Empty every resource collection in agentcore.json, then apply it (removes the stack; up to 25 minutes)
agentcore remove all --yes
agentcore deploy --yes
```

Then send a message in the chat UI. You should see:

- An error message like "The agent is currently unavailable. Please try again." 
- All previous conversation history should remain visible on screen 
- The UI should not crash or show a blank page 

After testing, restore the configuration and redeploy your agent (the runtime gets a new ARN, so update `AGENTCORE_ENDPOINT` in the chat UI afterwards):

```
git checkout agentcore/agentcore.json
agentcore deploy
agentcore status --json | jq -r '.resources[] | select(.resourceType=="runtime") | .arn'
```

Option 2: Check the error message display

If you don't want to stop your agent, verify the error handling code is in place:

```
# Check that your app handles connection errors
grep -r "unavailable\|error\|try\|except" ~/environment/chat-ui/
```

Full Validation Checklist
Run through this checklist to confirm Lab 6 is complete:

```
# 1. Verify ECS service is healthy
aws ecs describe-services --cluster $ECS_CLUSTER --services agent-chat-ui \
    --query "services[0].runningCount" --output text
# Expected: 1

# 2. Verify health endpoint responds
TASK_ARN=$(aws ecs list-tasks --cluster $ECS_CLUSTER --service-name agent-chat-ui --query "taskArns[0]" --output text)
ENI_ID=$(aws ecs describe-tasks --cluster $ECS_CLUSTER --tasks $TASK_ARN \
    --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text)
PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID \
    --query "NetworkInterfaces[0].Association.PublicIp" --output text)

curl -s http://${PUBLIC_IP}:8888/health | python3 -m json.tool
# Expected: {"status": "healthy"}

# 3. Open the UI in your browser
echo "Open: http://${PUBLIC_IP}:8888"
```

Testing the UI locally instead?

If you want to run the chat UI on the IDE instance rather than on ECS, start it on port 8888 (`cd ~/environment/chat-ui && python3 app.py`) and open the proxied port in your browser:

```
python3 -m webbrowser $IDE_URL/proxy/8888/
```

`IDE_URL` is pre-set in the IDE terminal, and the IDE proxies local ports under `/proxy/<port>/`, so this opens the UI in the same browser session that has the Kiro IDE open. Never stop a process on port 8080; that is the Kiro IDE Browser. If port 8888 is busy, free only that port: `lsof -ti:8888 | xargs kill -9`.

Then in the browser:
 
- Chat UI loads and displays an input field 
- Sending a message shows a typing indicator 
- Agent response streams token-by-token (not all at once) 
- 3-turn conversation maintains context (Turn 3 references Turn 1 info) 
- Error scenario shows a user-friendly message without clearing history 

Expected Behavior

Successful 3-turn conversation:

The chat window should show alternating user and agent messages. The agent's responses should:

- Turn 1: Provide Premium plan details (features, services included) 
- Turn 2: Compare pricing between Basic and Premium plans, referencing the plans discussed in Turn 1 
- Turn 3: Acknowledge the upgrade request AND attempt to check billing for the customer, referencing the customer name/ID from Turn 1 

Token streaming:

You should see the agent's response appear word-by-word or in small chunks, not as a single block after a long delay. This confirms real-time streaming is working.

Error handling:

When the agent is unavailable, the UI should display an inline error message (not a browser error page) and keep the conversation history visible.

Note

The exact wording of agent responses will vary based on your system prompt, model version, and knowledge base content. The key validation is that context is retained across turns and responses are streamed incrementally.

Lab 6 Summary
You have built and deployed a production-ready chat UI for your AI agent. Your application:
 
- Streams tokens in real-time from AgentCore 
- Runs as a container on ECS Fargate with health checks 
- Maintains multi-turn conversation context 
- Handles agent unavailability gracefully 
You now have a complete end-to-end system: a Strands SDK agent with memory, tool use, identity management, and observability, accessible through a web interface running on AWS infrastructure.
Next step
This completes Part 1, the guided build. Continue to Part 2, Lab 7: Bring Your Own Use Case, to build and deploy an agent for your own use case with Kiro Specs or AI-DLC. Teams on the 2-hour workshop format finish here and proceed to Cleanup.
---

<!-- page: 24_lab-7-bring-your-own-use-case -->
# Lab 7: Bring Your Own Use Case

Lab 7: Bring Your Own Use Case
Your Mission
Lab 7 is Part 2 of the workshop: your use case. Your team picks the problem, an agent idea of your own or the sample Investment Assistant, and ships it to Amazon Bedrock AgentCore Runtime under the production guardrails on this page. You can start here straight after Getting Started, using the workshop as a way to ship your own production agent with Kiro Specs or AI-DLC, or come here after the guided build in Part 1 (Labs 1 to 6). This is the lab that hackathon formats are built around; teams on the 2-hour workshop format finish with Part 1 and go to Cleanup.
There are two build paths, each on its own page. Build with Kiro Specs applies the Kiro spec workflow (requirements, design, tasks, then execution) to your own use case. Build with AI-DLC runs the AI-Driven Development Lifecycle workflow through the `/aidlc` command; that page starts with a five-minute install of AI-DLC in your IDE terminal. Both paths end at the same place: the checks on the Verify Your Agent page, which confirm every guardrail below.
Kiro does the building. Your job is to own the brief, review each plan against the guardrails before you approve it, and verify the result.
Estimated duration: 4 hours to 2 days.
A Kiro Specs build or an AI-DLC `express` build fits in about 4 hours, and running the full AI-DLC workflow through every phase can take up to 2 days.
Prerequisites
Required: Getting Started completed.
 
- AWS Event Setup verification passing, with every command in "Verify Your Environment" returning its expected result (if not, return to AWS Event Setup) 
- Kiro IDE Browser open, with Kiro signed in (if not, return to Kiro IDE Browser) 
- Steering files and MCP servers in place (if not, return to Steering, Skills and MCP Servers) 
Recommended, not required:
 
- Part 1 (Labs 1 to 6), the guided introduction to the same building blocks on the AnyCompany Telecom agent (start at Lab 1) 
Needed only if your use case answers from documents:
 
- A Knowledge Base. Upload your documents to `$S3_BUCKET_NAME` and ask Kiro in your brief to create a Knowledge Base from them, the same way the "Create Knowledge base (Optional)" section of Lab 1 Challenge 1 does. 
What you will have at the end
 
- An AgentCore project under `~/environment` built for your use case 
- A deployed AgentCore Runtime agent with observability enabled 
- At least one tool your agent calls (Gateway target, MCP server, or a local tool: Strands `@tool` or LangChain `@tool`) 
- A spec folder or an `aidlc/` folder documenting how the agent was built 
Guardrails (apply to both build paths)
The guardrails below apply to both build paths; they are the fixed interface every Lab 7 agent must satisfy.

| Guardrail | Requirement |
| Deploy | Deployed to AgentCore Runtime with agentcore deploy, from a project created with agentcore create in ~/environment whose name is not CustomerServiceAgent (the Lab 1 project) |
| Observability | UNIFIED_TRACES_DESTINATION_ENABLED set to true as an entry in the runtime's envVars list in agentcore/agentcore.json |
| Tool | At least one tool exposed: an AgentCore Gateway target, an MCP server, or a local tool (Strands @tool or LangChain @tool) |

The framework can be Strands, LangGraph or your own code, as long as the project is created or the runtime registered with the AgentCore CLI. The brief template on each build page repeats these three requirements word for word, and the checks on Verify Your Agent confirm each one.
Lab Structure
 
- Pick a Use Case: bring your own idea or start from a seed, and decide the framework before you brief Kiro 
- Build with Kiro Specs: requirements, design, and tasks you approve, then execution (about 4 hours) 
- Build with AI-DLC: install AI-DLC, then run `/aidlc` with the profile that fits your time (4 hours to 2 days) 
- Verify Your Agent: three checks, one per guardrail, that are the same whichever build path you took 

How this lab works

Read Pick a Use Case, then follow one build page, Kiro Specs or AI-DLC, not both. Each build page ends by sending you to Verify Your Agent. Supporters review your brief and plans against the guardrails table above; if a plan misses a guardrail, do not approve it, reply with feedback that names the missing guardrail.

- Pick a Use Case
- Build with Kiro Specs
- Build with AI-DLC
- Verify Your Agent

---

<!-- page: 25_lab-7-bring-your-own-use-case__pick-a-use-case -->
# Pick a Use Case

Pick a Use Case
Bring your own idea, or start from one of the seeds below. Each seed names a knowledge source to upload and a tool that meets the Tool guardrail. The Investment Assistant is also the sample brief on the Build with AI-DLC page, so you can compare both build paths on the same brief.

| Use case | Description | Knowledge source | Suggested tool |
| Investment Assistant | An assistant that explains a model portfolio's holdings, fees, and risk profile in plain language and never gives personalized investment advice. | Fund fact sheets and a glossary of investment terms, uploaded to $S3_BUCKET_NAME | A get_portfolio_summary tool (Strands @tool, or LangChain @tool for LangGraph teams) that returns sample holdings from a local JSON file |
| IT Helpdesk Agent | An agent that walks employees through runbook steps for common incidents and opens a ticket when a step fails. | Runbooks and FAQ pages uploaded to $S3_BUCKET_NAME | The Lab 3 ticketing backend as a Gateway target, or a create_ticket @tool |
| Travel Concierge | An agent that proposes itineraries from destination guides and checks fare rules before suggesting a booking. | Destination guides and fare-rule summaries uploaded to $S3_BUCKET_NAME | A check_availability @tool backed by a mock schedule |
| Clinical Trial FAQ | An agent that answers patient questions about a public trial protocol and pre-screens eligibility against published criteria without storing patient data. | Public trial protocol summaries uploaded to $S3_BUCKET_NAME | A prescreen_eligibility @tool that evaluates the published criteria |

Prepare your inputs
Before you brief Kiro, have these four values ready; both brief templates ask for them:
 
- Use case: one sentence that says what the agent does and what it must never do (the Investment Assistant never gives personalized investment advice). 
- Persona: who talks to the agent. 
- Knowledge source: the documents the agent answers from. Upload them to `$S3_BUCKET_NAME` now if your use case needs them; your brief then asks Kiro to create a Knowledge Base from them, as the "Create Knowledge base (Optional)" section of Lab 1 Challenge 1 does. 
- Tools: the tool that satisfies the Tool guardrail, from the table above or your own. 
Pick a project name for `agentcore create` that is not `CustomerServiceAgent` (the Lab 1 project), so the Lab 7 deployment never overwrites a Lab 1 agent. The build pages refer to it as `<YourLab7Project>`.

Bringing LangGraph or existing code

The guardrails do not require Strands. If your team builds with LangGraph or brings code it already has, decide that now, before the first brief:

- Confirm `langgraph-agent-coding.md` is in `~/environment/.kiro/steering/` and `strands-agent-coding.md` is gone (Getting Started Step 3b). With the Strands file still in place, Kiro generates Strands code. 
- State the framework in the first line of your brief, for example "a LangGraph agent" or "my existing agent code in `~/environment/<folder>`". 
- When you review the plan (`tasks.md` in Kiro Specs, the Inception plan in AI-DLC), check that the project task runs `agentcore create --name <YourLab7Project> --template agent-python-langchain`, or `agentcore create --name <YourLab7Project>` followed by `agentcore add runtime --name <YourLab7Project> --language python --protocol HTTP` for existing code. 
- Copy existing code into `~/environment` first (for example `~/environment/my-agent-src/`), so Kiro can read it and move it into `app/<YourLab7Project>/` with its `main.py` and `pyproject.toml`. 

Next step
Choose one build path and follow its page to the end:
 
- Build with Kiro Specs: the spec workflow from Lab 1 applied to your use case, about 4 hours. 
- Build with AI-DLC: the AI-Driven Development Lifecycle through `/aidlc`, 4 hours to 2 days depending on the profile. 
Both pages end at Verify Your Agent.

---

<!-- page: 26_lab-7-bring-your-own-use-case__build-with-kiro-specs -->
# Build with Kiro Specs

Build with Kiro Specs
This path applies the Kiro spec workflow, the same one Lab 1 uses, to your own use case. A [Kiro Specs](https://kiro.dev/docs/specs/) workflow turns your brief into three reviewable documents: a `requirements.md` with user stories and acceptance criteria, a `design.md` with the technical approach, and a `tasks.md` with an ordered implementation plan. You approve each document before Kiro writes code, then Kiro executes the tasks and you verify each result against the guardrails on the Lab 7 page.
Before you start, have the four inputs from Pick a Use Case ready: use case, persona, knowledge source, and tools.
The spec workflow
The five steps are the same as in Lab 1, and their time boxes add up to 4 hours, the short end of this lab. Teams with more time extend the Execute step with the optional stretch goals below.
 
- Start a spec (10 min). In the Kiro chat panel, open a new session and choose Spec from "Start with a built-in agent" (or Quick Spec, see the time box below). In Kiro CLI, start `kiro-cli chat` from `~/environment` and run `/spec new <name>`. When asked, pick Build a Feature and the Requirements workflow. 
- Requirements (30 min). Paste your brief from "Your spec brief" below. Kiro drafts `requirements.md` with user stories and acceptance criteria. Check it against each of the three guardrails (Deploy, Observability, Tool): every guardrail must appear as an acceptance criterion. If one is missing, do not approve; reply to Kiro with feedback that names the missing guardrail, for example "Add an acceptance criterion for the Observability guardrail". 
- Design (30 min). Kiro drafts `design.md` from the approved requirements. Review it for the project name, the tool, and the observability setting, then approve or give feedback. 
- Tasks (20 min). Kiro drafts `tasks.md`. Check it against each of the three guardrails: the task list must create the project with `agentcore create --template ...`, set the observability variable, build the tool, and deploy with `agentcore deploy`. If a guardrail has no task, do not approve; reply to Kiro with feedback that names the missing guardrail. 
- Execute (150 min). Start the tasks one at a time and confirm each task's result (the files it changed and any test output) before the next task starts. When the last task is done, run the checks on Verify Your Agent. 

Short on time? Use Quick Spec. If you have less than 2 hours, use Quick Spec instead of Spec. Quick Spec generates requirements, design, and tasks in one pass, and the review of `tasks.md` against the three guardrails still applies before Kiro builds.

Where the spec lives

The spec files land in `~/environment/.kiro/specs/<name>/` (`requirements.md`, `design.md`, `tasks.md`). You can open them in the Explorer and edit them directly; Kiro picks up your edits. The agent project is scaffolded with `agentcore create --name <YourLab7Project> --template agent-python-strands`, run from `~/environment` (LangGraph teams use the `agent-python-langchain` template, and existing code is registered with `agentcore add runtime`: see "Bringing LangGraph or existing code" on Pick a Use Case). Its name must not be `CustomerServiceAgent` (the Lab 1 project), so the Lab 7 deployment never overwrites a Lab 1 agent.

Your spec brief
Paste this template into the chat after you start the spec. Replace the four placeholders and keep the three guardrail lines unchanged, so each one becomes an acceptance criterion.

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

If your team builds with LangGraph or brings existing code, start the brief with the framework, as described in "Bringing LangGraph or existing code" on Pick a Use Case.
Optional stretch goals: Labs 2 to 6 capabilities
None of these is needed to meet the guardrails. If you have time left after the checks on Verify Your Agent pass, add any of them to your Lab 7 agent. Each one links to the lab that shows how it was done on the AnyCompany Telecom agent, so you can follow it even if you skipped that lab:
 
- Memory (Lab 2): add short-term memory for your persona's sessions and long-term memory for facts about the user. 
- Gateway tools (Lab 3): register your own Lambda tool as a Gateway target, or reuse the ticketing backend as a practice target. 
- Identity (Lab 4): scope data access to the authenticated end user of your domain. 
- Observability (Lab 5): use `agentcore traces runtime list` to confirm tool spans for your tool. 
- Chat UI (Lab 6): build a chat UI for the new agent the way Lab 6 does, or connect the Lab 6 chat UI to it if you built one. 
Next step
When the last task is done, run the three checks on Verify Your Agent.

---

<!-- page: 27_lab-7-bring-your-own-use-case__build-with-ai-dlc -->
# Build with AI-DLC

Build with AI-DLC
This path runs the AI-Driven Development Lifecycle workflow through the `/aidlc` command. It starts with a five-minute install of AI-DLC in your IDE terminal, then takes your brief through requirements, code generation, tests, and deployment, with an approval from you before each major step. Before you start, have the four inputs from Pick a Use Case ready: use case, persona, knowledge source, and tools.
Install AI-DLC (about 5 minutes)
The steps below download the pinned AI-DLC release from github.com and configure it for Kiro in `~/environment`; the install takes about 5 minutes. AI-DLC is not part of the pre-installed toolchain, which is why this page starts with the install. Run each command in the IDE terminal as shown, without `sudo`: the terminal already runs as the `participant` user. No sign-in is needed beyond the pre-authenticated Kiro IDE Browser. If a step does not give its expected result, open the Troubleshooting section further down this page.
Step 1: Back up your Kiro configuration

```
if [ -d ~/aidlc-backup ]; then
echo "Existing backup kept in ~/aidlc-backup"
else
rm -rf ~/aidlc-backup.tmp && mkdir ~/aidlc-backup.tmp &&
cp -a ~/environment/.kiro ~/aidlc-backup.tmp/environment-kiro &&
cp -a ~/.kiro/settings ~/aidlc-backup.tmp/kiro-settings &&
mv ~/aidlc-backup.tmp ~/aidlc-backup &&
echo "Backup created in ~/aidlc-backup"
fi
```

Expected: `Backup created in ~/aidlc-backup` the first time, or `Existing backup kept in ~/aidlc-backup` when you run the steps again.
Step 2: Download and run the installer

```
AIDLC_URL=github.com/awslabs/aidlc-workflows/releases/download/v2.11.1/install.sh
curl -fsSL -o /tmp/aidlc-install.sh "https://$AIDLC_URL" &&
sh /tmp/aidlc-install.sh --yes
```

Expected: the installer verifies its downloads and finishes without an error. The command saves the installer to a file first, so you can read it with `less /tmp/aidlc-install.sh` before running it if you want to.
Step 3: Put aidlc on your PATH

```
export PATH="$HOME/.local/bin:$PATH"
grep -qxF 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc ||
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
aidlc --version
```

Expected: the output names version 2.11.1, and new terminals pick up the same PATH from `~/.bashrc`.
Step 4: Configure AI-DLC for your workspace

```
cd ~/environment && aidlc config --harness kiro-ide --yes
```

Expected: the command finishes without an error after writing the AI-DLC agent, skill, steering, and hook files under `~/environment/.kiro/` and a section in `~/environment/AGENTS.md`.
Step 5: Check the install

```
cd ~/environment && aidlc doctor; echo "aidlc doctor exit code: $?"
```

Expected: the last line is `aidlc doctor exit code: 0` and no line above it reports an error or a missing dependency.
Step 6: Confirm the workshop configuration is intact

```
ls ~/environment/.kiro/skills/ ~/environment/.kiro/steering/
jq '.mcpServers | keys' ~/.kiro/settings/mcp.json
diff -rq ~/aidlc-backup/environment-kiro ~/environment/.kiro |
grep -v "^Only in $HOME/environment/.kiro" || echo "workspace .kiro: no workshop file changed"
diff -rq ~/aidlc-backup/kiro-settings ~/.kiro/settings |
grep -v "^Only in $HOME/.kiro/settings" || echo "Kiro settings: no file changed"
```

Expected:
 
- The skills listing shows `aidlc`, `build-chat-ui`, `build-customer-service-agent`, and `deploy-chat-ui-to-ecs`. 
- The steering listing shows `agentcore-deployment.md` and either `strands-agent-coding.md` or `langgraph-agent-coding.md` (Getting Started Step 3b) from Getting Started, plus the AI-DLC steering files. 
- The key list contains `"awslabs.ecs-mcp-server"` and `"bedrock-agentcore-mcp-server"`; `"strands-agents"` is expected only for Strands teams. 
- The last two lines are `workspace .kiro: no workshop file changed` and `Kiro settings: no file changed`. 
The comparison ignores the files AI-DLC added and prints only workshop files that changed or were deleted. If anything is missing or listed as changed, use Step 7.
Step 7: Restore from the backup

If Step 6 reports a missing or changed file: restore from the backup

```
cp -a ~/aidlc-backup/environment-kiro/. ~/environment/.kiro/
cp -a ~/aidlc-backup/kiro-settings/. ~/.kiro/settings/
```

Expected: no output. Run Step 6 again; it now prints the expected output above, and then reload the IDE browser tab as in Step 8. Files AI-DLC added have no counterpart in the backup, so they stay in place and the `aidlc` agent stays available.

Step 8: Reload the IDE
Reload the Kiro IDE Browser tab in your browser, open a new chat in the Kiro chat panel, and open the agent picker.
Expected: the agent picker lists `aidlc`.

Trust this folder

If Kiro asks whether to trust the folder, accept it. The prompt appears because `~/environment/.kiro/hooks/` now contains AI-DLC hook files that run commands, and Kiro runs hooks only in trusted folders. If a Restricted Mode banner shows at the top of the window instead, select Manage on it, then Trust, and reload the tab again.

What AI-DLC is
[AI-DLC](https://github.com/awslabs/aidlc-workflows) (AI-Driven Development Lifecycle) takes your brief through five phases in order, and each phase leaves its own artifact for you to review. Initialization creates the workflow record and its state file, `aidlc-state.md`. Ideation captures the intent and scope, starting with `intent-statement.md`. Inception turns the brief into `requirements.md` and, in the larger profiles, a plan of units of work. Construction generates the code and tests and records the results in `test-results.md`. Operation deploys the agent and records the run in `deployment-log.md`. The `express` profile skips Ideation and the design stages, `workshop` skips only Ideation, and `feature` runs every phase. Kiro Specs gives you three documents in one spec folder (`requirements.md`, `design.md`, `tasks.md`) before any code is written; AI-DLC spreads the same work over one folder per phase and stage, and carries on through tests to deployment.
Start in the Kiro chat panel
The sample brief is the Investment Assistant from the seed table on Pick a Use Case:
Investment Assistant: An assistant that explains a model portfolio's holdings, fees, and risk profile in plain language and never gives personalized investment advice.
Open a new chat in the Kiro chat panel and choose `aidlc` in the agent picker. Every new chat starts on the Default agent, so choose `aidlc` again whenever you open a new chat. Then send:

```
/aidlc express Build an Investment Assistant
```

`/aidlc express <your own brief>` works the same way for your own use case. For a build longer than about 4 hours, replace `express` with the profile for your time from "Profile and time box" below. Whichever brief you send, include the guardrail lines from "Your brief" below in the same message.
Start in Kiro CLI
To run AI-DLC from the terminal instead, start the chat from `~/environment`:

```
cd ~/environment
kiro-cli chat --agent aidlc
```

The chat must start from `~/environment`: the `aidlc` agent and skill are project files in `~/environment/.kiro/`, so `/aidlc` is recognized only in a chat started there. Then send the same `/aidlc` message as in the chat panel.
Your brief
Send `/aidlc` and your profile (for example `/aidlc express`) followed by this brief. Replace the four placeholders and paste the three guardrail lines unchanged, so the generated plan targets AgentCore Runtime with observability enabled and at least one tool. For the Investment Assistant, fill the placeholders from its row in the seed table on Pick a Use Case. If your team builds with LangGraph or brings existing code, start the brief with the framework, as described in "Bringing LangGraph or existing code" on that page.

```
Build <USE CASE>: an agent for <PERSONA> that answers from <KNOWLEDGE SOURCE> and can
call <TOOLS>.

Lab 7 guardrails (paste unchanged):

- Deployed to AgentCore Runtime with `agentcore deploy`, from a project created with `agentcore create` in `~/environment` whose name is not `CustomerServiceAgent` (the Lab 1 project)
- `UNIFIED_TRACES_DESTINATION_ENABLED` set to `true` as an entry in the runtime's `envVars` list in `agentcore/agentcore.json`
- At least one tool exposed: an AgentCore Gateway target, an MCP server, or a local tool (Strands `@tool` or LangChain `@tool`)

Ask me clarifying questions before you write the requirements, and include every
guardrail above in them.
```

Profile and time box
Pick the profile that fits the time your team has. Each row includes the install, which takes about 5 minutes.

| Time available | Profile | What it runs | Start with |
| About 4 hours | express | Requirements, code generation, build and test, and the conditional deploy and observability stages; no Ideation and no design pass | /aidlc express <brief> |
| About 1 day | workshop | Every Inception, Construction, and Operation stage, including the design stages, with a minimal test set; no Ideation | /aidlc workshop <brief> |
| Up to 2 days | feature | Every stage of every phase, from Ideation through Operation | /aidlc feature <brief> |

If code generation has not started when half of your planned time has passed (for example 2 hours into a 4-hour `express` build), restart with `/aidlc poc <brief>`, the smallest useful implementation.
Where AI-DLC writes
AI-DLC keeps its records in `~/environment/aidlc/`. Each request becomes an intent folder, `aidlc/spaces/<space>/intents/<YYMMDD>-<label>/`, with one folder per phase and, inside each phase, one folder per stage (for example `inception/requirements-analysis/`). The file `aidlc/active-space` names the space in use (`default` unless you create another), and memory that carries across requests lives under `aidlc/spaces/<space>/memory/`. The agent code itself goes into your AgentCore project under `~/environment`, not into `aidlc/`.
The artifact file to open for each phase, inside the intent folder:
 
- Initialization: `aidlc-state.md`, which tracks where the workflow is 
- Ideation (skipped by `express` and `workshop`): `ideation/intent-capture/intent-statement.md` 
- Inception: `inception/requirements-analysis/requirements.md` 
- Construction: `code-summary.md` in a `code-generation/` folder under `construction/`, and `construction/build-and-test/test-results.md` 
- Operation: `operation/deployment-execution/deployment-log.md` 
AI-DLC asks for your approval in the chat panel before major steps. Before you approve a plan, check it against each of the three guardrails (Deploy, Observability, Tool). If one is missing, do not approve; reply with feedback that names the missing guardrail.
Troubleshooting

Common Issues

Find your symptom below and apply its remedy.

- `aidlc: command not found`: run `export PATH="$HOME/.local/bin:$PATH"`, or open a new terminal (Step 3 adds the line to `~/.bashrc`). 
- The installer refuses to run: rerun Step 2 without `sudo`; the IDE terminal already runs as `participant` (`whoami` prints `participant`). If you did not use `sudo` and `echo $SUDO_USER` prints a name, run `env -u SUDO_USER -u SUDO_UID -u SUDO_GID -u SUDO_COMMAND sh /tmp/aidlc-install.sh --yes`. 
- The download fails: run `curl -fsSI https://github.com` to check that github.com is reachable, rerun Step 2, and ask your facilitator if it still fails. 
- The `aidlc` agent is missing from the agent picker: reload the IDE browser tab and accept the trust prompt if Kiro shows it, then run `cd ~/environment && aidlc doctor`. 
- `/aidlc` is not recognized in Kiro CLI: start the chat from `~/environment` with `kiro-cli chat --agent aidlc`. 
- Plain `kiro-cli chat` from `~/environment` opens on the `aidlc` agent: run the command in "Open plain Kiro CLI chats on the Default agent" below. 
- Spec or Quick Spec is missing from a new chat, or a workshop skill, steering file, or MCP server changed after Step 4: run Step 7, then reload the IDE browser tab. If Spec and Quick Spec are still missing, open the Kiro settings, search for "Workflows", and turn the setting on. 
- If AI-DLC still cannot be installed, switch to Build with Kiro Specs; it ends at the same guardrails and the same checks on Verify Your Agent. 

Open plain Kiro CLI chats on the Default agent

```
cd ~/environment && jq 'del(."chat.defaultAgent")' .kiro/settings/cli.json > /tmp/cli.json &&
mv /tmp/cli.json .kiro/settings/cli.json
```

Expected: plain `kiro-cli chat` from `~/environment` opens on the Default agent, and `kiro-cli chat --agent aidlc` still opens AI-DLC.

Next step
When the Operation phase has deployed your agent (or your `express` build reports the deploy stage done), run the three checks on Verify Your Agent. They are the same checks the Kiro Specs path uses: the expected end state is a project under `~/environment` that passes every one.

---

<!-- page: 28_lab-7-bring-your-own-use-case__verify-your-agent -->
# Verify Your Agent

Verify Your Agent
Whichever build path you followed, confirm your Lab 7 agent meets the three guardrails from the Lab 7 page before moving on. Replace `<YourLab7Project>` with your Lab 7 project name; it is the only value you fill in, and every other part of these commands runs unchanged on either path.
Check 1: Deploy

```
cd ~/environment/<YourLab7Project> && agentcore status
```

Expected: the output lists your Lab 7 runtime as `deployed` with its ARN, which confirms the Deploy guardrail: Deployed to AgentCore Runtime with `agentcore deploy`, from a project created with `agentcore create` in `~/environment` whose name is not `CustomerServiceAgent` (the Lab 1 project).
Check 2: Tool
Run the next command in the same terminal, so it runs from inside your project directory.

```
agentcore invoke --runtime agent --payload '{"prompt":"Describe your use case in one sentence, then call one of your tools and show what it returns."}'
```

`agent` is the runtime name every AgentCore CLI template declares; if your `agentcore/agentcore.json` names the runtime differently, use that name. Expected: a streamed answer that describes your use case and includes data returned by your tool, which confirms the Tool guardrail (At least one tool exposed: an AgentCore Gateway target, an MCP server, or a local tool (Strands `@tool` or LangChain `@tool`)).
Check 3: Observability

```
aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/ --query "logGroups[].logGroupName" --output text
```

Expected: the list includes `/aws/bedrock-agentcore/runtimes/{agent-id}-DEFAULT` for the agent ID at the end of the runtime ARN shown by `agentcore status`, which confirms the Observability guardrail (`UNIFIED_TRACES_DESTINATION_ENABLED` set to `true` as an entry in the runtime's `envVars` list in `agentcore/agentcore.json`); `agentcore traces runtime list --since 15m`, run from your project directory, shows the trace of the invoke above.
If a check does not give its expected output, fix it with Kiro on the build page you used (Kiro Specs or AI-DLC), then run the checks again.
Lab Completion Checklist
You have completed Lab 7 when:
 
- Deploy: `agentcore status` from `~/environment/<YourLab7Project>` shows your runtime as `deployed` 
- Tool: the invoke above returns data from at least one tool 
- Observability: the agent's log group exists and `agentcore traces runtime list` shows the trace of the invoke 
- Record: a spec folder (`~/environment/.kiro/specs/<name>/`) or an `aidlc/` intent folder documents how the agent was built 
Next step
When all three checks pass, your Lab 7 agent is complete. If you reproduce the labs in your own account, run the Cleanup page's manual Step 1 from `~/environment/<YourLab7Project>` as well, because `cleanup_workshop` removes only the agent in the folder you run it from. Proceed to Cleanup.

---

<!-- page: 29_cleanup -->
# Cleanup

At an AWS-hosted event
Your team account was created for this event and is closed automatically when the event ends. Every resource in it is removed at that point, including the resources you created during the labs. You do not need to do anything.
The only reason to clean up during the event is to reset and rebuild: for example, to start Lab 1 again with a different agent design. In that case, run the cleanup command below and the pre-provisioned infrastructure (Knowledge Base S3 bucket, ECS cluster, Kiro IDE Browser) stays in place for your next attempt.
If you reproduce the labs in your own account
The labs can be reproduced after the event with your own AWS account and Kiro license. In that case you are responsible for every resource you create, and this page is how you remove them. The one resource that keeps billing while idle is the Amazon OpenSearch Serverless collection behind the Knowledge Base; the cleanup command deletes it. Model invocations are billed per token. Review the pricing pages before you start, and run the cleanup when you finish:
 
- [Amazon Bedrock pricing](https://aws.amazon.com/bedrock/pricing/) (model invocations, Knowledge Bases) 
- [Amazon Bedrock AgentCore pricing](https://aws.amazon.com/bedrock/agentcore/pricing/) (Runtime, Memory, Gateway, Identity, Observability) 
- [Amazon OpenSearch Serverless pricing](https://aws.amazon.com/opensearch-service/pricing/#Amazon_OpenSearch_Serverless) (Knowledge Base vector store) 
- [Amazon ECS and AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/) (Lab 6 chat UI) 
- [Amazon ECR pricing](https://aws.amazon.com/ecr/pricing/) (Lab 6 container image) 
- [Amazon DynamoDB pricing](https://aws.amazon.com/dynamodb/pricing/) (Lab 3 backend tables) 
- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/) (Lab 3 MCP tool functions) 
- [Amazon API Gateway pricing](https://aws.amazon.com/api-gateway/pricing/) (Lab 3 backend API) 
- [Amazon CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/) (Lab 5 traces and logs) 
- [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/) (Knowledge Base documents) 
- [Kiro pricing](https://kiro.dev/pricing/) (your own Kiro license, outside the event) 
Clean up with one command
Run the cleanup alias from your terminal:

```
cleanup_workshop
```

It removes the resources the labs created, in dependency order:
 
- The AgentCore agent, its runtime, memory, gateway, and configuration 
- The ECS service for the chat UI, if you deployed it in Lab 6 
- The Lab 3 backend: API Gateway, the three Lambda MCP functions, the DynamoDB tables, and their IAM role 
- The Bedrock Knowledge Base, its data source, its OpenSearch Serverless collection and policies, and its IAM role 
You see progress output as each resource is removed. The command is safe to run more than once; resources that are already gone are skipped.

What the command does not remove

At an AWS event: the Knowledge Base S3 bucket, the ECS cluster, and the Kiro IDE Browser are part of the pre-provisioned infrastructure and are removed when the event ends. The workshop creates no VPC; Lab 6 runs in the account's default VPC.

In your own account: after `cleanup_workshop`, also delete the ECR repository from Lab 6 (`agent-chat-ui`), the Knowledge Base document bucket (`anycompany-telecom-kb-<account>-<region>`), and the CloudWatch log groups the labs created, using the commands in the manual section below. If you deployed the workshop infrastructure with CloudFormation, delete that stack last.

Manual cleanup
Use these if the one-command cleanup fails part way, or if you want to remove a single lab's resources. Run them in this order.

Step 1: Remove the AgentCore agent (Lab 1, 2, 3, 4, 5)

From your agent project folder:

```
# or cd ~/environment/<YourAgentName>
cd ~/environment/CustomerServiceAgent
agentcore remove all --yes
agentcore deploy --yes
agentcore status
```

`agentcore remove all --yes` empties every resource collection in `agentcore.json` (runtime, memory, gateway and targets) and prints `removed all resources from project`; `agentcore deploy --yes` confirms removing the target's CloudFormation stack now that the project declares nothing to deploy (it prints `removing stack AgentCore-CustomerServiceAgent-default` and takes up to 25 minutes while the runtime endpoint and memory are deleted), and `agentcore status` then lists no deployed resource:

```
{
  "projectName": "CustomerServiceAgent",
  "target": "default",
  "region": "us-east-1",
  "resources": []
}
```

The runtime's CloudWatch log group `/aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT` is not part of the stack; delete it with `aws logs delete-log-group --log-group-name <name>` if you want the account fully clean.

Step 2: Delete the chat UI service and image (Lab 6)

```
aws ecs update-service --cluster agent-workshop-cluster --service agent-chat-ui --desired-count 0
aws ecs delete-service --cluster agent-workshop-cluster --service agent-chat-ui --force
aws ecr delete-repository --repository-name agent-chat-ui --force
aws logs delete-log-group --log-group-name /ecs/agent-chat-ui
```

If you used a different service or repository name in Lab 6, replace `agent-chat-ui` with the name you used.

Step 3: Delete the backend systems (Lab 3)

```
API_ID=$(aws apigateway get-rest-apis --query "items[?name=='MCP-Server-API'].id" --output text)
aws apigateway delete-rest-api --rest-api-id "$API_ID"

for fn in billing-mcp ticketing-mcp escalation-mcp; do
  aws lambda delete-function --function-name "$fn"
  aws logs delete-log-group --log-group-name "/aws/lambda/$fn" 2>/dev/null || true
done

for tbl in customers billing tickets; do
  aws dynamodb delete-table --table-name "$tbl"
done

aws iam detach-role-policy --role-name mcp-server-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role-policy --role-name mcp-server-lambda-role --policy-name DynamoDBAccess
aws iam delete-role --role-name mcp-server-lambda-role
```

Step 4: Delete the Knowledge Base and its collection (Lab 1)

```
KB_ID=$(aws bedrock-agent list-knowledge-bases --query "knowledgeBaseSummaries[?name=='anycompany-telecom-kb'].knowledgeBaseId" --output text)
for ds in $(aws bedrock-agent list-data-sources --knowledge-base-id "$KB_ID" --query 'dataSourceSummaries[].dataSourceId' --output text); do
  aws bedrock-agent delete-data-source --knowledge-base-id "$KB_ID" --data-source-id "$ds"
done
aws bedrock-agent delete-knowledge-base --knowledge-base-id "$KB_ID"

# The OpenSearch Serverless collection bills per OCU-hour while it exists
COLL_ID=$(aws opensearchserverless batch-get-collection --names anycompany-telecom-kb --query 'collectionDetails[0].id' --output text)
aws opensearchserverless delete-collection --id "$COLL_ID"
aws opensearchserverless delete-access-policy --name anycompany-telecom-kb-access --type data
aws opensearchserverless delete-security-policy --name anycompany-telecom-kb-enc --type encryption
aws opensearchserverless delete-security-policy --name anycompany-telecom-kb-net --type network

aws iam delete-role-policy --role-name anycompany-telecom-kb-role --policy-name anycompany-telecom-kb-policy
aws iam delete-role --role-name anycompany-telecom-kb-role
```

In your own account, also remove the document bucket the Knowledge Base script created:

```
BUCKET="anycompany-telecom-kb-$(aws sts get-caller-identity --query Account --output text)-$AWS_REGION"
aws s3 rm "s3://$BUCKET" --recursive
aws s3 rb "s3://$BUCKET"
```

Verify

```
agentcore status
aws ecs list-services --cluster agent-workshop-cluster
aws lambda list-functions --query "Functions[?contains(FunctionName,'-mcp')].FunctionName"
aws dynamodb list-tables
aws bedrock-agent list-knowledge-bases --query "knowledgeBaseSummaries[].name"
aws opensearchserverless list-collections --query "collectionSummaries[].name"
```

Each command should return an empty list, or report that no agent is deployed.

---

<!-- page: 30_conclusion -->
# Conclusion

You have built, deployed, and operated a production-grade AI customer service agent for AnyCompany Telecom with Kiro Specs: you turned your intent into requirements, a design, and a task list, approved each before any code was written, and let steering files and skills enforce the production rules.
What You Accomplished
Throughout this workshop, you progressed from an idea to a fully operational AI agent with enterprise capabilities:

| Lab | Accomplishment |
| Lab 1 | Built a customer service agent using the Strands SDK and deployed it to Amazon Bedrock AgentCore Runtime |
| Lab 2 | Inspected and tuned the memory the template created so the agent remembers across sessions |
| Lab 3 | Connected the agent to backend systems (billing, ticketing, escalation) via MCP Gateway |
| Lab 4 | Scoped every tool call to the authenticated customer to enforce data access boundaries |
| Lab 5 | Routed OpenTelemetry traces to CloudWatch to debug agent behavior and monitor performance |
| Lab 6 | Built and deployed a streaming chat UI to Amazon ECS Fargate |
| Lab 7 | Part 2: shipped an agent for your own use case to AgentCore Runtime, built with Kiro Specs or AI-DLC |

Key Learning Outcomes
 
- Spec-driven development: You turned your intent into requirements, a design, and a task list with Kiro Specs, approved each before any code was written, and let steering files and skills enforce the production rules to generate production-quality agent code 
- Agent lifecycle management: You managed the full agent lifecycle (build, deploy, test, iterate) using the AgentCore CLI 
- Production readiness: You added the capabilities that separate a prototype from production: persistent memory, tool integration, access control, and observability 
- MCP protocol: You connected your agent to external systems using the Model Context Protocol, enabling real actions beyond text generation 
- Infrastructure as Code: The entire workshop environment was provisioned via AWS CDK, demonstrating repeatable and scalable infrastructure patterns 
Next Steps
Here are ways to continue your journey with AI agents on AWS:
Keep Using Kiro the Production Way
 
- Keep a spec per feature in `.kiro/specs/` and review the requirements and tasks before any code is written ([Kiro Specs](https://kiro.dev/docs/specs/)) 
- Promote the workshop steering files into your team's repositories and add your own rules 
- Add hooks for tests, linting, and security checks so they run on every save ([Kiro Hooks](https://kiro.dev/docs/hooks/)) 
Explore More AgentCore Features
 
- Multi-agent orchestration: Build agents that collaborate and delegate tasks to each other 
- Custom tool development: Create your own MCP servers for domain-specific integrations 
- Advanced memory strategies: Experiment with different memory configurations for optimal recall 
Production Deployment Considerations
 
- CI/CD pipelines: Automate agent deployments with CodePipeline or GitHub Actions 
- Load testing: Validate agent performance under concurrent user sessions 
- Cost optimization: Monitor token usage, optimize prompts, and right-size infrastructure 
- Security hardening: Implement least-privilege IAM policies, enable encryption, and audit agent interactions 
Advanced Patterns
 
- Guardrails: Add content filtering and safety controls to your agent responses 
- A/B testing: Deploy multiple agent versions and compare performance metrics 
- Human-in-the-loop: Build workflows where agents escalate complex decisions to human operators 
- Multi-modal agents: Extend your agent to process images, documents, and structured data 
Additional Resources

| Resource | Link |
| Amazon Bedrock AgentCore Documentation | docs.aws.amazon.com/bedrock/latest/userguide/agentcore.html |
| Strands Agents SDK | github.com/strands-agents/sdk-python |
| Kiro IDE | kiro.dev |
| Model Context Protocol (MCP) | modelcontextprotocol.io |
| AWS CDK Documentation | docs.aws.amazon.com/cdk |
| AWS Workshops | workshops.aws |

Thank You
Thank you for participating in this workshop. The combination of spec-driven development with Kiro IDE (turning your intent into requirements, a design, and a task list you approve before any code is written, with steering files and skills enforcing the production rules), the Strands SDK for agent logic, and Amazon Bedrock AgentCore for production operations is a workflow you can take back to your own projects. We hope this experience inspires you to bring these patterns into your own projects.