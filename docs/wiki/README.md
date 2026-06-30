# docs/wiki — the project's own deep-wiki (generated)

This is a **machine-generated deep-wiki of THIS repository** — the `selfwiki` domain (the
"deep-wiki daqui"). It's the assurance mechanism turned on its own source:
[`wiki_builder.py`](../../apps/backend/app/knowledge/wiki_builder.py) read the real code of
each area of the monorepo and wrote a faithful, cited wiki bundle, gated on **build
fidelity** (≥ 80% of file citations must resolve to a real source file — see
[`assurance.yaml`](../../apps/backend/eval/assurance.yaml)).

> **Generated, not curated.** Unlike the rest of `docs/` (hand-written, follows
> [`DOCS-STANDARD.md`](../DOCS-STANDARD.md) — front-matter + Diátaxis types), the bundles
> here are machine-generated in the ingest bundle format and are **exempt from the
> front-matter rule** (the standard says so). Don't hand-edit them — regenerate.

Unlike the **Cockpit** corpus (Avanade-internal docs, read from an external path and never
committed), this corpus is generated from *this public repo*, so it's safe to version here.
It's also the input the selfwiki ingest ships to the cloud knowledge base.

## What's here

One bundle per monorepo area, in the format the ingest consumes
(`manifest.json` + `pages/page-N.md` + `llms.txt`). **Current bundles are `v0.2.0`** — regenerated
to reflect the **multi-tenant SaaS evolution** (sub-projects A→B→C→D: deployment modes, connections +
credential brokering, DomainAssignment, the 4th `platform` domain, the hosted platform agent, and the
Managed App + Lighthouse stamp). `v0.2.0` was produced via the **local Microsoft Agent-Skills path**
(`wiki-architect` + `wiki-page-writer`, run by the coding agent — **no Foundry infra**), so the
manifests read `model: local-agent` (the `wiki_builder.py` Foundry pipeline remains the other path).

| Bundle (`v0.2.0`) | Source area | Pages | Fidelity (cited paths → real file) |
| --- | --- | --- | --- |
| `foundry-helpdesk-backend/`  | `apps/backend`  | 8 | 98% (40/41 — the 1 non-file is an intentional `eval/` dir link) |
| `foundry-helpdesk-frontend/` | `apps/frontend` | 8 | 100% (33/33) |
| `foundry-helpdesk-infra/`    | `infra` (+ `azure.yaml`, `apps/hosted-*`) | 9 | 100% (33/33) |
| `foundry-helpdesk-docs/`     | `docs`          | 8 | 100% (53/53, whole-monorepo denominator)¹ |

> **Two gate bugs this dogfood surfaced** (the mechanism finding faults in itself):
> 1. An extension-alternation regex matched `.js` inside `.json` (`js` sorted before
>    `json`), silently failing every `.json`/`.tsx` citation — unfairly failing the
>    config/frontend-heavy bundles (frontend 37%, infra 50% before the fix). Fixed
>    (longest-extension-first) in `wiki_builder.py`; backend/frontend/infra scores above
>    are post-fix (85–98%).
> 2. ¹ The fidelity check resolved citations only against the bundle's `--repo` gather,
>    but a cross-cutting `docs/` bundle legitimately cites files across `apps/` + `infra/`.
>    Scored against `docs/` alone it read 71%; against the whole monorepo (the fair
>    denominator) it's **85%**. The `--fidelity-root` flag lets a monorepo sub-area
>    resolve citations against the repo root.

## Regenerate

Two paths, both fidelity-gated (≥ 80% of cited paths must resolve to a real file):

**A — Foundry pipeline** (`wiki_builder.py`, uses the Foundry `gpt-5-mini` model → needs `azd up` /
Azure). From `apps/backend/`, one run per area:

```bash
uv run python -m app.knowledge.wiki_builder \
  --repo ../../apps/backend --component foundry-helpdesk-backend --version v0.2.0 \
  --out ../../docs/wiki
# …repeat for ../../apps/frontend, ../../infra, ../../docs
```

**B — Local Agent-Skills path** (the Microsoft `wiki-architect` + `wiki-page-writer` skills in
[`apps/backend/app/knowledge/skills/`](../../apps/backend/app/knowledge/skills/), run by a coding
agent — **VS Code Copilot, GitHub Copilot CLI, or Claude Code — NO Foundry/Azure infra**). Open the
repo in the agent and ask it to *"regenerate the deep-wiki for area X following the wiki-page-writer
skill, with linked citations and the ≥80% build-fidelity gate."* This is how `v0.2.0` was produced.

## Ingest into the selfwiki knowledge base

The ingest reuses [`ingest_cockpit.py`](../../apps/backend/app/knowledge/ingest_cockpit.py)
verbatim — only the env points it at the selfwiki names (the mechanism is domain-generic).
No ACL group map → non-blocking ingest, single-audience (this repo is public):

```bash
KB_KNOWLEDGE_SOURCE=selfwiki-docbundles-ks \
KB_DOMAIN_LABEL="o projeto foundry-helpdesk" \
COCKPIT_STORAGE_CONTAINER=selfwiki-corpus \
COCKPIT_SEARCH_KNOWLEDGE_BASE=selfwiki-kb \
COCKPIT_SEARCH_INDEX=selfwiki-docbundles-ks-index \
COCKPIT_DOCBUNDLES=../../docs/wiki \
  uv run python -m app.knowledge.ingest_cockpit
```

The `/selfwiki` agent ([`selfwiki.py`](../../apps/backend/app/agents/selfwiki.py)) then
answers questions about this project grounded in this wiki.
