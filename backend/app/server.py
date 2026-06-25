"""FastAPI server exposing the helpdesk agent over the AG-UI protocol.

Phase 0: a single hello-world agent. Later phases swap build_hello_agent() for
the workflow-as-agent (triage -> retrieve -> resolve -> escalate).

CORS note: add_agent_framework_fastapi_endpoint accepts an allow_origins kwarg,
but its docstring marks it "not yet implemented" (verified in
agent-framework-ag-ui 1.0.0rc5), so we apply CORSMiddleware ourselves.
"""

import uvicorn
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.concierge import build_concierge_agent
from app.settings import settings

app = FastAPI(title="Foundry Helpdesk", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# Expose the agent as an AG-UI endpoint the CopilotKit HttpAgent connects to.
add_agent_framework_fastapi_endpoint(app, agent=build_concierge_agent(), path="/helpdesk")


if __name__ == "__main__":
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)
