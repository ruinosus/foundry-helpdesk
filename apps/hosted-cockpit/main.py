# Hosted-agent entrypoint — Cockpit expert (Phase C, second domain).
#
# Packages the Cockpit expert as a Foundry *hosted agent*: a container that serves
# the Responses protocol on port 8088, invoked through the Foundry gateway.
# agent-framework-foundry-hosting's ResponsesHostServer is the bridge.
#
# A self-contained, single-identity variant of the live /cockpit agent
# (app/agents/cockpit.py): same Foundry IQ knowledge base (cockpit-kb, agentic
# retrieval) and the same open-standard **grounded-qa** Agent Skill (bundled under
# ./skills), but config comes from env (declared in agent.yaml / injected by the
# platform) and auth is the platform-injected agent identity via
# DefaultAzureCredential. Pure grounded Q&A — no workflow, memory or HITL.
# APIs mirror app/agents/cockpit.py; verified against agent-framework 1.9.0.

import asyncio
import os
from pathlib import Path

from agent_framework import FileSkillsSource, SkillsProvider, agent_middleware
from agent_framework.azure import AzureAISearchContextProvider
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

# Same identity + discipline as the live agent (app/agents/prompts.COCKPIT_INSTRUCTIONS):
# the answering/citation/decline discipline lives in the grounded-qa skill, not here.
COCKPIT_INSTRUCTIONS = (
    "Você é um especialista na plataforma **Cockpit** (Avanade AAP). Responda em "
    "português. Siga o seu skill **grounded-qa**: responda SEMPRE fundamentado nos "
    "documentos recuperados da base de conhecimento do Cockpit, citando o componente e "
    "o documento-fonte."
)

_SKILLS_DIR = Path(__file__).parent / "skills"


# Mirrors app/agents/cockpit.py: strip orphaned skill tool calls from replayed history
# so multi-turn doesn't 400 ("No tool output found for function call"). Match ONLY tool
# content by its `.type` — never the user's `type="text"` message (a broader check would
# drop the user turn and starve agentic retrieval). The agentic retrieval itself runs in
# a context-provider hook and emits no model tool call; the grounded-qa skill's
# load_skill / read_skill_resource calls are the ones that need sanitizing on replay.
def _is_tool_content(content) -> bool:
    return getattr(content, "type", None) in (
        "function_call",
        "function_result",
        "tool_call",
        "tool_result",
    )


@agent_middleware
async def _drop_replayed_tool_messages(context, call_next):
    msgs = context.messages
    if msgs:
        msgs[:] = [
            m
            for m in msgs
            if not any(_is_tool_content(c) for c in (getattr(m, "contents", None) or []))
        ]
    await call_next()


async def main() -> None:
    credential = DefaultAzureCredential()

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=credential,
    )

    # Foundry IQ knowledge base (agentic) — the same cockpit-kb the live app grounds in.
    search = AzureAISearchContextProvider(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        knowledge_base_name=os.environ["AZURE_SEARCH_KNOWLEDGE_BASE"],
        credential=credential,
        mode="agentic",
    )

    # Open Agent Skills standard (SKILL.md) — the grounded-qa retrieval discipline.
    skills = SkillsProvider(FileSkillsSource([str(_SKILLS_DIR)]))

    async with search:
        agent = client.as_agent(
            name="CockpitExpert",
            description="Avanade Cockpit platform expert grounded in the Cockpit knowledge base.",
            instructions=COCKPIT_INSTRUCTIONS,
            context_providers=[search, skills],
            middleware=[_drop_replayed_tool_messages],
            # Foundry hosting manages conversation history; don't double-store.
            default_options={"store": False},
        )

        server = ResponsesHostServer(agent)
        await server.run_async()


if __name__ == "__main__":
    asyncio.run(main())
