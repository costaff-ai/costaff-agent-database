from pathlib import Path

_dir = Path(__file__).parent
AGENT_INSTRUCTION = (_dir / "agent_instruction.md").read_text(encoding="utf-8")
