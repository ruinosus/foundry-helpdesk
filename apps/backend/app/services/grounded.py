"""Grounded structured-citations bridge — Responses API (as the user, OBO) + Foundry IQ MCP tool.

Replaces the AzureAISearchContextProvider path for the grounded domains (cockpit, selfwiki) with a
direct Responses call that attaches the KB as an inline `knowledge_base_retrieve` MCP tool, so the
answer carries STRUCTURED `url_citation` annotations (not prose). It runs the call **as the signed-in
user** (OBO for `https://ai.azure.com/.default` → no service-principal 403), streams the Responses
events, and re-emits them as AG-UI SSE (text deltas + a `sources` CUSTOM event) for the same
CopilotChat the hosted twins use.

Verified live in STEP 0 (docs/superpowers/plans/2026-07-01-grounded-obo-citations-STEP0-findings.md):
  • A1 inline — NO project connection; the MCP server's primary auth is the tool `authorization`
    field (a search-scoped bearer, `https://search.azure.com/.default` = Search Index Data Reader).
  • `model` is REQUIRED on the inline Responses path (no agent to bind it).
  • citations arrive as `response.output_text.annotation.added` events whose `.annotation` is
    `{type:"url_citation", title, url, start_index, end_index}` (real blob URLs; `mcp://…` synthesis
    pseudo-cites are dropped). Text arrives as `response.output_text.delta`.
  • per-user document ACL (cockpit) = the `x-ms-query-source-authorization` header (conditional on
    domain.acl); selfwiki is single-audience → no header. ACL trimming on our service version is
    tracked as unverified (see the STEP 0 findings); attaching the header is harmless when inert.
"""

from __future__ import annotations

import inspect
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from app.core.settings import settings
from app.core.tenant import tenant_config

_SEARCH_SCOPE = "https://search.azure.com/.default"
_KB_API = "2026-05-01-preview"

# Appended to every grounded domain's instructions. STEP 0 confirmed the KB MCP tool emits structured
# url_citation annotations when the model is told to cite in this exact marker format (Microsoft's
# format from the Foundry IQ docs). Without it the answer grounds but may not annotate.
CITATION_DIRECTIVE = (
    "Use SEMPRE a ferramenta da base de conhecimento para responder e cite as fontes. "
    "Toda afirmação fundamentada deve trazer anotações da ferramenta, renderizadas exatamente como "
    "【message_idx:search_idx†source_name】. Se a resposta não estiver na base, diga que não sabe."
)


@dataclass(frozen=True)
class GroundedDomain:
    """Per-domain config for the grounded citations bridge (spec §3 domain_cfg)."""

    kb_name: str
    instructions: str
    acl: bool  # True → attach x-ms-query-source-authorization (cockpit); False → omit (selfwiki)
    search_endpoint: str


def _server_url(domain: GroundedDomain) -> str:
    return f"{domain.search_endpoint.rstrip('/')}/knowledgebases/{domain.kb_name}/mcp?api-version={_KB_API}"


def build_responses_kwargs(
    user_text: str, domain: GroundedDomain, *, model: str, search_token: str
) -> dict:
    """The exact `responses.create(**kwargs)` payload (pure — no I/O, keeps the test infra-free).

    The MCP tool's `authorization` is the primary auth to the Search KB endpoint; the ACL header is
    added only for ACL domains. Both use the caller's search-scoped token in this slice."""
    tool: dict = {
        "type": "mcp",
        "server_label": "knowledge-base",
        "server_url": _server_url(domain),
        "allowed_tools": ["knowledge_base_retrieve"],
        "require_approval": "never",
        "authorization": search_token,
    }
    if domain.acl:
        tool["headers"] = {"x-ms-query-source-authorization": search_token}
    return {
        "model": model,
        "input": user_text,
        "instructions": f"{domain.instructions}\n\n{CITATION_DIRECTIVE}",
        "tools": [tool],
        "stream": True,
    }


def _source_from_annotation(ann: object) -> dict | None:
    """`url_citation` annotation → {source, url}, or None for synthesis pseudo-cites / non-URL."""
    if ann is None:
        return None
    d = ann if isinstance(ann, dict) else (
        ann.model_dump() if hasattr(ann, "model_dump") else getattr(ann, "__dict__", {})
    )
    url = (d.get("url") or "").strip()
    if not url or url.startswith("mcp://"):
        return None
    return {"source": url.rsplit("/", 1)[-1], "url": url}


def _async_credential():
    """Async credential AS THE SIGNED-IN USER (OBO), mirroring app.core.auth.credential_for_request.
    Falls back to DefaultAzureCredential (aio) when auth is off (local dev)."""
    from azure.identity.aio import DefaultAzureCredential, OnBehalfOfCredential

    from app.core.auth import current_user

    user = current_user()
    if settings.auth_enabled and user is not None:
        return OnBehalfOfCredential(
            tenant_id=settings.entra_tenant_id,
            client_id=settings.entra_api_client_id,
            client_secret=settings.entra_api_client_secret,
            user_assertion=user.access_token,
        )
    return DefaultAzureCredential()


async def stream_grounded_agui(body: dict, domain: GroundedDomain) -> AsyncGenerator[str]:
    """Stream a grounded Responses answer (as the user) as AG-UI SSE: text deltas + a `sources`
    CUSTOM event carrying the structured citations. Mirrors hosted.stream_agui's framing."""
    from ag_ui.core import (
        CustomEvent,
        RunErrorEvent,
        RunFinishedEvent,
        RunStartedEvent,
        TextMessageContentEvent,
        TextMessageEndEvent,
        TextMessageStartEvent,
    )
    from ag_ui.encoder import EventEncoder
    from azure.ai.projects.aio import AIProjectClient

    from app.services.hosted import _last_user_text

    user_text = _last_user_text(body.get("messages") or [])
    thread_id = body.get("threadId") or body.get("thread_id") or uuid.uuid4().hex
    run_id = body.get("runId") or body.get("run_id") or uuid.uuid4().hex

    enc = EventEncoder()
    yield enc.encode(RunStartedEvent(thread_id=thread_id, run_id=run_id))
    message_id = uuid.uuid4().hex
    yield enc.encode(TextMessageStartEvent(message_id=message_id, role="assistant"))

    cfg = tenant_config()
    credential = _async_credential()
    proj = AIProjectClient(
        endpoint=cfg.foundry_project_endpoint, credential=credential, allow_preview=True
    )
    sources: list[dict] = []
    seen: set[str] = set()
    try:
        search_token = (await credential.get_token(_SEARCH_SCOPE)).token
        client = proj.get_openai_client()
        client = await client if inspect.isawaitable(client) else client
        kwargs = build_responses_kwargs(
            user_text, domain, model=cfg.foundry_model, search_token=search_token
        )
        stream = await client.responses.create(**kwargs)
        async for ev in stream:
            etype = getattr(ev, "type", "")
            if etype == "response.output_text.delta":
                delta = getattr(ev, "delta", "") or ""
                if delta:
                    yield enc.encode(TextMessageContentEvent(message_id=message_id, delta=delta))
            elif etype == "response.output_text.annotation.added":
                s = _source_from_annotation(getattr(ev, "annotation", None))
                if s and s["url"] not in seen:
                    seen.add(s["url"])
                    sources.append({"index": len(sources) + 1, **s})
        yield enc.encode(TextMessageEndEvent(message_id=message_id))
        if sources:
            yield enc.encode(CustomEvent(name="sources", value=sources))
        yield enc.encode(RunFinishedEvent(thread_id=thread_id, run_id=run_id))
    except Exception as exc:  # surface to the UI as a clean run error (mirrors hosted.stream_agui)
        yield enc.encode(TextMessageEndEvent(message_id=message_id))
        yield enc.encode(RunErrorEvent(message=str(exc), code=type(exc).__name__))
    finally:
        import contextlib

        for obj in (proj, credential):
            with contextlib.suppress(Exception):
                await obj.close()
