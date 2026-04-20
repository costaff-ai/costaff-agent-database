import os
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from a2a.types import AgentCard

# TODO: Update the import to match your agent variable name in agent.py
from agent import database_agent

PORT = int(os.getenv("PORT", "8081"))
# In CoStaff, this should match the a2a_service name in costaff.agent.json
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "costaff-agent-database")

# Provide a minimal agent card with only the agent-level description.
# Omitting individual tool skills prevents the parent agent from seeing
# sub-agent tools as directly callable, which would cause 500 errors.
agent_card = AgentCard(
    name=database_agent.name,
    url=f"http://{PUBLIC_HOST}:{PORT}",
    description=database_agent.description,
    version="1.0.0",
    capabilities={
        "display_name": "AI 資料庫管理員"
    },
    skills=[],
    default_input_modes=["text/plain"],
    default_output_modes=["text/plain"],
    supports_authenticated_extended_card=False,
)

app = to_a2a(database_agent, host=PUBLIC_HOST, port=PORT, protocol="http", agent_card=agent_card)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
