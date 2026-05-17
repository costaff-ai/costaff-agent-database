"""MCP toolset loader for the Database agent — SINGLE own McpToolset.

The agent connects to its OWN MCP server (costaff-mcp-database:8082) via exactly
ONE McpToolset. The 4 shared manager-core tools (send_message_now /
add_task_comment / move_to_shared / list_data_files) are NOT loaded
here — they go via the costaff-core httpx shim (agent/tools/
costaff_api.py).

WHY single session: the anyio MCP cancel-scope race
(google/adk-python#4454) is driven by the NUMBER OF CONCURRENT MCP
sessions per agent process, not the transport. Exactly ONE McpToolset
+ shared-tools-via-shim is race-free under to_a2a() even on
streamable-http (verified 2026-05-17). The old extra-MCP loop
(MCP_DATABASE_URL-style multi-server loading) is intentionally removed: every
extra entry was a 2nd+ concurrent session and the direct cause of the
race. Do NOT reintroduce it.

Transport: MCP_TRANSPORT (default streamable-http; set sse as the
fallback if a high-concurrency edge ever leaks).
"""
import logging
import os
import re
from typing import List

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    SseConnectionParams,
    StreamableHTTPServerParams,
)

logger = logging.getLogger(__name__)

DEFAULT_MCP_URL = "http://costaff-mcp-database:8082/mcp"


def _server_params(url, headers=None):
    """ServerParams with transport chosen by MCP_TRANSPORT (default streamable-http)."""
    t = os.getenv("MCP_TRANSPORT", "streamable-http").strip().lower()
    base = re.sub(r"/(mcp|sse)/?$", "", (url or "").rstrip("/"))
    if t == "streamable-http":
        return StreamableHTTPServerParams(url=base + "/mcp", headers=headers or {})
    return SseConnectionParams(url=base + "/sse", headers=headers or {})


def load_all_mcp_toolsets() -> List[McpToolset]:
    """Return [own-MCP McpToolset] — exactly one session, no extra loop."""
    own_url = os.getenv("MCP_DATABASE_URL", DEFAULT_MCP_URL)
    params = _server_params(own_url)
    logger.info(
        f"Database MCP (single session): {params.url} "
        f"(transport={os.getenv('MCP_TRANSPORT', 'streamable-http')})"
    )
    return [McpToolset(connection_params=params)]
