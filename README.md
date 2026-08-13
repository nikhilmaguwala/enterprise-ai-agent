# Enterprise AI Support Agent

Multi-tenant AI customer-support platform for a fictional e-commerce company. Demonstrates grounded RAG answers, multi-system tool use, human-in-the-loop approvals, idempotent mutations, durable jobs, and tenant isolation.

## Product problem

Support teams need an agent that can explain delayed orders with evidence and safely change delivery addresses — without inventing policy, bypassing authorization, or double-applying mutations.

## Solution

A modular FastAPI monolith + Next.js UI that:

1. Authenticates users and resolves organization membership
2. Retrieves tenant-scoped policy via hybrid RAG (Qdrant)
3. Calls mock CRM / ERP / carrier / ticketing HTTP APIs
4. Pauses for explicit approval before mutations
5. Executes once with idempotency keys and verifies results
6. Escalates with a handoff summary when unsafe or under-evidenced

## Screenshots

> Placeholders — capture after local/demo run.

- Customer chat with citations and approval card
- Support inbox handoff
- Agent-run inspector
- Evaluation dashboard
- Operations / queue health

## Architecture

See [docs/architecture.md](docs/architecture.md).

## Technology stack

- **Backend:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, LangGraph, Groq
- **Frontend:** Next.js App Router, TypeScript strict, Tailwind, TanStack Query, SSE
- **Data:** Neon Postgres, Qdrant Cloud, Upstash Redis (ephemeral), Cloudflare R2
- **Auth:** Auth0 OIDC (+ local dev tokens)
- **Hosting:** FastAPI Cloud + Vercel Hobby
- **Obs:** structlog, OpenTelemetry hooks, Langfuse (optional)

## Local setup

```bash
make setup   # copies .env.example if missing, installs deps, migrates, seeds
make dev     # API + web + mocks
make test
make eval
```

Requires Python 3.12+, Node 20+, and either Docker Compose **or** a reachable `DATABASE_URL` (e.g. Neon).

## Demo users (synthetic)

| Role | Email | Org |
| --- | --- | --- |
| Customer | `customer@acme-demo.test` | Acme Retail |
| Support | `agent@acme-demo.test` | Acme Retail |
| Supervisor | `supervisor@acme-demo.test` | Acme Retail |
| Admin | `admin@acme-demo.test` | Acme Retail |
| Customer B | `customer@globex-demo.test` | Globex Shop |

Dev auth tokens are minted when `DEV_AUTH_ENABLED=true`.

## Environment

Copy `.env.example` → `.env`. Never commit secrets.

## Testing / evaluation

```bash
make test
make eval
```

## Deployment

- Frontend: Vercel (automated from this repo)
- Backend: FastAPI Cloud — see [docs/deployment.md](docs/deployment.md)
- Remaining free-tier services: Auth0, Upstash, R2, Langfuse — setup steps in deployment docs

## Security

Deterministic RBAC outside the LLM, tenant filters on every Qdrant query, idempotent writes, approval revalidation, redacted logs. Threat model: [docs/threat-model.md](docs/threat-model.md).

## Known limitations

- Hobby-tier quotas and cold starts
- Synthetic corpus and mock enterprise systems
- Optional services degrade when unavailable

## Production migration

See architecture / deployment docs for AWS mapping (ECS, RDS, S3, ElastiCache, etc.).

## Demo video

Placeholder for a 2-minute walkthrough.

## My contribution

Designed and implemented end to end: architecture, multi-tenant backend, agent workflow, RAG, approvals, jobs, frontend, evaluations, and deployment documentation.

## Measured results

_Filled after real test/eval runs — not invented._
