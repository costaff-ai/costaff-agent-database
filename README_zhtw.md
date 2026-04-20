# CoStaff Agent Template

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-latest-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![costaff.agent.json](https://img.shields.io/badge/costaff-compatible-blue.svg)](https://github.com/CoStaffAI/costaff)

**English** | [繁體中文](./README_zhtw.md)

**CoStaff Agent Template** 是在 [CoStaff](https://github.com/CoStaffAI/costaff) 平台上建立 external agent 的起始模板。它遵循與官方 first-party agents（`costaff-coding-agent`、`costaff-viz-report-agent`）相同的架構，可以直接用 Docker Compose 或 CoStaff CLI 部署。

---

## 目錄

- [運作原理](#運作原理)
- [專案架構](#專案架構)
- [快速開始](#快速開始)
- [客製化指南](#客製化指南)
- [環境變數](#環境變數)
- [MCP 擴充](#mcp-擴充)
- [costaff.agent.json](#costaffagentjson)
- [授權](#授權)

---

## 運作原理

```
CoStaff Agent
     │
     │  A2A Protocol (/.well-known/agent.json)
     ▼
Template Agent  ──►  MCP Template Server  ──►  你的工具 / 資料 / API
```

1. CoStaff Agent 透過 **A2A 協議** 委派任務
2. Agent 根據 system prompt 推理，並透過 **MCP Server** 呼叫工具
3. 結果儲存在共享 volume，並回傳給呼叫端 agent

---

## 專案架構

```
costaff-agent-template/
├── agent/                        # ADK agent 定義
│   ├── agent.py                  # LlmAgent，含動態 MCP 載入
│   ├── agent_a2a.py              # A2A server 進入點
│   ├── requirements.txt
│   └── utils/
│       └── instructions/
│           └── agent_instruction.md   # System prompt（主要編輯這裡）
├── mcp/                          # MCP server
│   ├── server.py                 # FastMCP server — 在這裡加入你的工具
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yaml           # 獨立部署設定
├── costaff.agent.json           # CoStaff 平台 manifest
└── .gitignore
```

---

## 快速開始

### 前置需求

- Docker 和 Docker Compose
- Google Gemini API Key **或** LiteLLM 相容的 provider

### 獨立部署

```bash
git clone https://github.com/CoStaffAI/costaff-agent-template.git
cd costaff-agent-template

# 設定 API Key
export GOOGLE_API_KEY=your_key_here

# 啟動
docker compose up -d --build
```

Agent 將在 `http://localhost:8081` 提供服務。

### 透過 CoStaff 平台部署

```bash
cst agent deploy --local /path/to/your-agent
```

CoStaff 會讀取 `costaff.agent.json`，自動 build、啟動容器並註冊 agent。

---

## 客製化指南

在整個專案中搜尋所有 `TODO` 註解 — 每一個都標記了需要針對你的 agent 做決定的地方。

### 1. 重新命名識別符

| 搜尋 | 取代為 |
|------|--------|
| `template_agent` | `your_agent_name`（snake_case，Python 檔案） |
| `template-agent` | `your-agent-name`（kebab-case，YAML / JSON） |
| `mcp-template` | `mcp-your-agent`（kebab-case） |
| `TEMPLATE_` | `YOUR_AGENT_`（SCREAMING_SNAKE_CASE，環境變數前綴） |
| `template_data` | `your_agent_data`（Docker volume 名稱） |
| `TODO: 這裡填寫 Agent 的中文顯示名稱` | `您的 Agent 中文稱呼`（用於主 Agent 識別） |

### 2. 撰寫 MCP 工具（`mcp/server.py`）

- 移除或重新命名 `example_*` 工具
- 加入讓 agent 能存取所需資料、API 或能力的工具
- 每個工具都必須有清晰的 docstring — LLM 靠它決定何時呼叫該工具

### 3. 撰寫 system prompt（`agent/utils/instructions/agent_instruction.md`）

- 用你的 agent 的身份、角色和工作流程取代佔位內容
- 在工具使用指南表格中列出實際的工具名稱

### 4. 更新 manifest 檔案

- `costaff.agent.json` — 更新 `name`、`description`、環境變數名稱
- `docker-compose.yaml` — 更新 service 名稱、環境變數、volume 名稱

---

## 環境變數

| 變數 | 必填 | 預設值 | 說明 |
|------|------|--------|------|
| `GOOGLE_API_KEY` | ✅ | — | Google Gemini API key |
| `TEMPLATE_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Gemini provider 的 model 名稱 |
| `COSTAFF_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` 或 `litellm` |
| `LITELLM_MODEL_NAME` | ❌ | — | LiteLLM provider 的 model 名稱 |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API key |
| `MCP_TEMPLATE_URL` | ❌ | `http://mcp-template:8082/sse` | 內部 MCP server URL |
| `TEMPLATE_WORKSPACE_DIR` | ❌ | `/app/data/workspace` | 共享資料目錄 |
| `TEMPLATE_AGENT_MCP_URLS` | ❌ | — | 額外 MCP servers 的 JSON dict |

---

## MCP 擴充

額外的 MCP（資料庫、搜尋 API、內部工具）可以從 **CoStaff dashboard** 的 `Agents → your-agent → MCP Extensions → Apply & Restart` 動態指派，不需要重新部署。

額外 MCP 透過 `TEMPLATE_AGENT_MCP_URLS` 環境變數以 JSON dict 傳入：

```json
{
  "my-db-mcp": {
    "url": "https://my-db-mcp.internal/mcp",
    "transport": "streamable",
    "headers": { "Authorization": "Bearer ..." }
  }
}
```

支援的 transport：`sse`（URL 含 `/sse`）和 `streamable`（預設）。

---

## costaff.agent.json

此 manifest 宣告 agent 的身份和能力給 CoStaff 平台：

```json
{
  "name": "your-agent-name",
  "version": "1.0.0",
  "description": "一句話說明這個 agent 做什麼。",
  "a2a_service": "your-agent-name",
  "port": 8081,
  "env_required": ["GOOGLE_API_KEY"],
  "mcp_configurable": true,
  "mcp_env_var": "YOUR_AGENT_MCP_URLS"
}
```

---

## 授權

以 MIT License 發佈。詳見 `LICENSE`。
