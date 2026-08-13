# ResolveAI — Enterprise AI Support Agent

**Portfolio project · Full-stack multi-tenant AI support platform**

A production-deployed B2B support agent for e-commerce operations. It grounds answers in tenant policy (RAG), calls enterprise systems through typed tools, requires human approval before mutations, executes writes idempotently, and records a full audit trail.

> **For reviewers:** This repo is a complete end-to-end build — backend, agent orchestration, frontend, CI/CD, evals, and architecture docs. Read [Project scope](#project-scope) and [Engineering highlights](#engineering-highlights) first.

---

## At a glance

| | |
| --- | --- |
| **Problem** | Support teams need an agent that explains order issues with evidence and safely changes addresses — without hallucinating policy or double-applying mutations. |
| **Approach** | Modular FastAPI monolith + LangGraph workflow + Next.js console, multi-tenant from day one. |
| **Domain** | Fictional e-commerce (order delays, address changes, escalations). |
| **Deployment** | Vercel (frontend) + FastAPI Cloud (API) + Neon Postgres + Qdrant + Groq. |
| **Tests** | 24 pytest tests (incl. tenant isolation) · 60-case eval dataset · CI on every PR |
| **Docs** | Architecture, 11 ADRs, threat model, runbooks, deployment guide |

---

## Project scope

I designed and built this project end to end as a **portfolio-grade enterprise AI application**, not a thin ChatGPT wrapper.

### Backend & platform

- Multi-tenant Postgres schema: organizations, memberships, RBAC, customers, orders, conversations, approvals, audit events
- Email/password **signup** (creates org + admin + starter order), **login**, and **team invites** with Brevo email
- JWT auth with deterministic authorization **outside the LLM**
- Tenant isolation enforced in repositories, API routes, and Qdrant queries — covered by integration tests
- Usage quotas (per-user and global daily limits)
- Durable **Postgres job queue** with outbox pattern and dead-letter replay
- **Idempotency keys** on mutating endpoints
- Alembic migrations; auto-run on cloud startup

### AI agent (LangGraph)

13-node workflow: authenticate → classify intent → load CRM/ERP data → RAG policy retrieval → carrier check → grounded response → policy validation → **human approval** → idempotent ERP mutation → verify → finalize (or escalate).

- Tool gateway to mock CRM, ERP, carrier, and ticketing services
- SSE streaming of tool progress, approvals, and run status
- Provider abstraction: Groq (primary), Gemini (fallback), Ollama (local)

### Knowledge / RAG

- Document upload (presigned URL flow), PDF extraction, chunking, embedding
- Qdrant upsert with **mandatory tenant filter** on every search
- Inline citations in assistant messages

### Frontend (ResolveAI UI)

Next.js App Router console with role-aware navigation:

| Route | Access | Purpose |
| --- | --- | --- |
| `/signup`, `/login` | Public | Workspace registration and auth |
| `/chat` | All roles | Streaming chat, citations, approval cards |
| `/inbox` | Agent+ | Escalation queue |
| `/knowledge` | Agent+ | Document upload and ingest status |
| `/evaluations` | Supervisor+ | Eval dashboard |
| `/operations` | Admin | Job queue and ops health |
| `/team/invite` | Admin | Invite teammates by role |
| `/runs/[id]` | All | Agent run inspector |
| `/architecture` | All | In-app Mermaid architecture view |

### DevOps & quality

- GitHub Actions: PR lint/test/secret scan, main-branch full suite, auto-deploy to Vercel + FastAPI Cloud
- Deterministic eval graders (grounding, injection resistance, approval behavior)
- gitleaks in CI; secrets gitignored

### Documentation

| Document | Contents |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | C4 diagrams, agent flow, RAG pipeline |
| [docs/threat-model.md](docs/threat-model.md) | Threats and mitigations |
| [docs/deployment.md](docs/deployment.md) | Full hosting setup |
| [docs/adr/](docs/adr/) | 11 architecture decision records |
| [docs/runbooks/](docs/runbooks/) | Incident runbooks |
| [docs/demo-script.md](docs/demo-script.md) | Demo walkthrough |

---

## Engineering highlights

What this demonstrates for hiring / code review:

1. **Multi-tenancy done seriously** — org context from JWT membership, not client-supplied IDs; isolation tests in CI.
2. **Safe agent actions** — mutations blocked until explicit human approval; policy engine validates before tools run.
3. **Production patterns** — idempotency, audit log, job queue, SSE, API proxy layer, env-based config.
4. **Monorepo structure** — shared packages for domain, agent, knowledge, integrations, observability.
5. **Eval-driven quality** — 60 labeled cases with deterministic graders, not vibes-only testing.
6. **Honest scope** — mocks for enterprise systems; synthetic policy corpus; documented gaps (billing, SSO, SOC2).

---

## Architecture

```
Browser → Next.js (Vercel) → /api/v1 proxy → FastAPI Cloud
                        ↓
              Neon Postgres (system of record)
              Qdrant Cloud (tenant-scoped RAG)
              Groq / Gemini (LLM + tool calling)
              Object storage (Firebase / R2 / local)
              Brevo (transactional email)
```

Agent workflow (simplified):

```
User message → LangGraph → [CRM/ERP/Carrier tools + RAG] → Grounded reply
                                    ↓
                          Address change proposed?
                                    ↓
                          Approval card in UI → Approve → Idempotent ERP write → Verify
```

Full diagrams: [docs/architecture.md](docs/architecture.md)

---

## API surface

Modular FastAPI app under `/api/v1`:

| Area | Capabilities |
| --- | --- |
| Auth | Register, login, invite, me, dev tokens (local) |
| Conversations | CRUD threads, post messages (triggers agent), SSE events |
| Approvals | Get, approve, reject (resumes LangGraph) |
| Knowledge | Presign, upload, ingest, list, delete documents |
| Inbox | Escalation queue |
| Operations | Dashboard, job replay |
| Evaluations | Run eval suites, dashboard |
| Audit | Append-only event log |
| Jobs | Queue list, replay, HMAC-protected drain |

OpenAPI: run locally at `/docs` or on your deployed API URL.

---

## Tech stack

| Layer | Technologies |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, bcrypt |
| Agent | LangGraph, LangChain Core, Groq SDK |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind 4, TanStack Query, Zod |
| Data | PostgreSQL (Neon), Qdrant Cloud, optional Upstash Redis |
| Storage | Firebase / Cloudflare R2 / local filesystem |
| Email | Brevo |
| Hosting | Vercel + FastAPI Cloud |
| CI | GitHub Actions, uv, ruff, pytest, ESLint, gitleaks |

---

## SaaS maturity (honest assessment)

This is **architecturally SaaS-grade** for a technical portfolio and pilot — **not** a commercial SaaS product yet.

| Capability | Status |
| --- | --- |
| Multi-tenant model, signup, invites, RBAC | Done |
| RAG, HITL approvals, idempotency, audit, quotas | Done |
| Production deploy + CI/CD | Done |
| Billing / Stripe | Not built |
| Enterprise SSO in production | Auth0 wired; prod uses first-party JWT |
| Real CRM/ERP integrations | Mock HTTP services |
| SOC2 / compliance | Threat model + runbooks only |

---

## Run locally

**Requirements:** Python 3.12+, Node 20+, optional Docker.

```bash
cp .env.example .env    # fill in Neon, Qdrant, Groq keys
make setup              # deps, migrate, seed
make dev                # API + web + mock services
make test               # pytest
make eval               # eval smoke (60 cases)
```

**Demo users** (when `DEV_AUTH_ENABLED=true`):

| Role | Email |
| --- | --- |
| Customer | `customer@acme-demo.test` |
| Agent | `agent@acme-demo.test` |
| Admin | `admin@acme-demo.test` |

Demo order number: `ACM-10001`

**Real signup flow:** `/signup` → creates your org, admin account, and starter order (`ORD-XXXXXX`) → `/chat`.

---

## Deploy

Push to `main` triggers `.github/workflows/deploy.yml`:

1. API → FastAPI Cloud (`scripts/prepare-fastapi-cloud.sh` + `uv run fastapi cloud deploy`)
2. Web → Vercel (pnpm, prebuilt deploy)

**GitHub secrets:** `FASTAPI_CLOUD_TOKEN`, `FASTAPI_CLOUD_APP_ID`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

**GitHub variables:** `PUBLIC_API_URL`, `PUBLIC_APP_URL`

Guide: [docs/deployment.md](docs/deployment.md)

---

## Security

- Tenant filters on every DB query and vector search
- RBAC enforced in code, not delegated to the LLM
- Approval payload hashing and revalidation on approve
- Secrets in env only (gitignored); gitleaks in CI
- Details: [docs/threat-model.md](docs/threat-model.md)

---

## Repository layout

```
enterprise-ai-agent/
├── apps/api/       FastAPI monolith, Alembic, tests
├── apps/web/       Next.js ResolveAI console
├── packages/       domain, agent, knowledge, integrations, observability
├── services/       Mock CRM, ERP, carrier, ticketing (local Docker)
├── evals/          60-case dataset + deterministic graders
├── docs/           Architecture, ADRs, runbooks, deployment
└── scripts/        dev.sh, prepare-fastapi-cloud.sh, seed
```

---

## Results

| Metric | Value |
| --- | --- |
| Pytest | 24 passing (unit + tenant isolation integration) |
| Eval dataset | 60 cases across 6 categories |
| CI | Green on main (lint, test, eval smoke, deploy) |
| ADRs | 11 documented decisions |
| Frontend routes | 12 pages |
| LangGraph nodes | 13 |

---

## Author

**Nikhil Maguwala**

Full-stack build: system design, multi-tenant backend, LangGraph agent, RAG pipeline, human-in-the-loop approvals, durable jobs, ResolveAI frontend, evaluation harness, CI/CD, and technical documentation.

---

## License

See repository license file. Demo data is synthetic; do not use production PII.
