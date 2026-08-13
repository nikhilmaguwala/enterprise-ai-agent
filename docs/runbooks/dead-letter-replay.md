# Runbook: Dead-letter replay

## Symptoms

- Jobs stuck in `dead_letter` / failed terminal state.
- Knowledge ingest or ticket creation not completed.
- Ops UI shows DLQ depth > 0.

## Preconditions

- Root cause understood (transient vs poison message).
- Supervisor/admin role for replay.
- Idempotency keys still valid for any mutating side effects.

## Steps

1. Inspect dead-letter payload, error class, attempt count, correlation IDs.
2. Fix underlying dependency (mock ERP down, Qdrant auth, etc.).
3. Replay **eligible** jobs only (supervisor action or internal admin API).
4. Watch worker/`/internal/jobs/drain` process the replay.
5. Confirm side effects occurred once (idempotency).

## Do not

- Blindly replay payment-like mutations without verify-read strategy.
- Delete audit history to “clear” DLQ.
- Replay across tenants.

## Verification

- DLQ depth decreases.
- Original conversation/run shows successful follow-through.
- No duplicate ERP mutations in mock logs.
