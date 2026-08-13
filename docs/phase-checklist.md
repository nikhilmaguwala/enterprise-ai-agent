# Phase Checklist

| Phase | Status | Notes |
| --- | --- | --- |
| 1 Planning | done | Plan, architecture, assumptions |
| 2 Foundation | done | Monorepo, Neon migrations, mocks, seed, health |
| 3 Identity & tenancy | done | Dev auth + RBAC + isolation tests (20 pytest) |
| 4 RAG | done | Chunking, Qdrant adapter (`query_points`), hybrid retrieval + fallback |
| 5 Read-only agent | done | LangGraph 13 nodes + SSE events + grounded citations |
| 6 Safe actions | done | Approval pause/resume, ERP mutation, verify, audit |
| 7 Reliability | done | Postgres jobs SKIP LOCKED, HMAC drain, outbox models |
| 8 Evals & observability | done | 60 JSONL cases, graders, structlog, Langfuse adapter |
| 9 Deployment | partial | **Vercel live**; FastAPI Cloud / Auth0 / Upstash / R2 / Langfuse need operator steps |
| 10 Portfolio polish | done | ADRs, threat model, demo script, runbooks |

## Critical path demo criteria

- [x] Two tenants isolated (tests)
- [x] Delay explanation with citations
- [x] Address change requires approval
- [x] Mutation executes once and verifies
- [x] Escalation path on failure
- [x] Jobs model + drain endpoint
- [x] Quota service present
- [x] Docs present
- [x] No secrets in git (`.env` gitignored)

## Hosted URLs

Set in your deployment provider (not committed):

- Frontend (Vercel): `https://your-app.vercel.app`
- Backend (FastAPI Cloud): `https://your-app.fastapicloud.dev`
