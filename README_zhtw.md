# CoStaff 資料庫 Agent

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-latest-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![costaff.agent.json](https://img.shields.io/badge/costaff-compatible-blue.svg)](https://github.com/costaff-ai/costaff)

**[English](./README.md)** | 繁體中文

**CoStaff 資料庫 Agent** 是基於 **Google ADK** 與 **A2A 協議** 的後台專業子 Agent。它可同時連線多個資料庫，自動探索 Schema、執行 SQL 查詢，並將結果存入共享工作區，供後續 Agent（如 Business Analysis Agent 或 Coding Agent）使用。

> *「我負責查詢你的資料庫，並將資料交給需要的人。」*

---

## 目錄

- [運作方式](#運作方式)
- [功能特色](#功能特色)
- [專案架構](#專案架構)
- [快速開始](#快速開始)
- [環境變數](#環境變數)
- [資料庫設定](#資料庫設定)
- [MCP 工具](#mcp-工具)
- [MCP 擴充](#mcp-擴充)
- [costaff.agent.json](#costaffagentjson)
- [授權](#授權)

---

## 運作方式

```
CoStaff Agent
     │
     │  A2A Protocol (/.well-known/agent.json)
     ▼
資料庫 Agent  ──►  MCP 資料庫伺服器  ──►  您的資料庫（PostgreSQL、MySQL、SQLite…）
                              │
                              └──►  /app/data/workspace/（CSV / JSON 輸出）
```

Agent 採用一次性執行模型：

1. **接收** — CoStaff Agent 委派資料擷取或查詢任務
2. **探索** — 自動檢查可用資料庫及其 Schema
3. **查詢** — 執行 SQL 並取得結果
4. **儲存** — 將輸出寫入共享工作區為 CSV 或 JSON，供其他 Agent 使用
5. **回報** — 向呼叫端 Agent 回傳摘要

---

## 功能特色

- **多資料庫支援** — 同時連線 PostgreSQL、MySQL、SQLite 及任何 SQLAlchemy 相容資料庫
- **Schema 自動探索** — 無需手動設定，自動列出資料表、欄位與型別
- **SQL 執行** — 執行任意 SELECT 查詢並匯出結果
- **共享工作區輸出** — 以具描述性的檔名將結果儲存為 CSV/JSON，所有 Agent 皆可存取
- **A2A 相容** — 在 8081 port 提供 `/.well-known/agent.json` 健康端點
- **動態 MCP 支援** — 可從 CoStaff 後台在執行階段動態新增 MCP 伺服器
- **多模型支援** — 原生支援 Google Gemini，或任何 LiteLLM 相容提供者

---

## 專案架構

```
costaff-agent-database/
├── agent/
│   ├── agent.py                           # 含動態 MCP 載入的 LlmAgent
│   ├── agent_a2a.py                       # A2A 伺服器入口
│   └── utils/
│       └── instructions/
│           └── agent_instruction.md       # Agent 系統提示詞
├── mcp/
│   ├── server.py                          # FastMCP 伺服器
│   └── tools/
│       └── db_operations.py              # 資料庫工具（查詢、檢查、列表）
├── docker-compose.yaml
└── costaff.agent.json
```

---

## 快速開始

### 前置需求

- Docker 與 Docker Compose
- Google Gemini API Key 或 LiteLLM 相容提供者
- 至少一個資料庫連線 URL

### 獨立部署

```bash
git clone https://github.com/costaff-ai/costaff-agent-database.git
cd costaff-agent-database

# 設定環境變數
cat > .env <<EOF
GOOGLE_API_KEY=your_key_here
DATABASE_CONFIG={"prod_db": {"type": "postgresql", "url": "postgresql://user:pass@host/dbname", "desc": "正式資料庫"}}
EOF

docker compose up -d --build
```

Agent 將可於 `http://localhost:8081` 存取。

### 透過 CoStaff 平台部署

```bash
cst agent deploy --local /path/to/costaff-agent-database
```

---

## 環境變數

| 變數名稱 | 必填 | 預設值 | 說明 |
|---|---|---|---|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API 金鑰 |
| `DATABASE_CONFIG` | ✅ | — | 定義資料庫連線的 JSON 物件（見下方） |
| `DATABASE_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Gemini 提供者的模型名稱 |
| `COSTAFF_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` 或 `litellm` |
| `LITELLM_MODEL_NAME` | ❌ | — | LiteLLM 提供者的模型名稱 |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API Base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API 金鑰 |
| `DATABASE_WORKSPACE_DIR` | ❌ | `/app/data/workspace` | 查詢結果輸出目錄 |
| `DATABASE_AGENT_MCP_URLS` | ❌ | — | 額外 MCP 伺服器的 JSON 字典 |
| `COSTAFF_PREFERRED_LANGUAGE` | ❌ | — | Agent 回應語言 |

---

## 資料庫設定

`DATABASE_CONFIG` 是一個 JSON 物件，每個 key 為資料庫的邏輯別名：

```json
{
  "analytics": {
    "type": "postgresql",
    "url": "postgresql://user:password@host:5432/analytics_db",
    "desc": "分析資料倉儲"
  },
  "app_db": {
    "type": "mysql",
    "url": "mysql+pymysql://user:password@host:3306/app",
    "desc": "主應用程式資料庫"
  },
  "local": {
    "type": "sqlite",
    "url": "sqlite:////app/data/local.db",
    "desc": "本地 SQLite 資料庫"
  }
}
```

支援任何 [SQLAlchemy 相容的資料庫方言](https://docs.sqlalchemy.org/en/20/dialects/)。

---

## MCP 工具

| 工具 | 說明 |
|---|---|
| `get_connected_databases()` | 列出所有已設定的資料庫別名與描述 |
| `inspect_database(db_alias)` | 列出指定資料庫的所有資料表 |
| `inspect_table(db_alias, table_name)` | 取得資料表的 Schema（欄位與型別）及樣本資料 |
| `query(db_alias, sql, output_filename)` | 執行 SQL SELECT 查詢，可選擇性地將結果存至工作區 |

---

## MCP 擴充

可從 **CoStaff 後台** 的 `Agents → costaff-agent-database → MCP Extensions → Apply & Restart` 動態新增額外 MCP 伺服器，無需重新部署。

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

## 授權

依 MIT 授權條款發布。詳見 `LICENSE`。
