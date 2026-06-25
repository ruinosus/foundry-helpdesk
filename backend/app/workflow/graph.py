"""The helpdesk workflow: triage -> retrieve -> resolve.

A WorkflowBuilder chain of the three agents, exposed over AG-UI as a
workflow-as-agent. The AG-UI adapter emits StepStarted/StepFinished per executor
so the frontend can render the steps as they run (the Phase 2 green signal).

- start_executor=triage: the chain entry point.
- intermediate_output_from=[triage, retrieve]: surface their outputs as
  intermediate workflow events (the steps), not just the final answer.
- output_from=[resolve]: the final chat answer comes from resolve only.

Phase 4 will add a conditional escalate edge (HITL + create_ticket); Phase 2 is
the linear chain.

WorkflowBuilder API verified against agent-framework 1.9.0.
"""

from agent_framework import Workflow, WorkflowBuilder
from azure.identity import DefaultAzureCredential

from app.workflow.agents import (
    build_resolve_agent,
    build_retrieve_agent,
    build_triage_agent,
)


def build_helpdesk_workflow() -> Workflow:
    credential = DefaultAzureCredential()
    triage = build_triage_agent(credential)
    retrieve = build_retrieve_agent(credential)
    resolve = build_resolve_agent(credential)

    return (
        WorkflowBuilder(
            name="HelpdeskConcierge",
            description="Triage -> retrieve -> resolve helpdesk workflow.",
            start_executor=triage,
            intermediate_output_from=[triage, retrieve],
            output_from=[resolve],
        )
        .add_chain([triage, retrieve, resolve])
        .build()
    )
