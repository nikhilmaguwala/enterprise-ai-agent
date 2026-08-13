# ResolveAI — Enterprise AI Support Agent

Multi-tenant AI customer-support platform for e-commerce operations. Grounds answers in tenant policy (RAG), calls enterprise systems via tools, pauses for human approval before mutations, executes idempotently, and leaves a full audit trail.

**Demo deployment (set your own URLs in env — not stored in this repo)**

| Surface | Example |
| --- | --- |
| Web app | `https://your-app.vercel.app` |
| API | `https://your-app.fastapicloud.dev` |
| API docs | `https://your-app.fastapicloud.dev/docs` |

---

## What you built

An end-to-end **B2B support agent product** — not a chatbot wrapper. You designed and shipped:

- A **multi-tenant SaaS-shaped backend** (organizations, users, roles, tenant-scoped data)
- A **LangGraph agent workflow** with tool use, RAG, approvals, and escalation
- A **ResolveAI-themed Next.js console** (chat, inbox, knowledge, ops, team invites)
- **Production deployment** on Vercel + FastAPI Cloud with CI/CD, migrations, and email
- **Evaluation harness** with deterministic graders and a 60-case dataset
- **Architecture documentation**, ADRs, threat model, and runbooks

The fictional domain is order delays and address changes, but the patterns (tenant isolation, HITL, idempotency, durable jobs) are what real enterprise SaaS products use.

---

## Is this SaaS-level?

**Short answer:** Strong **MVP / production-demo SaaS architecture** — not yet a **commercial SaaS business** (billing, enterprise SSO in prod, SOC2, etc.).

| SaaS capability | Status | Notes |
| --- | --- | --- |
| Multi-tenant data model | **Implemented** | `Organization`, `Membership`, tenant filters on queries + RAG |
| Self-serve signup | **Implemented** | Email/password registration creates org + admin + starter order |
| Team invites | **Implemented** | Admin invites by email (Brevo); roles: customer, agent, supervisor, admin |
| Role-based access (RBAC) | **Implemented** | Deterministic auth outside the LLM; route + API guards |
| Tenant isolation tests | **Implemented** | Integration tests in CI |
| Real auth in production | **Partial** | JWT access tokens (signup/login); Auth0 OIDC wired but not primary prod path |
| Usage quotas | **Implemented** | Per-user / global daily message + model-call limits |
| Audit trail | **Implemented** | Append-only `AuditEvent`; approval payload hashing |
| Human-in-the-loop mutations | **Implemented** | Approve/reject before ERP address change |
| Idempotent writes | **Implemented** | `Idempotency-Key` on messages + tool mutations |
| Durable background jobs | **Implemented** | Postgres job queue + outbox + dead-letter replay |
| Knowledge base (RAG) | **Implemented** | Upload → chunk → embed → Qdrant; tenant-filtered retrieval |
| Real-time UX | **Implemented** | SSE stream for tool progress, approvals, run status |
| Observability hooks | **Partial** | structlog, OTEL/Prometheus hooks, optional Langfuse |
| Billing / subscriptions | **Not implemented** | No Stripe, plans, or seat billing |
| Enterprise SSO (SAML/OIDC prod) | **Not implemented** | Auth0 config exists; prod uses first-party JWT auth |
| Custom domains / white-label | **Not implemented** | Single Vercel deployment |
| SLA / multi-region | **Not implemented** | Hobby-tier hosting |
| SOC2 / compliance pack | **Not implemented** | Threat model + runbooks only |

**Verdict:** Architecturally **SaaS-grade** for a technical portfolio and pilot customers. Operationally **pre-revenue SaaS** — you'd add billing, enterprise auth, and hardening before charging enterprises.

---

## Feature catalog

### Frontend (`apps/web`)

ResolveAI-themed App Router UI with role-aware navigation.

| Route | Who | What it does |
| --- | --- | --- |
| `/` | Public | Marketing landing page |
| `/signup` | Public | Create company workspace (admin + starter order) |
| `/login` | Public | Email/password login |
| `/dashboard` | All roles | Overview and quick links |
| `/chat` | All roles | Conversation list, streaming chat, citations, approval cards, order context panel |
| `/inbox` | Agent+ | Escalation queue with handoff summaries |
| `/knowledge` | Agent+ | Document list, upload, ingest status |
| `/evaluations` | Supervisor+ | Eval run history and dashboard |
| `/operations` | Admin | Job queue health, replay, ops dashboard |
| `/team/invite` | Admin | Invite teammates (role picker, permission summary) |
| `/architecture` | All | In-app architecture diagram (Mermaid) |
| `/runs/[id]` | All | Agent run inspector (events, graph state) |

**UX details**

- Live vs demo mode detection (`@acme-demo.test` = demo chrome; real users see **Live** badge)
- TanStack Query for API state; Zod-validated responses
- SSE for agent events (tool started/finished, approval required, message completed)
- Next.js API proxy: `/api/auth/*` and `/api/v1/*` → FastAPI Cloud (avoids CORS and bad public env)

### Backend API (`apps/api`)

Modular FastAPI monolith. All routes under `/api/v1` unless noted.

| Module | Endpoints | Purpose |
| --- | --- | --- |
| **Health** | `GET /health/live`, `/health/ready`, `/version` | Liveness, DB readiness, build info |
| **Auth** | `POST /auth/register`, `/login`, `/invite`, `/dev-login`, `/dev-token`; `GET /auth/me` | Workspace signup, login, team invites, dev tokens |
| **Conversations** | `GET/POST /conversations`, `GET /conversations/{id}`, `GET/POST .../messages` | Threads and user messages (triggers agent) |
| **Events** | `GET /conversations/{id}/events` | SSE stream of agent run events |
| **Approvals** | `GET /approvals/{id}`, `POST .../approve`, `.../reject` | Human-in-the-loop mutation gate |
| **Documents** | Presign, upload, complete, list, download, delete | Knowledge ingestion pipeline |
| **Knowledge** | `GET /knowledge/documents` | Tenant document index |
| **Agent runs** | List/get runs and run events | Debugging and UI inspector |
| **Jobs** | List jobs, replay, internal drain | Background processing |
| **Operations** | Dashboard, job replay | Admin ops view |
| **Inbox** | `GET /inbox/escalations` | Support escalation queue |
| **Evaluations** | Start/list runs, dashboard | Offline eval orchestration |
| **Audit** | `GET /audit` | Tenant audit log |
| **Notifications** | `POST /notifications/test-email` | Brevo email smoke test |
| **Integrations** | `GET /integrations/health` | Mock/real service health |

**Embedded mocks** (when `EMBEDDED_MOCKS_ENABLED=true`): CRM, ERP, carrier, ticketing under `/mocks/*` on the same API host — used on FastAPI Cloud without separate mock containers.

### AI agent (`packages/agent`)

LangGraph workflow (`graph_version=v1`):

1. Authenticate and load context  
2. Classify intent  
3. Load customer + order (CRM/ERP tools)  
4. Retrieve policy (tenant-scoped RAG)  
5. Check delivery (carrier tool)  
6. Compose grounded explanation with citations  
7. Validate proposed action (policy engine — **not** LLM-only)  
8. Request human approval **or** escalate **or** finalize  
9. Execute approved mutation (idempotent ERP call)  
10. Verify result and finalize  

**LLM providers:** Groq (primary), Gemini (fallback), Ollama (local), fake (tests).

**Tools:** Typed HTTP gateway to CRM, ERP, carrier, and ticketing (`packages/integrations`).

### Knowledge / RAG (`packages/knowledge`)

- Presigned upload → MIME/checksum validation → async extract job  
- PDF text extraction, section-aware chunking  
- Embeddings upserted to **Qdrant** with `organization_id` metadata filter on every search  
- Citations returned inline in assistant messages  

### Shared packages

| Package | Role |
| --- | --- |
| `packages/domain` | Policy engine, intent/error classification, chunking helpers |
| `packages/integrations` | CRM, ERP, carrier, ticketing HTTP clients |
| `packages/knowledge` | Retrieval and ingestion |
| `packages/agent` | LangGraph graph + nodes + LLM providers |
| `packages/observability` | Logging/metrics helpers |

### Data model (Postgres)

Core entities: `Organization`, `User`, `Membership`, `Customer`, `Order`, `Shipment`, `Conversation`, `Message`, `AgentRun`, `AgentEvent`, `Approval`, `Document`, `DocumentChunk`, `Job`, `DeadLetterRecord`, `OutboxEvent`, `IdempotencyRecord`, `AuditEvent`, `UsageCounter`, evaluation tables.

Alembic migrations run on API startup in cloud (`RUN_MIGRATIONS_ON_STARTUP=true`).

### Evaluations (`evals/`)

- **60-case** JSONL dataset (`evals/datasets/cases.jsonl`)  
- Deterministic graders: grounding, forbidden tools, injection resistance, approval behavior  
- CI smoke: `make eval` / workflow **Deterministic eval suite**  
- Categories: order/shipment, policy, address change, dependency failure, missing evidence, prompt injection  

### CI/CD (`.github/workflows/`)

| Workflow | Trigger | Jobs |
| --- | --- | --- |
| `ci.yml` | Pull request | Python lint + unit tests, TS lint, gitleaks, optional Docker, eval smoke |
| `main.yml` | Push to main | Full test suite (Ruff, pytest, web lint), eval dataset check |
| `deploy.yml` | Push to main | Deploy API → FastAPI Cloud; deploy web → Vercel (pnpm + prebuilt) |

Python CI uses `uv sync` + `scripts/prepare-fastapi-cloud.sh` for monorepo packages.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser  →  Next.js (Vercel)  →  proxy /api/v1/*  →  FastAPI │
└─────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
    Neon Postgres              Qdrant Cloud                 Groq / Gemini
    (system of record)         (tenant RAG index)            (LLM tools)
          │
          ├── Jobs / outbox / idempotency
          ├── Conversations / approvals / audit
          └── Usage quotas

    Object storage: Firebase / R2 / local filesystem
    Email: Brevo (invites, notifications)
    Optional: Upstash Redis, Langfuse, Sentry
```

Deep dive: [docs/architecture.md](docs/architecture.md) · ADRs in [docs/adr/](docs/adr/) · Threat model: [docs/threat-model.md](docs/threat-model.md)

---

## Technology stack

| Layer | Technologies |
| --- | --- |
| **Backend** | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, bcrypt, python-jose |
| **Agent** | LangGraph, LangChain Core, Groq SDK |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind 4, TanStack Query, Zod, SSE |
| **Database** | PostgreSQL (Neon in prod) |
| **Vector** | Qdrant Cloud |
| **Storage** | Firebase Storage / Cloudflare R2 / MinIO (local) |
| **Email** | Brevo |
| **Hosting** | Vercel (web) + FastAPI Cloud (API) |
| **Tooling** | uv, ruff, mypy, pytest, ESLint, gitleaks |

---

## User workflows

### 1. New company (real signup)

1. Go to `/signup` — company name, your name, email, password  
2. Backend creates **organization**, **admin membership**, **customer**, and a **starter order** (`ORD-XXXXXX`)  
3. You land in `/chat` as **Live** (not demo)  
4. Start a conversation and ask about your order number  

### 2. Support agent flow

1. Admin invites agent at `/team/invite`  
2. Agent receives Brevo email with temporary password  
3. Agent logs in → `/chat` or `/inbox` for escalations  
4. Approves/rejects address-change cards in chat  

### 3. Local demo users (dev only)

When `DEV_AUTH_ENABLED=true`:

| Role | Email | Org |
| --- | --- | --- |
| Customer | `customer@acme-demo.test` | Acme Retail |
| Support agent | `agent@acme-demo.test` | Acme Retail |
| Supervisor | `supervisor@acme-demo.test` | Acme Retail |
| Admin | `admin@acme-demo.test` | Acme Retail |
| Customer B | `customer@globex-demo.test` | Globex Shop |

Demo order: `ACM-10001`. Dev user switcher visible only in demo mode.

---

## Local development

**Prerequisites:** Python 3.12+, Node 20+, optional Docker for Postgres/Redis/Qdrant/MinIO.

```bash
make setup   # .env, deps, migrate, seed
make dev     # API + web + mock services
make test    # unit tests
make eval    # deterministic eval smoke
make lint
```

Copy `.env.example` → `.env`. Never commit secrets. See [docs/deployment.md](docs/deployment.md) for every external service.

**Key env vars**

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Postgres (`postgresql+asyncpg://...`) |
| `GROQ_API_KEY` | Primary LLM |
| `QDRANT_URL` / `QDRANT_API_KEY` | Vector search |
| `NEXT_PUBLIC_API_URL` | Web → API (local: `http://localhost:8000`) |
| `DEV_AUTH_ENABLED` | Local demo login |
| `BREVO_API_KEY` | Invite emails |

---

## Deployment

Automated on every push to `main`:

1. **API:** `scripts/prepare-fastapi-cloud.sh` → `uv run fastapi cloud deploy`  
2. **Web:** Vercel CLI (`vercel pull` → `vercel build --prod` → `vercel deploy --prebuilt --prod`)  

Required GitHub **secrets**: `FASTAPI_CLOUD_TOKEN`, `FASTAPI_CLOUD_APP_ID`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.

Required GitHub **variables** (Repository → Settings → Secrets and variables → Actions → Variables):

| Variable | Example |
| --- | --- |
| `PUBLIC_API_URL` | `https://your-app.fastapicloud.dev` |
| `PUBLIC_APP_URL` | `https://your-app.vercel.app` |

Full checklist: [docs/deployment.md](docs/deployment.md) · Remaining services: [docs/setup-remaining-services.md](docs/setup-remaining-services.md)

---

## Security

- **Tenant context** from JWT membership — never trust `organization_id` from request body alone  
- **RBAC** enforced in API and policy engine before tools run  
- **Approvals** with payload hash + revalidation on approve  
- **Idempotency** on mutating endpoints  
- **Quota guards** against cost abuse  
- **Gitleaks** in CI; secrets only server-side  
- **Redacted structured logs**  

Details: [docs/threat-model.md](docs/threat-model.md)

---

## Testing

```bash
# From repo root after make setup
cd apps/api && uv run pytest tests/unit tests/integration -q
```

**24 tests** including tenant isolation integration tests. CI runs Ruff, full pytest, web ESLint, and eval dataset smoke (≥60 cases).

---

## Known limitations (honest)

- Hobby-tier cold starts and quotas on Vercel / FastAPI Cloud / Groq free tier  
- Enterprise integrations are **mock HTTP services** (or embedded mocks), not live Salesforce/SAP  
- Policy corpus is **synthetic** demo content  
- Production auth is **first-party JWT** (signup/login), not full Auth0 SSO yet  
- No billing, invoicing, or subscription management  
- Some UI panels (shipment timeline, quota %) are **placeholder copy** until tool results populate them  
- Virus scanning on uploads documented as production follow-up  

---

## Roadmap to full commercial SaaS

1. **Stripe** — plans, seats, usage-based LLM metering  
2. **Auth0 / WorkOS** — enterprise SSO, SCIM provisioning  
3. **Real connectors** — Shopify, Zendesk, Salesforce, carrier APIs  
4. **SOC2** — audit exports, retention policies, pen test  
5. **Multi-region** — read replicas, regional Qdrant, edge SSE  
6. **Customer admin** — usage dashboards, data export, DPA  

---

## Repository layout

```
enterprise-ai-agent/
├── apps/
│   ├── api/          # FastAPI monolith, Alembic, tests
│   └── web/          # Next.js ResolveAI console
├── packages/         # domain, agent, knowledge, integrations, observability
├── services/         # Standalone mock CRM/ERP/carrier/ticketing (local Docker)
├── evals/            # Datasets + graders
├── docs/             # Architecture, ADRs, deployment, runbooks
├── infra/            # docker-compose, Vercel config
└── scripts/          # dev.sh, prepare-fastapi-cloud.sh, seed
```

---

## Documentation index

| Doc | Contents |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | C4 diagrams, agent workflow, RAG pipeline |
| [docs/deployment.md](docs/deployment.md) | Neon, Qdrant, Groq, Vercel, FastAPI Cloud |
| [docs/threat-model.md](docs/threat-model.md) | Threats and mitigations |
| [docs/demo-script.md](docs/demo-script.md) | Live demo walkthrough |
| [docs/implementation-plan.md](docs/implementation-plan.md) | Build phases |
| [docs/adr/](docs/adr/) | Architecture decision records |
| [docs/runbooks/](docs/runbooks/) | Incident runbooks |

---

## Making this repo public

**Safe — not in git (gitignored):**

- `.env`, `.env.local`, `apps/web/.env.local`
- `infra/secrets/**` (Firebase admin JSON)
- `.vercel/`, `.fastapicloud/`, local storage under `data/storage/`

**Scrubbed from source:**

- Personal Firebase bucket names → configure via `FIREBASE_STORAGE_BUCKET`
- FastAPI Cloud app id → `FASTAPI_CLOUD_APP_ID` env / GitHub secret
- Production URLs → GitHub Actions variables `PUBLIC_API_URL`, `PUBLIC_APP_URL`

**Still rotate if this repo was ever private with real keys in local `.env`:**

Neon, Qdrant, Groq, Brevo, Vercel/FastAPI tokens, Firebase service account, Auth0 client secret, `DEV_AUTH_SECRET`, `INTERNAL_JOB_*`.

**Git history:** commit author metadata (name/email) remains in history — normal for public repos. No API keys or Firebase JSON were found in tracked history.

CI runs **gitleaks** on pull requests.

---

## Author

Designed and implemented end to end: multi-tenant backend, LangGraph agent, RAG pipeline, approvals, durable jobs, ResolveAI frontend, evaluations, production deployment, and documentation.

**Measured results** — fill after benchmark runs (test count: 24 passing; eval dataset: 60 cases; CI: green on main).
