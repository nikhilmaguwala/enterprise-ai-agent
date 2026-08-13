#!/usr/bin/env bash
# Copy monorepo Python packages into apps/api/packages for FastAPI Cloud builds.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/apps/api/packages"
mkdir -p "$DEST"
for pkg in domain integrations knowledge agent observability; do
  rsync -a --delete "$ROOT/packages/$pkg/" "$DEST/$pkg/"
done
echo "Prepared FastAPI Cloud vendor packages in apps/api/packages"
