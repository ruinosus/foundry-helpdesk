"""Phase 0 hello-world agent.

A single trivial concierge agent backed by the real Foundry model
(gpt-4.1-mini) via the OpenAI Responses API. No knowledge base, memory, or
tools yet — those arrive in later phases. The point of Phase 0 is to prove the
round-trip CopilotKit -> AG-UI -> Agent Framework -> Foundry works end to end.

API verified against agent-framework 1.9.0 / agent-framework-ag-ui 1.0.0rc5:
  FoundryChatClient(project_endpoint=..., model=..., credential=...).as_agent(...)
"""

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

from app.settings import settings

INSTRUCTIONS = (
    "You are the Helpdesk Concierge, an internal engineering support assistant. "
    "For now you only greet the developer and explain that you can help triage "
    "engineering questions. Keep replies short and friendly. "
    "Do not invent runbooks or sources yet — knowledge retrieval is not wired up."
)


def build_hello_agent() -> Agent:
    """Create the Phase 0 concierge agent bound to the Foundry model.

    Auth is always DefaultAzureCredential (never an API key). The credential and
    endpoint are only exercised at request time, so this constructs fine even
    before Azure is provisioned — the round-trip just won't succeed until then.
    """
    client = FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint or None,
        model=settings.foundry_model,
        credential=DefaultAzureCredential(),
    )
    return client.as_agent(
        name="HelpdeskConcierge",
        description="Internal engineering support concierge (Phase 0 hello-world).",
        instructions=INSTRUCTIONS,
    )
