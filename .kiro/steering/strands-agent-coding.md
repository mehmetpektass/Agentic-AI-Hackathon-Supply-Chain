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
