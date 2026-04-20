import os
import sys
import inspect
import importlib
import pkgutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-database")

sys.path.insert(0, str(Path(__file__).parent))

WORKSPACE = os.getenv("DATABASE_WORKSPACE_DIR", "/app/data/workspace")
os.makedirs(WORKSPACE, exist_ok=True)

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Database", host="0.0.0.0", port=int(os.getenv("MCP_DATABASE_PORT", "8082")))

def _register_tools(mcp_instance):
    tools_pkg_dir = Path(__file__).parent / "tools"
    for finder, module_name, _ in pkgutil.iter_modules([str(tools_pkg_dir)]):
        full_name = f"tools.{module_name}"
        try:
            module = importlib.import_module(full_name)
        except Exception as e:
            logger.error(f"Failed to import tool module '{full_name}': {e}")
            continue

        registered = 0
        for name, fn in inspect.getmembers(module, inspect.isfunction):
            if fn.__module__ != full_name:
                continue
            if name.startswith("_"):
                continue
            mcp_instance.tool()(fn)
            registered += 1

        logger.info(f"Registered {registered} tool(s) from tools/{module_name}.py")


_register_tools(mcp)


if __name__ == "__main__":
    logger.info(f"Starting Database MCP server (transport=streamable-http, workspace={WORKSPACE})")
    mcp.run(transport="streamable-http")
