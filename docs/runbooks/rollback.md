# Runbook: Rollback

## Scope

Rollback of web (Vercel), API (FastAPI Cloud), and database migrations for the hobby demo.

## Frontend (Vercel)

1. Vercel dashboard → Project → Deployments.
2. Promote previous known-good production deployment.
3. Confirm `NEXT_PUBLIC_API_URL` still points at intended API.

## Backend (FastAPI Cloud)

1. Check current healthy git SHA / deploy time.
2. Locally check out the last known-good commit.
3. From `apps/api` run `fastapi deploy` (interactive login if needed).
4. Confirm `/health` and a smoke chat.

There is no invented “fastapi rollback” flag documented here — redeploy the prior revision.

## Database

1. Prefer forward-fix migrations.
2. If a migration must revert, use a **new** Alembic revision that undoes the change after backup/snapshot in Neon.
3. Avoid `downgrade` on shared demo DB without a snapshot.

## Feature flags / config

1. Revert risky env vars (model name, quota, `DEV_AUTH_ENABLED`).
2. Keep Auth0 callbacks aligned with the live web origin.

## Verification

- Critical path: delay explanation + approval mutation on synthetic order.
- Eval smoke still passes in CI on the rolled-back commit if that commit is restored to `main` intentionally.
- Announce rollback in team notes with timestamp and SHA.
