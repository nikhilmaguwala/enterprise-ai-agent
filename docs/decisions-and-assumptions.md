# Decisions and Assumptions

## Confirmed decisions

1. **SQLAlchemy 2.x**, not Drizzle — backend is Python; spec mandates SQLAlchemy + Alembic.
2. **Modular monolith** under `apps/api` with packages for agent/domain/integrations/knowledge/observability.
3. **Mock enterprise systems** are separate FastAPI apps under `services/` accessed only via HTTP.
4. **Neon** is used as Postgres for both local (when Docker unavailable) and hosted demo.
5. **Groq** is the primary LLM; Gemini/Ollama adapters exist but mutations never silently fall back.
6. **Dev auth** uses HS256 local JWTs when `DEV_AUTH_ENABLED=true` (default false in production).
7. **Vercel** hosts the Next.js frontend; API URL is configured via env.
8. **FastAPI Cloud** deployment is documented (`fastapi deploy`); requires interactive login — not invented CI credentials.

## Assumptions

- Operator will create Auth0, Upstash, R2, Langfuse accounts using the setup guide.
- Public demo runs with synthetic tenants only and quota limits.
- Embeddings may use Groq-compatible or local hash/fallback embeddings when a dedicated embedding model is unavailable; document the limitation.
- Playwright e2e runs in CI when browsers are available; critical backend isolation tests always run.

## Risks accepted for hobby tier

- Scale-to-zero cold starts → external job drain scheduler.
- Free LLM budget exhaustion → recorded demo + architecture pages remain available.
- Qdrant free cluster limits → small synthetic corpus only.

## Explicit non-claims

- Measured latency/cost numbers in README will be filled only after real runs.
- Terraform modules are conceptual and do not auto-provision chargeable AWS resources.
