"""
Example workspace tools — read, write, and list files.
Replace or remove this file once you add your own tool files.
"""
import os
from pathlib import Path

# Read workspace path at call time so it reflects runtime env vars.
_workspace = lambda: os.getenv("AGENT_DATABASE_WORKSPACE_DIR", "/app/data/agent-database")


def example_read_file(filename: str) -> str:
    """
    Read the content of a file from the workspace.
    Returns the file content as a string, or an [ERROR] message.
    """
    try:
        filepath = Path(_workspace()) / filename
        if not filepath.exists():
            return f"[ERROR]: File '{filename}' not found in workspace."
        return filepath.read_text(encoding="utf-8")
    except Exception as e:
        return f"[ERROR]: {e}"


def example_write_file(filename: str, content: str) -> str:
    """
    Write content to a file in the workspace.
    Use this to persist output or intermediate results.
    """
    try:
        filepath = Path(_workspace()) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        return f"File '{filename}' written successfully ({len(content)} chars)."
    except Exception as e:
        return f"[ERROR]: {e}"


def example_list_workspace() -> str:
    """
    List all files currently in the workspace.
    Call this at the start of every task to understand what already exists.
    """
    try:
        files = sorted(Path(_workspace()).rglob("*"))
        if not files:
            return "(workspace is empty)"
        return "\n".join(
            str(f.relative_to(_workspace())) + ("/" if f.is_dir() else "")
            for f in files
        )
    except Exception as e:
        return f"[ERROR]: {e}"
