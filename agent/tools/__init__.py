"""Native function tools for the Database agent.

Only the 4 shared manager-core tools live here — they reach the
costaff-core HTTP shim via httpx (no MCP client, keeps the agent off a
2nd MCP session = the single-session invariant that makes streamable-http
race-free; keeps DB/notifiers/tokens centralised in costaff-mcp). The
agent's OWN tools are served by its MCP server and reached via the
single McpToolset (see agent/mcp_toolsets/).
"""
from .costaff_api import load_costaff_api_tools

__all__ = ["load_costaff_api_tools"]
