#!/usr/bin/env bash
# Demo mode — run the UI with NO Azure and NO Python backend. aimock (CopilotKit)
# replays a recorded AG-UI fixture; the real Next.js frontend renders the full flow
# (triage→retrieve→resolve steps, grounded answer, HITL approval). Record the fixture
# first with scripts/demo-record.sh. See docs/DEPLOYMENT.md › Demo mode.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONT="$ROOT/apps/frontend"
PORT_MOCK="${PORT_MOCK:-4010}"

command -v npx >/dev/null || { echo "✖ npx not found — install Node 20+."; exit 1; }
if ! ls "$FRONT"/demo/fixtures/*.json >/dev/null 2>&1; then
  echo "✖ No demo fixture in apps/frontend/demo/fixtures/."
  echo "  Record one first:  ./scripts/demo-record.sh"
  exit 1
fi
[ -d "$FRONT/node_modules" ] || ( cd "$FRONT" && npm install )

echo "▸ aimock (AG-UI replay) on :$PORT_MOCK …"
( cd "$FRONT" && npx -p @copilotkit/aimock llmock -p "$PORT_MOCK" -f demo/fixtures --log-level warn ) &
MOCK_PID=$!
trap 'kill "$MOCK_PID" 2>/dev/null || true' EXIT
sleep 2

echo "▸ Frontend in demo mode → http://localhost:3000  (Ctrl-C to stop both)"
cd "$FRONT"
AGUI_URL="http://localhost:$PORT_MOCK/agui" \
HOSTED_AGUI_URL="http://localhost:$PORT_MOCK/agui" \
NEXT_PUBLIC_DEMO_MODE=1 \
npm run dev
