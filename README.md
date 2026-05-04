# CoStaff Database Agent

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-latest-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![costaff.agent.json](https://img.shields.io/badge/costaff-compatible-blue.svg)](https://github.com/costaff-ai/costaff)

[繁體中文](./README_zhtw.md) | **English**

**CoStaff Database Agent** is a background specialist agent built on **Google ADK** and the **A2A protocol**. It connects to multiple databases simultaneously, auto-discovers schemas, executes SQL queries, and saves results to the shared workspace for downstream agents (such as the Business Analysis Agent or Coding Agent) to consume.

> *"I query your databases and hand the data to whoever needs it."*

---

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Database Configuration](#database-configuration)
- [MCP Tools](#mcp-tools)
- [MCP Extensions](#mcp-extensions)
- [costaff.agent.json](#costaffagentjson)
- [License](#license)

---

## How It Works

```
CoStaff Agent
     │
     │  A2A Protocol (/.well-known/agent-card.json)
     ▼
Database Agent  ──►  MCP Database Server  ──►  Your Databases (PostgreSQL, MySQL, SQLite…)
                              │
                              └──►  /app/data/workspace/  (CSV / JSON output)
```

The agent follows a one-shot execution model:

1. **Receive** — CoStaff Agent delegates a data extraction or query task
2. **Discover** — inspect available databases and their schemas automatically
3. **Query** — execute SQL and retrieve results
4. **Save** — write output to the shared workspace as CSV or JSON for other agents
5. **Report** — return a summary to the calling agent

---

## Features

- **Multi-database support** — connect to PostgreSQL, MySQL, SQLite, and any SQLAlchemy-compatible database simultaneously
- **Schema auto-discovery** — lists tables, columns, and types without manual configuration
- **SQL execution** — run arbitrary SELECT queries and export results
- **Shared workspace output** — saves results as descriptively named CSV/JSON files accessible by all agents
- **A2A-compatible** — exposes `/.well-known/agent-card.json` health endpoint at port 8081
- **Dynamic MCP support** — additional MCP servers can be assigned at runtime from the CoStaff dashboard
- **Multi-model support** — works with Google Gemini natively or any LiteLLM-compatible provider

---

## Architecture

```
costaff-agent-database/
├── agent/
│   ├── agent.py                           # LlmAgent with dynamic MCP loading
│   ├── agent_a2a.py                       # A2A server entry point
│   └── utils/
│       └── instructions/
│           └── agent_instruction.md       # Agent system prompt
├── mcp/
│   ├── server.py                          # FastMCP server
│   └── tools/
│       └── db_operations.py              # Database tools (query, inspect, list)
├── docker-compose.yaml
└── costaff.agent.json
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Google Gemini API Key **or** LiteLLM-compatible provider
- At least one database connection URL

### Standalone

```bash
git clone https://github.com/costaff-ai/costaff-agent-database.git
cd costaff-agent-database

# Configure environment
cat > .env <<EOF
GOOGLE_API_KEY=your_key_here
DATABASE_CONFIG={"prod_db": {"type": "postgresql", "url": "postgresql://user:pass@host/dbname", "desc": "Production database"}}
EOF

docker compose up -d --build
```

The agent will be available at `http://localhost:8081`.

### Via CoStaff Platform

```bash
cst agent deploy --local /path/to/costaff-agent-database
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API key |
| `DATABASE_CONFIG` | ✅ | — | JSON object defining database connections (see below) |
| `DATABASE_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Model name for Gemini provider |
| `COSTAFF_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` or `litellm` |
| `LITELLM_MODEL_NAME` | ❌ | — | Model name for LiteLLM provider |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API key |
| `DATABASE_WORKSPACE_DIR` | ❌ | `/app/data/workspace` | Output directory for query results |
| `DATABASE_AGENT_MCP_URLS` | ❌ | — | JSON dict of extra MCP servers |
| `COSTAFF_PREFERRED_LANGUAGE` | ❌ | — | Language for agent responses |

---

## Database Configuration

`DATABASE_CONFIG` is a JSON object where each key is a logical alias for the database:

```json
{
  "analytics": {
    "type": "postgresql",
    "url": "postgresql://user:password@host:5432/analytics_db",
    "desc": "Analytics data warehouse"
  },
  "app_db": {
    "type": "mysql",
    "url": "mysql+pymysql://user:password@host:3306/app",
    "desc": "Main application database"
  },
  "local": {
    "type": "sqlite",
    "url": "sqlite:////app/data/local.db",
    "desc": "Local SQLite database"
  }
}
```

Any [SQLAlchemy-supported dialect](https://docs.sqlalchemy.org/en/20/dialects/) can be used.

---

## MCP Tools

| Tool | Description |
|---|---|
| `get_connected_databases()` | List all configured database aliases and their descriptions |
| `inspect_database(db_alias)` | List all tables in the specified database |
| `inspect_table(db_alias, table_name)` | Get schema (columns + types) and sample rows from a table |
| `query(db_alias, sql, output_filename)` | Execute a SQL SELECT query and optionally save results to workspace |

---

## MCP Extensions

Additional MCPs can be assigned dynamically from the **CoStaff dashboard** under `Agents → costaff-agent-database → MCP Extensions → Apply & Restart`.

```json
{
  "my-extra-mcp": {
    "url": "https://my-mcp-server.internal/mcp",
    "headers": { "Authorization": "Bearer ..." }
  }
}
```

---

## costaff.agent.json

```json
{
  "name": "costaff-agent-database",
  "version": "0.1.0",
  "description": "資料庫管理專家，支援多種資料庫連線、自動探索 Schema 並執行跨庫查詢與分析。",
  "a2a_service": "agent-database",
  "port": 8081,
  "env_required": ["GOOGLE_API_KEY", "DATABASE_CONFIG"],
  "mcp_configurable": true,
  "mcp_env_var": "DATABASE_AGENT_MCP_URLS"
}
```

---

## License

Distributed under the Apache 2.0 License. See `LICENSE` for details.
