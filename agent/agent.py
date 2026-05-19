import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from google.adk.agents import LlmAgent

from instruction import build_instruction
from mcp_toolsets import load_all_mcp_toolsets
from models import selected_model
from skills import load_all_skills
from tools import load_costaff_api_tools
from sub_agents import load_all_sub_agents
from progress import (
    before_model_callback,
    before_tool_callback,
    after_tool_callback,
)

# Tools = MCP toolsets + Skill toolset
tools = list(load_all_mcp_toolsets())
tools.extend(load_costaff_api_tools())
tools.append(load_all_skills())

# Sub-agents (file-based discovery from sub_agents/ folder)
sub_agents = load_all_sub_agents()

# Instruction (placeholders resolved here)
instruction = build_instruction()

database_agent = LlmAgent(
    name="database_agent",
    model=selected_model,
    description="A database management specialist that can query multiple databases and automate data extraction.",
    instruction=instruction,
    # Code-driven live panel (same canonical progress.py as every agent).
    before_model_callback=before_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    tools=tools,
    sub_agents=sub_agents,
    # A2A leaf default: A2A response auto-returns control to the manager.
    # Disabling parent/peer transfer drops ADK to SingleFlow when
    # `sub_agents` is empty, omitting the transfer-to-agent system prompt
    # so Gemini cannot hallucinate `transfer_to_agent` and crash the run.
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
