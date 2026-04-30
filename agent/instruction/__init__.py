"""Auto-load `system.md` and provide a build_instruction() helper.

Usage:
    from instruction import build_instruction
    instruction = build_instruction()

Substitutes runtime placeholders ({WORKSPACE_DIR}, {user_id},
{PREFERRED_LANGUAGE}) with values from environment variables. Falls
back to a generic placeholder if `system.md` is missing.
"""
import os
from pathlib import Path

_SYSTEM_PATH = Path(__file__).parent / "system.md"

if _SYSTEM_PATH.exists():
    instruction_content = _SYSTEM_PATH.read_text(encoding="utf-8")
else:
    instruction_content = "You are a helpful AI assistant."


def build_instruction() -> str:
    """Substitute runtime placeholders in the instruction template."""
    workspace_dir = os.getenv("WORKSPACE_DIR", "/app/data/costaff-agent-database")
    preferred_lang = os.getenv("COSTAFF_PREFERRED_LANGUAGE", "English")
    return (
        instruction_content
        .replace("{WORKSPACE_DIR}", workspace_dir)
        .replace("{user_id}", "shared")
        .replace("{PREFERRED_LANGUAGE}", preferred_lang)
    )
