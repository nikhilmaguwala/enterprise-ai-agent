# Runbook: Suspected credential leak

## Symptoms

- Secret scanning alert (gitleaks/CI).
- Unexpected LLM/API spend.
- Auth anomalies or public gist with keys.

## Immediate actions (stop the bleed)

1. **Rotate** compromised credentials in provider consoles (Groq, Neon, Qdrant, Auth0, Upstash, R2, Langfuse, mock tokens).
2. Revoke old keys; do not merely delete from `.env`.
3. Purge secrets from git history if committed (`git filter-repo` / support process) — coordinate before force-pushing shared branches.
4. Invalidate FastAPI Cloud / Vercel env that still hold old values; set new secrets.
5. Set `DEV_AUTH_ENABLED=false` anywhere public.

## Investigation

1. Identify exposure window from CI/commit timestamps.
2. Review audit logs for abnormal tool mutations.
3. Check Upstash/Neon metrics for unusual traffic.

## Prevention

- `.env` gitignored; placeholders only in `.env.example`.
- gitleaks on PRs.
- Prefer dashboard secret fields (`fastapi cloud env set --secret`).

## Verification

- Old keys fail when tested in a scratch request.
- App healthy with new keys.
- CI secret scan clean on latest commit.
