import os
import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# TODO: Update the import to match your agent variable name in agent.py
from agent import database_agent

PORT = int(os.getenv("PORT", "8081"))
# In CoStaff, this should match the a2a_service name in costaff.agent.json
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "costaff-agent-database")

app = to_a2a(database_agent, host=PUBLIC_HOST, port=PORT, protocol="http")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
