# Foundry Helpdesk

Internal engineering support concierge — a Microsoft Foundry showcase exercising
workflow, knowledge base, memory, and eval, with a CopilotKit frontend over the
**AG-UI** protocol. See [`foundry-helpdesk-spec.md`](./foundry-helpdesk-spec.md)
for the full build spec and [`CLAUDE.md`](./CLAUDE.md) for the working rules.

## Status — Phase 0 (skeleton + hello-world over AG-UI)

Code-complete and wired to the **real** Foundry model (`gpt-4.1-mini`) via Agent
Framework, exposed over AG-UI, with CopilotKit connecting. The end-to-end
round-trip (the Phase 0 🟢 signal) is **pending Azure provisioning** — `azd` is
not installed here and no subscription is wired up yet.

What works without Azure: the Next.js app builds and the chat UI renders; the
backend wiring is verified (the FastAPI app constructs and registers `/helpdesk`
+ `/healthz` with no network call). What needs Azure: `FOUNDRY_PROJECT_ENDPOINT`
must be set for the backend to boot, and a provisioned model for an actual reply.
The server fails fast with a clear error if the endpoint is unset.

## Layout

```
backend/    FastAPI + Agent Framework, AG-UI endpoint at /helpdesk
frontend/   Next.js 15 (App Router) + CopilotKit chat
infra/      Bicep skeleton (azd) — NOT yet deployable, see TODOs
azure.yaml  azd config skeleton
```

## Run locally

### 1. Provision Foundry (required for live replies)

```bash
# azd is not installed in the dev box used for Phase 0 — install it first:
#   https://aka.ms/install-azd
azd auth login
azd up        # provisions Foundry project + gpt-4.1-mini deployment
```

> ⚠️ `infra/main.bicep` and `azure.yaml` are **skeletons** with `TODO: verify`
> markers. Confirm the Foundry resource schema against the Foundry samples repo
> before running `azd up`. See [`CLAUDE.md`](./CLAUDE.md) rule #1.

### 2. Backend

```bash
cd backend
cp .env.example .env          # fill FOUNDRY_PROJECT_ENDPOINT from azd output
uv run uvicorn app.server:app --port 8000 --reload
```

Auth is always `DefaultAzureCredential` — `az login` / `azd auth login`, no keys.

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev                   # http://localhost:3000
```

Open http://localhost:3000 and send a message — it round-trips
CopilotKit → `/api/copilotkit` → AG-UI (`:8000/helpdesk`) → Foundry.

## Phase 0 acceptance

- 🟢 message round-trips with streaming visible in the CopilotKit chat.
- 🔴 CORS blocking, or `DefaultAzureCredential` failing locally.

Next: Phase 1 (Foundry IQ knowledge base). See the spec's phase plan.
