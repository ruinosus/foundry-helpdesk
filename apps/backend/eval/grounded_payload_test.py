"""Infra-free: grounded.build_responses_kwargs builds the correct Responses+MCP payload.

Asserts the STEP-0-verified shape (inline MCP tool, `authorization` primary auth, `model` required,
conditional ACL header) WITHOUT touching Azure.

    cd apps/backend && uv run python -m eval.grounded_payload_test
"""

from __future__ import annotations

import sys

from app.services.grounded import CITATION_DIRECTIVE, GroundedDomain, build_responses_kwargs

_EP = "https://srch.search.windows.net"


def main() -> None:
    # Cockpit — ACL domain: header present, authorization present, model set, tool shape correct.
    ck = GroundedDomain(kb_name="cockpit-kb", instructions="INSTR", acl=True, search_endpoint=_EP)
    kw = build_responses_kwargs("q", ck, model="gpt-5-mini", search_token="STOK")
    assert kw["model"] == "gpt-5-mini", kw["model"]
    assert kw["stream"] is True
    assert kw["instructions"].startswith("INSTR")  # domain instructions preserved
    assert CITATION_DIRECTIVE in kw["instructions"]  # + the annotation directive always appended
    tool = kw["tools"][0]
    assert tool["type"] == "mcp", tool
    assert tool["allowed_tools"] == ["knowledge_base_retrieve"], tool
    assert tool["require_approval"] == "never", tool
    assert tool["authorization"] == "STOK", tool
    assert tool["server_url"] == (
        f"{_EP}/knowledgebases/cockpit-kb/mcp?api-version=2026-05-01-preview"
    ), tool["server_url"]
    assert tool["headers"]["x-ms-query-source-authorization"] == "STOK", tool

    # Selfwiki — non-ACL domain: NO x-ms-query-source-authorization header.
    sw = GroundedDomain(kb_name="selfwiki-kb", instructions="Y", acl=False, search_endpoint=_EP)
    sw_tool = build_responses_kwargs("q", sw, model="m", search_token="S")["tools"][0]
    assert "headers" not in sw_tool, sw_tool
    assert sw_tool["authorization"] == "S", sw_tool  # primary auth still present

    print("PASS: grounded payload shape (inline MCP tool, authorization, conditional ACL header)")
    sys.exit(0)


if __name__ == "__main__":
    main()
