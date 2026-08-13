# Runbook: Database migration failure

## Symptoms

- `alembic upgrade head` errors in CI/deploy/setup.
- API boot fails on schema mismatch.
- Partial migration applied.

## Immediate actions

1. Capture exact Alembic revision and error text.
2. **Do not** invent `downgrade` in production without a reviewed plan.
3. Check Neon console for locks / storage / connection limits.

## Local recovery

```bash
cd apps/api
alembic current
alembic history
# Fix migration script if not yet applied anywhere
alembic upgrade head
```

## Hosted recovery

1. Pause deploys.
2. Apply fixed migration from a controlled environment with `DATABASE_URL` secret.
3. Re-run API health.
4. Re-seed only if seed is idempotent and environment is demo/synthetic.

## Prevention

- Migration validation job in CI.
- Expand/contract patterns for destructive changes.
- Never edit already-applied revisions; add a new revision.

## Verification

- `alembic current` matches head.
- API `/health` DB check passes.
- Critical path demo still works (login → delay Q&A).
