import os
import sys
import json
import importlib
import pkgutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from utils.instructions import AGENT_INSTRUCTION

# Workspace for DB results
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/app/data/costaff-agent-database")

# Connect to own MCP
MCP_DATABASE_URL = os.getenv("MCP_DATABASE_URL", "http://costaff-mcp-database:8082/mcp")
tools = [McpToolset(connection_params=StreamableHTTPServerParams(url=MCP_DATABASE_URL))]
logger.info(f"Database MCP URL: {MCP_DATABASE_URL}")

# Additional MCPs (configured via Dashboard)
raw_extra = os.getenv("DATABASE_AGENT_MCP_URLS", "")
if raw_extra:
    try:
        extra_config = json.loads(raw_extra)
        for mcp_name, entry in extra_config.items():
            if isinstance(entry, dict) and not entry.get("enabled", True):
                continue
            try:
                url = entry if isinstance(entry, str) else entry.get("url")
                headers = None if isinstance(entry, str) else entry.get("headers")
                tools.append(McpToolset(connection_params=StreamableHTTPServerParams(url=url, headers=headers or {})))
                logger.info(f"Added extra MCP: {mcp_name}")
            except Exception as e:
                logger.error(f"Failed to load extra MCP '{mcp_name}': {e}")
    except json.JSONDecodeError:
        logger.error("DATABASE_AGENT_MCP_URLS is not valid JSON")

model_provider = os.getenv("COSTAFF_AGENT_MODEL_PROVIDER", "gemini").lower()
model_name = os.getenv("DATABASE_AGENT_MODEL", "gemini-2.5-flash")

if model_provider == "litellm":
    from google.adk.models.lite_llm import LiteLlm
    selected_model = LiteLlm(
        model=os.getenv("LITELLM_MODEL_NAME"),
        api_base=os.getenv("LITELLM_API_BASE"),
        api_key=os.getenv("LITELLM_API_KEY"),
    )
else:
    selected_model = model_name

preferred_lang = os.getenv("COSTAFF_PREFERRED_LANGUAGE", "Traditional Chinese (繁體中文)")
instruction = (
    AGENT_INSTRUCTION
    .replace("{WORKSPACE_DIR}", WORKSPACE_DIR)
    .replace("{user_id}", "shared")
    .replace("{PREFERRED_LANGUAGE}", preferred_lang)
)

def _load_sub_agents():
    sub_agents = []
    pkg_dir = Path(__file__).parent / "sub_agents"
    if pkg_dir.exists():
        for _, module_name, _ in pkgutil.iter_modules([str(pkg_dir)]):
            full_name = f"sub_agents.{module_name}"
            try:
                module = importlib.import_module(full_name)
                if hasattr(module, "agent"):
                    sub_agents.append(module.agent)
            except Exception as e:
                logger.error(f"Failed to load sub-agent '{full_name}': {e}")
    return sub_agents

sub_agents = _load_sub_agents()

database_agent = LlmAgent(
    name="database_agent",
    model=selected_model,
    description="A database management specialist that can query multiple databases and automate data extraction.",
    instruction=instruction,
    tools=tools,
    sub_agents=sub_agents,
)
