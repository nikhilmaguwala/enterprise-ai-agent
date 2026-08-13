# Runbook: Qdrant unavailable

## Symptoms

- Policy answers lack citations or retrieval errors in agent runs.
- Knowledge ingest jobs fail at upsert.
- `/health` reports Qdrant unhealthy.

## Immediate actions

1. Check Qdrant Cloud console status and API key.
2. Confirm `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`.
3. For local Compose: `docker compose -f infra/docker-compose.yml ps qdrant` and restart if needed.

## Expected product behavior

- Do **not** invent policy text without retrieval.
- Prefer escalation / “insufficient evidence” when retrieval fails.
- Relational data (orders via mocks) may still load; grounded policy path degrades.

## Mitigation

1. Restore Qdrant connectivity.
2. Re-run failed ingest jobs / DLQ replay for knowledge upserts.
3. If collection missing, recreate via admin ingest bootstrap (no manual prod data inventing).

## Verification

- Retrieval returns tenant-filtered hits for Acme policy doc.
- Citation IDs resolve in UI.
- Globex query still cannot retrieve Acme chunks.
