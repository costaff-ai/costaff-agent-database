"""Model selector: pick the LLM to use based on COSTAFF_AGENT_MODEL_PROVIDER.

If provider == "litellm":
    use the LiteLlm instance from litellm_model.py
otherwise:
    use the Gemini model name from gemini_model.py (DATABASE_AGENT_MODEL,
    default gemini-2.5-flash)
"""
import os

from .gemini_model import gemini_model

_provider = (os.getenv("COSTAFF_AGENT_MODEL_PROVIDER") or "gemini").lower()

if _provider == "litellm":
    from .litellm_model import litellm_model
    selected_model = litellm_model
else:
    selected_model = gemini_model
