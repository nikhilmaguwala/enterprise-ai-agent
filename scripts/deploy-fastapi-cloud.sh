#!/usr/bin/env bash
# Deploy API to FastAPI Cloud (requires prior `fastapi login`).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT/apps/api"
FASTAPI_BIN="${FASTAPI_BIN:-$API_DIR/.venv/bin/fastapi}"

bash "$ROOT/scripts/prepare-fastapi-cloud.sh"

if [[ ! -x "$FASTAPI_BIN" ]]; then
  echo "Missing FastAPI CLI. Run: cd apps/api && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'"
  exit 1
fi

echo "Checking FastAPI Cloud login..."
if ! "$FASTAPI_BIN" cloud whoami >/dev/null 2>&1; then
  echo "Not logged in. Run this first (opens browser):"
  echo "  cd apps/api && fastapi login"
  exit 1
fi

echo "Deploying from $API_DIR ..."
cd "$API_DIR"
"$FASTAPI_BIN" deploy --app-id cbb6161b-3492-4f56-aff4-fbd0b6ac565b --json

echo ""
echo "Next steps:"
echo "  1. Set env vars: fastapi cloud env set --secret DATABASE_URL '...'"
echo "  2. Copy the *.fastapicloud.dev URL into Vercel NEXT_PUBLIC_API_URL"
echo "  3. Set DEV_AUTH_ENABLED=false once Auth0 is configured"
echo "See docs/setup-remaining-services.md and infra/fastapi-cloud/README.md"
