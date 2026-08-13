#!/usr/bin/env bash
# Start local API, web, and mock services for development.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH="$ROOT/packages/domain/src:$ROOT/packages/integrations/src:$ROOT/packages/knowledge/src:$ROOT/packages/agent/src:$ROOT/packages/observability/src:${PYTHONPATH:-}"

if [[ ! -f .env ]]; then
  echo "Missing .env — run make setup first (copies from .env.example)."
  exit 1
fi

UVICORN_BIN="uvicorn"
if [[ -x "$ROOT/apps/api/.venv/bin/uvicorn" ]]; then
  UVICORN_BIN="$ROOT/apps/api/.venv/bin/uvicorn"
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

PIDS=()
cleanup() {
  echo "Shutting down dev processes..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

start_uvicorn() {
  local app="$1"
  local port="$2"
  local cwd="$3"
  echo "Starting $app on :$port"
  (cd "$cwd" && PYTHONPATH="${PYTHONPATH:-.}:." "$UVICORN_BIN" "$app" --host 0.0.0.0 --port "$port" --reload) &
  PIDS+=($!)
}

# Mocks
if [[ -f services/mock-crm/app/main.py ]]; then
  start_uvicorn app.main:app 8101 services/mock-crm
fi
if [[ -f services/mock-erp/app/main.py ]]; then
  start_uvicorn app.main:app 8102 services/mock-erp
fi
if [[ -f services/mock-carrier/app/main.py ]]; then
  start_uvicorn app.main:app 8103 services/mock-carrier
fi
if [[ -f services/mock-ticketing/app/main.py ]]; then
  start_uvicorn app.main:app 8104 services/mock-ticketing
fi

# API
if [[ -f apps/api/app/main.py ]]; then
  echo "Starting API on :8000"
  (cd apps/api && PYTHONPATH="$PYTHONPATH:." "$UVICORN_BIN" app.main:app --host 0.0.0.0 --port 8000 --reload) &
  PIDS+=($!)
else
  echo "API main not found yet — skipping API process"
fi

# Web
if [[ -f apps/web/package.json ]]; then
  echo "Starting web on :3000"
  (cd apps/web && (pnpm dev 2>/dev/null || npm run dev)) &
  PIDS+=($!)
else
  echo "Web package not found yet — skipping web process"
fi

echo "Dev stack running (pids: ${PIDS[*]:-none}). Ctrl+C to stop."
wait
