#!/usr/bin/env bash
# azd POSTPROVISION hook — runs after infra is created, BEFORE the package/build/deploy phase.
#
# Does the two data-plane/config steps Bicep can't, so `azd up` is one-shot:
#   1) push the local .env (NEXT_PUBLIC_*/ENTRA_*) into the azd env — the web image bakes the
#      sign-in config at BUILD time (Docker buildArgs), so it must be in the azd env before deploy.
#      Harmless/idempotent when auth isn't set up (nothing to push).
#   2) bootstrap the data plane (ingest the helpdesk KB + provision memory) — ONLY when
#      AUTO_BOOTSTRAP=true in the azd env (scripts/up-all.sh sets it). Gated so a plain `azd up`
#      for a code change doesn't re-ingest the KB (which polls for minutes).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "▸ postprovision: pushing local env into the azd environment (for the web build)"
if [ -x "$ROOT/scripts/set-deploy-env.sh" ]; then
  "$ROOT/scripts/set-deploy-env.sh" || echo "  (set-deploy-env: nothing to push)"
fi

AUTO_BOOTSTRAP="$(azd env get-value AUTO_BOOTSTRAP 2>/dev/null || echo '')"
if [ "$AUTO_BOOTSTRAP" = "true" ]; then
  echo "▸ postprovision: bootstrapping the data plane (helpdesk KB + memory)"
  "$ROOT/scripts/bootstrap.sh"
else
  echo "  (AUTO_BOOTSTRAP not set — skipping KB ingest; run ./scripts/bootstrap.sh to do it)"
fi
