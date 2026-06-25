# Foundry Helpdesk

Internal engineering support concierge — a Microsoft Foundry showcase exercising
workflow, knowledge base, memory, and eval, with a CopilotKit frontend over the
**AG-UI** protocol. See [`foundry-helpdesk-spec.md`](./foundry-helpdesk-spec.md)
for the full build spec and [`CLAUDE.md`](./CLAUDE.md) for the working rules.

## Status — Phase 0 (skeleton + hello-world over AG-UI)

Code-complete and wired to the **real** Foundry model (`gpt-4.1-mini`) via Agent
Framework, exposed over AG-UI, with CopilotKit connecting. Infrastructure is a
real `azd` Bicep template (Foundry account + project + model + RBAC). The
end-to-end round-trip (the Phase 0 🟢 signal) is reached after `azd up` +
wiring the endpoint into the backend env (step 1 below).

What works without Azure: the Next.js app builds and the chat UI renders; the
backend wiring is verified (the FastAPI app constructs and registers `/helpdesk`
+ `/healthz` with no network call). What needs Azure: `FOUNDRY_PROJECT_ENDPOINT`
must be set for the backend to boot, and a provisioned model for an actual reply.
The server fails fast with a clear error if the endpoint is unset.

## Layout

```
backend/    FastAPI + Agent Framework, AG-UI endpoint at /helpdesk
frontend/   Next.js 15 (App Router) + CopilotKit chat
infra/      Bicep (azd): Foundry account + project + gpt-4.1-mini + RBAC
azure.yaml  azd config (provision-only — no services yet)
```

## Run locally

### 1. Provision Foundry with azd (required for live replies)

```bash
azd auth login
azd up        # prompts for env name + location; provisions everything in infra/
```

`azd up` creates a resource group `rg-<env>`, a Foundry account
`aif-helpdesk-<token>`, the project **`helpdesk-concierge`**, a `gpt-4.1-mini`
deployment, and grants your user the **Azure AI User** data-plane role (without
it, inference returns 401). Pick a region where `gpt-4.1-mini` GlobalStandard is
available (e.g. `eastus2`). Lower `modelCapacity` in `infra/resources.bicep` if
you hit a quota error.

After it finishes, read the outputs into the backend env:

```bash
azd env get-values | grep FOUNDRY_   # FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL
```

> The Bicep schema is verified against the official Foundry sample
> (`microsoft-foundry/foundry-samples` `00-basic`), but it has **not** been
> compile-checked locally (no bicep CLI in the dev box). If `azd up` surfaces a
> Bicep error, that's the place to look first.
>
> **Endpoint form:** `FOUNDRY_PROJECT_ENDPOINT` is emitted as
> `https://<account>.services.ai.azure.com/api/projects/<project>`. If
> `FoundryChatClient` rejects it at runtime, try the account-only endpoint from
> the `AZURE_AI_ACCOUNT_ENDPOINT` output instead.

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
