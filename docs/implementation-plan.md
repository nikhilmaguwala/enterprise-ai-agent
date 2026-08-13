# Implementation Plan — Enterprise AI Support Agent

## Goal

Ship a production-quality, multi-tenant AI customer-support platform that demonstrates the delayed-order + address-change approval workflow end to end, with portfolio-grade engineering (security, reliability, observability, evaluations).

## Stack confirmation

| Layer | Choice | Notes |
| --- | --- | --- |
| Backend ORM | **SQLAlchemy 2.x + Alembic** | Spec requirement; not Drizzle (Drizzle is TS-first) |
| Frontend | Next.js App Router + TanStack Query + Zod | Vercel Hobby |
| Vector | Qdrant Cloud | Tenant-filtered hybrid retrieval |
| LLM | Groq (`openai/gpt-oss-20b`) | Provider-neutral adapters |
| Auth | Auth0 OIDC + local signed-dev tokens | Dev mode off in production |
| Jobs | PostgreSQL `FOR UPDATE SKIP LOCKED` | Redis ephemeral only |
| Hosting | FastAPI Cloud + Vercel + Neon | Document remaining free-tier setup |

## Assumptions

1. Neon, Groq, and Qdrant credentials are available for hosted/local hybrid development.
2. Auth0, Upstash, R2, Langfuse, and FastAPI Cloud require interactive account setup by the operator — adapters and docs ship regardless.
3. Docker may be unavailable on the build machine; Compose files still ship; local Postgres can use Neon.
4. Mock CRM/ERP/carrier/ticketing run as separate FastAPI apps (in-process or Compose services).
5. Synthetic data only; no real PII.

## Risks

| Risk | Mitigation |
| --- | --- |
| FastAPI Cloud deploy needs interactive login | Document exact `fastapi deploy` steps; CI marked manual |
| Free-tier cold starts / scale-to-zero | HMAC-signed `/internal/jobs/drain` for external scheduler |
| Provider outages during mutations | No silent fallback; pause + escalate |
| Secret leakage | `.env` gitignored; placeholders in `.env.example`; secret scanning in CI |
| Scope explosion | Phase gates; critical-path first (delay + address change) |

## Phase order

1. Planning + docs skeleton
2. Foundation (monorepo, API, web, DB, mocks, seed, health)
3. Identity & tenancy
4. RAG
5. Read-only agent + SSE
6. Safe actions (approval, idempotency, audit)
7. Durable jobs + outbox
8. Evaluations + observability
9. Deployment (Vercel auto; FastAPI Cloud documented)
10. Portfolio polish

## Verification gates (every phase)

- Format/lint
- Relevant tests
- Services start or build
- Checklist update
- App remains runnable

## Non-goals for v1

- Real AWS deployment
- Real employer data
- Microservices split
- Paying for LLM fallback without explicit config
