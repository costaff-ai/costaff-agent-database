# CoStaff Agent Template

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-latest-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![costaff.agent.json](https://img.shields.io/badge/costaff-compatible-blue.svg)](https://github.com/CoStaffAI/costaff)

[繁體中文](./README_zhtw.md) | **English**

**CoStaff Agent Template** is a starting point for building external agents on the [CoStaff](https://github.com/CoStaffAI/costaff) platform. It follows the same architecture as first-party agents (`costaff-coding-agent`, `costaff-viz-report-agent`) and is ready to deploy with Docker Compose or the CoStaff CLI.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Customisation Guide](#customisation-guide)
- [Environment Variables](#environment-variables)
- [MCP Extensions](#mcp-extensions)
- [costaff.agent.json](#costaffagentjson)
- [License](#license)

---

## How It Works

```
CoStaff Agent
     │
     │  A2A Protocol (/.well-known/agent.json)
     ▼
Template Agent  ──►  MCP Template Server  ──►  Your tools / data / APIs
```

1. The CoStaff Agent delegates tasks via **A2A protocol**
2. The agent reasons using its system prompt and calls tools via the **MCP server**
3. Results are saved to a shared volume and returned to the calling agent

---

## Architecture

```
costaff-agent-template/
├── agent/                        # ADK agent definition
│   ├── agent.py                  # LlmAgent with dynamic MCP loading
│   ├── agent_a2a.py              # A2A server entrypoint
│   ├── requirements.txt
│   └── utils/
│       └── instructions/
│           └── agent_instruction.md   # System prompt (edit this)
├── mcp/                          # MCP server
│   ├── server.py                 # FastMCP server — add your tools here
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yaml           # Standalone deployment
├── costaff.agent.json           # CoStaff platform manifest
└── .gitignore
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Google Gemini API Key **or** LiteLLM-compatible provider

### Standalone

```bash
git clone https://github.com/CoStaffAI/costaff-agent-template.git
cd costaff-agent-template

# Set your API key
export GOOGLE_API_KEY=your_key_here

# Start
docker compose up -d --build
```

The agent will be available at `http://localhost:8081`.

### Via CoStaff Platform

```bash
cst agent deploy --local /path/to/your-agent
```

CoStaff reads `costaff.agent.json`, builds and starts the containers, and registers the agent automatically.

---

## Customisation Guide

Search for all `TODO` comments across the project — each marks a decision point specific to your agent:

### 1. Rename identifiers

| Find | Replace with |
|------|--------------|
| `template_agent` | `your_agent_name` (snake_case, in Python files) |
| `template-agent` | `your-agent-name` (kebab-case, in YAML / JSON) |
| `mcp-template` | `mcp-your-agent` (kebab-case) |
| `TEMPLATE_` | `YOUR_AGENT_` (SCREAMING_SNAKE_CASE, env var prefix) |
| `template_data` | `your_agent_data` (Docker volume name) |

### 2. Write your MCP tools (`mcp/server.py`)

- Remove or rename the `example_*` tools
- Add tools that give the agent access to the data, APIs, or capabilities it needs
- Every tool must have a clear docstring — the LLM reads it to decide when to call the tool

### 3. Write your system prompt (`agent/utils/instructions/agent_instruction.md`)

- Replace the placeholder content with your agent's identity, role, and workflow
- Reference your actual tool names in the Tool Usage Guide table

### 4. Update manifests

- `costaff.agent.json` — update `name`, `description`, env var names
- `docker-compose.yaml` — update service names, env vars, volume name

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API key |
| `TEMPLATE_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Model name for Gemini provider |
| `COSTAFF_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` or `litellm` |
| `LITELLM_MODEL_NAME` | ❌ | — | Model name for LiteLLM provider |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API key |
| `MCP_TEMPLATE_URL` | ❌ | `http://mcp-template:8082/sse` | Internal MCP server URL |
| `TEMPLATE_WORKSPACE_DIR` | ❌ | `/app/data/workspace` | Shared data directory |
| `TEMPLATE_AGENT_MCP_URLS` | ❌ | — | JSON dict of extra MCP servers |

---

## MCP Extensions

Additional MCPs (databases, search APIs, internal tools) can be assigned dynamically from the **CoStaff dashboard** under `Agents → your-agent → MCP Extensions → Apply & Restart` — no redeployment needed.

Extra MCPs are passed via the `TEMPLATE_AGENT_MCP_URLS` environment variable as a JSON dict:

```json
{
  "my-db-mcp": {
    "url": "https://my-db-mcp.internal/mcp",
    "transport": "streamable",
    "headers": { "Authorization": "Bearer ..." }
  }
}
```

Supported transports: `sse` (URL contains `/sse`) and `streamable` (default).

---

## costaff.agent.json

This manifest declares the agent's identity and capabilities to the CoStaff platform:

```json
{
  "name": "your-agent-name",
  "version": "1.0.0",
  "description": "One-sentence description of what this agent does.",
  "a2a_service": "your-agent-name",
  "port": 8081,
  "env_required": ["GOOGLE_API_KEY"],
  "mcp_configurable": true,
  "mcp_env_var": "YOUR_AGENT_MCP_URLS"
}
```

---

## License

Distributed under the MIT License. See `LICENSE` for details.
