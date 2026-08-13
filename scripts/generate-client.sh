#!/usr/bin/env bash
# Generate TypeScript client from running API OpenAPI schema.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/packages/sdk-typescript/src/generated"
mkdir -p "$OUT"
URL="${OPENAPI_URL:-http://localhost:8000/openapi.json}"
curl -sf "$URL" -o /tmp/enterprise-ai-openapi.json
npx --yes openapi-typescript /tmp/enterprise-ai-openapi.json -o "$OUT/schema.ts"
echo "Wrote $OUT/schema.ts"
