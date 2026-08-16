<div align="center">

# ResolveAI

**Enterprise AI support agent — multi-tenant, grounded, approval-gated**

A full-stack portfolio project: customers ask about orders, the agent pulls policy + live data,  
and **nothing mutates until a human approves it**.

<br />

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=nextdotjs)](https://nextjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-111827)](https://langchain-ai.github.io/langgraph/)
[![Tests](https://img.shields.io/badge/tests-24_passing-success)](#tests--quality)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Live Demo](https://img.shields.io/badge/demo-live-059669?style=flat-square)](https://enterprise-ai-support-agent.vercel.app)

<br />

### Live app

| | URL |
| --- | --- |
| **Web app** | https://enterprise-ai-support-agent.vercel.app |
| **API** | https://enterprise-ai-support-agent.fastapicloud.dev |
| **API docs** | https://enterprise-ai-support-agent.fastapicloud.dev/docs |

<br />

**[About](#about)** · **[What it does](#what-it-does)** · **[UI design](#ui-design)** · **[How it works](#how-it-works)** · **[Architecture](#architecture)** · **[Tech stack](#tech-stack)** · **[Quick start](#quick-start)**

</div>

---

## About

| | |
| --- | --- |
| **Project** | ResolveAI — Enterprise AI Support Agent |
| **Type** | Full-stack portfolio project (multi-tenant B2B support platform) |
| **Author** | Nikhil Maguwala |
| **UI design** | [Stitch by Google](https://stitch.withgoogle.com) |
| **Repository** | https://github.com/nikhilmaguwala/enterprise-ai-agent |
| **Live web app** | https://enterprise-ai-support-agent.vercel.app |
| **Live API** | https://enterprise-ai-support-agent.fastapicloud.dev |

**Short description (for GitHub About):**

> Multi-tenant AI support agent with LangGraph, RAG, human-in-the-loop approvals, and a ResolveAI console. UI designed in Google Stitch. FastAPI + Next.js + Neon + Qdrant.

**GitHub About → Website URL:** `https://enterprise-ai-support-agent.vercel.app`

---

## What it does

ResolveAI is a **B2B customer-support platform** for e-commerce (demo domain: order delays and address changes).

| Stakeholder | Experience |
| --- | --- |
| **Customer** | Chats about their order; gets answers with **policy citations**, not guesses |
| **Support agent** | Handles escalations in an inbox; approves or rejects risky actions |
| **Admin** | Invites teammates, uploads knowledge docs, monitors jobs and evals |

Built and deployed end-to-end by **[Nikhil Maguwala](#author)** — backend, AI agent, frontend, CI/CD, evals, and docs.

---

## UI design

The **ResolveAI console** UI was designed with **[Stitch by Google Labs](https://stitch.withgoogle.com)** — Google's AI-native design canvas — then implemented in code as a production Next.js app.

| | |
| --- | --- |
| **Design tool** | [Stitch (Google Labs)](https://stitch.withgoogle.com) |
| **Learn more** | [Google blog: Stitch AI UI design](https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-ai-ui-design/) |
| **Implementation** | Next.js App Router · Tailwind CSS 4 · Geist font · Lucide icons |
| **Screens** | Chat, inbox, knowledge, team invites, ops, evals, architecture view |

**Design → code flow:**

```
  ┌──────────────────────┐      ┌──────────────────────┐      ┌─────────────────────────────┐
  │  Stitch by Google    │ ───▶ │  Next.js build       │ ───▶ │  ResolveAI live console     │
  │  UI prototypes       │      │  Tailwind + Geist    │      │  chat · inbox · admin       │
  └──────────────────────┘      └──────────────────────┘      └─────────────────────────────┘
```

---

## How it works

### The happy path (4 steps)

| Step | Who | What happens |
| :---: | --- | --- |
| **1** | Customer | Asks a question — *"Why is my order late?"* |
| **2** | Agent | Researches using **RAG** (policy) + **CRM/ERP** (order) + **carrier** (tracking) |
| **3** | User | Sees an **approval card** in chat and approves or rejects the action |
| **4** | System | Writes **once** to ERP (idempotent) · verifies · logs audit trail |

```
  ASK  ──────▶  RESEARCH  ──────▶  APPROVE  ──────▶  WRITE ONCE
  user          RAG + tools         HITL gate          idempotent ERP
```

### Message flow (what happens on each chat send)

| # | From | To | Action |
| :---: | --- | --- | --- |
| 1 | User | Web UI | Types message in `/chat` |
| 2 | Web UI | FastAPI | `POST /conversations/{id}/messages` |
| 3 | FastAPI | LangGraph | Runs agent turn |
| 4 | Agent | Postgres + Qdrant | Loads order + searches policy |
| 5 | Agent | FastAPI | Returns grounded reply + citations |
| 6 | FastAPI | Web UI | Streams SSE events (tools, message, approval) |
| 7 | User | Web UI | Approves mutation if required |
| 8 | Agent | Mock ERP | Executes + verifies + audit |

---

## Architecture

```
                         ┌─────────────────────────────────────────┐
                         │           USERS (browser)               │
                         └────────────────────┬────────────────────┘
                                              │
                         ┌────────────────────▼────────────────────┐
  FRONTEND (Vercel)      │  Next.js ResolveAI console              │
                         │  chat · inbox · knowledge · admin       │
                         └────────────────────┬────────────────────┘
                                              │  /api/v1 proxy + SSE
                         ┌────────────────────▼────────────────────┐
  BACKEND (FastAPI Cloud)│  FastAPI API                            │
                         │  auth · conversations · approvals       │
                         │  LangGraph agent · policy engine        │
                         └───┬─────────┬─────────┬─────────┬───────┘
                             │         │         │         │
              ┌──────────────┘         │         │         └──────────────┐
              ▼                        ▼         ▼                        ▼
       ┌────────────┐           ┌──────────┐ ┌─────────┐           ┌────────────┐
       │ Neon       │           │ Qdrant   │ │ Groq /  │           │ Mock CRM   │
       │ Postgres   │           │ vectors  │ │ Gemini  │           │ ERP carrier│
       └────────────┘           └──────────┘ └─────────┘           │ Brevo mail │
                                                                    └────────────┘
```

| Layer | Folder / host | Role |
| --- | --- | --- |
| **UI** | `apps/web` · Vercel | Chat, inbox, knowledge, admin screens |
| **API** | `apps/api` · FastAPI Cloud | Auth, conversations, approvals, jobs |
| **Agent** | `packages/agent` | LangGraph workflow + tool calls |
| **RAG** | `packages/knowledge` | Ingest docs, tenant-filtered search |
| **Integrations** | `packages/integrations` | HTTP clients for enterprise mocks |

---

## Features

### Platform capabilities

| Area | Includes |
| --- | --- |
| **Identity** | Signup · login · team invites · RBAC · tenant isolation tests |
| **Agent** | 13-node LangGraph · tool calling · human approval · SSE streaming |
| **Knowledge** | PDF upload · chunk · embed · citations in chat |
| **Reliability** | Idempotency keys · job queue · audit log · usage quotas |

---

### Application screens

| Screen | Path | Who can access |
| --- | --- | --- |
| Sign up / Log in | `/signup` `/login` | Everyone |
| Conversations | `/chat` | All roles |
| Support inbox | `/inbox` | Agent, supervisor, admin |
| Knowledge base | `/knowledge` | Agent+ |
| Team invites | `/team/invite` | Admin |
| Operations | `/operations` | Admin |
| Evaluations | `/evaluations` | Supervisor+ |
| Run inspector | `/runs/[id]` | All roles |

### Role permissions

| | Chat | Inbox | Knowledge | Evals | Ops | Invite |
| ---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Customer | ✓ | | | | | |
| Agent | ✓ | ✓ | ✓ | | | |
| Supervisor | ✓ | ✓ | ✓ | ✓ | | |
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## Agent pipeline

The agent runs a **13-node LangGraph** workflow in three phases:

| Phase | Nodes | Purpose |
| --- | --- | --- |
| **1 — Understand** | Auth · classify intent · load customer · load order | Know who is asking and about which order |
| **2 — Research** | RAG policy · carrier check · grounded reply | Answer with evidence and citations |
| **3 — Act safely** | Validate · approve · execute · verify · or escalate | Mutations only after human approval |

```
  UNDERSTAND  ──▶  RESEARCH  ──▶  ACT SAFELY
  auth + order     RAG + carrier   approve → write → verify
                                   └─ unsafe? → escalate to inbox
```

### Knowledge ingestion (RAG)

| Step | Action |
| :---: | --- |
| 1 | Upload PDF |
| 2 | Validate MIME + checksum |
| 3 | Extract text |
| 4 | Chunk by section |
| 5 | Embed vectors |
| 6 | Store in Qdrant (with `organization_id`) |
| 7 | Retrieve on user question → cite in answer |

```
  Upload → Validate → Extract → Chunk → Embed → Qdrant → Cite in chat
```

---

## Repository layout

```
enterprise-ai-agent/
├── apps/
│   ├── api/          ← FastAPI backend, Alembic, tests
│   └── web/          ← Next.js ResolveAI UI
├── packages/
│   ├── agent/        ← LangGraph workflow
│   ├── knowledge/    ← RAG pipeline
│   ├── integrations/ ← CRM, ERP, carrier, ticketing clients
│   ├── domain/       ← Policy engine, classifiers
│   └── observability/
├── services/         ← Local mock microservices (Docker)
├── evals/            ← 60 test cases + graders
├── docs/             ← Architecture, ADRs, runbooks
└── scripts/          ← Dev and deploy helpers
```

---

## Tech stack

**Stack at a glance:**

| Layer | Host | Key technologies |
| --- | --- | --- |
| **UI design** | [Stitch by Google](https://stitch.withgoogle.com) | Prototypes → Next.js implementation |
| **Frontend** | Vercel | Next.js 16 · React 19 · TypeScript · Tailwind 4 |
| **Backend** | FastAPI Cloud | FastAPI · LangGraph · SQLAlchemy 2 · Alembic |
| **Database** | Neon | PostgreSQL · asyncpg |
| **Vector DB** | Qdrant Cloud | Tenant-scoped RAG embeddings |
| **LLM** | Groq + Gemini | Agent reasoning and tool use |
| **Email** | Brevo | Team invites and notifications |
| **CI/CD** | GitHub Actions | Test · lint · deploy |

```
  Stitch ──▶ Next.js (Vercel) ──▶ FastAPI (Cloud) ──▶ Neon Postgres
                                        │                    │
                                        ├── Qdrant (RAG)     │
                                        ├── Groq / Gemini      │
                                        └── Brevo email        │
```

Full breakdown by layer — what runs where:

### UI and design

| Tool | Purpose |
| --- | --- |
| [Stitch by Google](https://stitch.withgoogle.com) | AI UI design and prototyping (ResolveAI theme) |
| [Geist](https://vercel.com/font) | Typography |
| [Lucide React](https://lucide.dev/) | Icons |
| [Tailwind CSS 4](https://tailwindcss.com/) | Layout and styling |
| [Mermaid](https://mermaid.js.org/) | In-app architecture diagram |

### Frontend (`apps/web`)

| Category | Technologies |
| --- | --- |
| **Framework** | Next.js 16.3 · React 19 · TypeScript 5 |
| **Styling** | Tailwind CSS 4 · PostCSS · clsx |
| **Data / forms** | TanStack Query 5 · Zod 4 |
| **Content** | react-markdown · remark-gfm |
| **Package manager** | pnpm 9 |
| **Lint** | ESLint 9 · eslint-config-next |

### Backend API (`apps/api`)

| Category | Technologies |
| --- | --- |
| **Runtime** | Python 3.12 · uv |
| **Web** | FastAPI · Uvicorn · sse-starlette |
| **ORM / DB** | SQLAlchemy 2 async · asyncpg · Alembic |
| **Validation** | Pydantic v2 · pydantic-settings · email-validator |
| **Auth** | bcrypt · python-jose (JWT) |
| **HTTP** | httpx · python-multipart |
| **PDF / storage** | pypdf · firebase-admin |
| **Resilience** | tenacity |
| **Logging / metrics** | structlog · opentelemetry-api · prometheus-client |
| **Lint / test** | ruff · mypy · pytest · pytest-asyncio |

### AI and agent (`packages/agent`)

| Category | Technologies |
| --- | --- |
| **Orchestration** | LangGraph · LangChain Core |
| **Primary LLM** | Groq (`openai/gpt-oss-20b`) |
| **Fallback LLM** | Google Gemini |
| **Local dev LLM** | Ollama |
| **Streaming** | Server-Sent Events to frontend |

### Shared packages

| Package | Role |
| --- | --- |
| `packages/domain` | Policy engine · intent classification · chunking |
| `packages/knowledge` | RAG ingestion · Qdrant retrieval |
| `packages/integrations` | CRM · ERP · carrier · ticketing HTTP clients |
| `packages/observability` | Logging and metrics helpers |

### Database

| Store | Technology | Used for |
| --- | --- | --- |
| **Primary DB** | [Neon](https://neon.tech) PostgreSQL | Users, orgs, conversations, approvals, jobs, audit |
| **Driver** | SQLAlchemy 2 + asyncpg | Async queries and migrations |
| **Migrations** | Alembic | Schema versioning |
| **Local dev** | Docker Postgres (optional) | `infra/docker-compose.yml` |

### Vector database (RAG)

| Store | Technology | Used for |
| --- | --- | --- |
| **Vector index** | [Qdrant Cloud](https://qdrant.tech) | Policy document embeddings |
| **Client** | qdrant-client | Tenant-filtered hybrid search |
| **Local dev** | Docker Qdrant (optional) | Compose stack |

### Cache and queue (optional)

| Store | Technology | Used for |
| --- | --- | --- |
| **Redis** | [Upstash Redis](https://upstash.com) REST | Rate limits · ephemeral locks |
| **Jobs** | Postgres SKIP LOCKED | Durable background job queue |

### Object storage

| Backend | Technology | Used for |
| --- | --- | --- |
| **Production option** | Firebase Storage | Knowledge PDF uploads |
| **Alternative** | Cloudflare R2 | Document storage |
| **Local dev** | MinIO / filesystem | `OBJECT_STORAGE_BACKEND=filesystem` |

### Email and auth

| Service | Technology | Used for |
| --- | --- | --- |
| **Email** | [Brevo](https://www.brevo.com) | Team invites · notifications |
| **Production auth** | JWT + bcrypt | Signup · login · API bearer tokens |
| **Enterprise auth** | Auth0 OIDC (configured) | Optional SSO path |

### Integrations (demo)

| Service | Type | Purpose |
| --- | --- | --- |
| Mock CRM | HTTP (`services/mock-crm`) | Customer lookup |
| Mock ERP | HTTP (`services/mock-erp`) | Orders · address changes |
| Mock carrier | HTTP (`services/mock-carrier`) | Shipment tracking |
| Mock ticketing | HTTP (`services/mock-ticketing`) | Escalations |
| Embedded mocks | FastAPI routes | FastAPI Cloud deploy without extra containers |

### Observability (optional)

| Tool | Purpose |
| --- | --- |
| structlog | Structured JSON logs |
| OpenTelemetry | Trace hooks |
| Prometheus client | Metrics endpoints |
| [Langfuse](https://langfuse.com) | LLM tracing |
| Sentry | Error reporting |

### DevOps, CI/CD, and hosting

| Layer | Technologies |
| --- | --- |
| **CI** | GitHub Actions · gitleaks · ruff · pytest · ESLint |
| **Deploy** | Vercel (frontend) · FastAPI Cloud (API) |
| **Containers** | Docker · Docker Compose (local mocks + infra) |
| **Monorepo** | uv workspace · `scripts/prepare-fastapi-cloud.sh` |

### Quality and evals

| Tool | Purpose |
| --- | --- |
| pytest (24 tests) | Unit + tenant isolation integration |
| `evals/` (60 cases) | Deterministic graders · grounding · injection tests |
| gitleaks | Secret scanning on PRs |

---

## Quick start

```bash
git clone https://github.com/nikhilmaguwala/enterprise-ai-agent.git
cd enterprise-ai-agent
cp .env.example .env    # add Neon, Qdrant, Groq keys
make setup
make dev                # API + web + mocks
```

Open **http://localhost:3000**

| Command | What it runs |
| --- | --- |
| `make test` | 24 pytest tests |
| `make eval` | 60-case eval smoke |
| `make lint` | Python + TypeScript lint |

**Try the demo** (`DEV_AUTH_ENABLED=true`): log in as `customer@acme-demo.test`, order `ACM-10001`

**Try real signup:** `/signup` → your org + order `ORD-XXXXXX` → `/chat`

---

## Tests & quality

**CI/CD pipeline:**

| Stage | Trigger | Runs |
| --- | --- | --- |
| PR check | Pull request | Lint · pytest · gitleaks |
| Main check | Merge to `main` | Full suite · 60 eval cases |
| Deploy | After main passes | Vercel + FastAPI Cloud |

**Eval dataset (60 cases):**

| Category | Cases |
| --- | ---: |
| Policy / grounding | 20 |
| Order / shipment | 15 |
| Address change | 10 |
| Prompt injection | 5 |
| Missing evidence | 5 |
| Dependency failure | 5 |

| Metric | Count |
| --- | ---: |
| Pytest tests | 24 |
| Eval cases | 60 |
| LangGraph nodes | 13 |
| UI routes | 12 |
| Architecture ADRs | 11 |

---

## Documentation

| Document | Description |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | System design and diagrams |
| [docs/deployment.md](docs/deployment.md) | Hosting setup guide |
| [docs/threat-model.md](docs/threat-model.md) | Security threats and mitigations |
| [docs/demo-script.md](docs/demo-script.md) | Step-by-step demo script |
| [docs/adr/](docs/adr/) | Architecture decision records |
| [docs/runbooks/](docs/runbooks/) | Operational runbooks |

---

## SaaS scope (honest)

**Implemented:** multi-tenancy, signup, invites, RBAC, RAG, approvals, idempotency, audit, quotas, CI/CD.

**Not implemented:** Stripe billing, enterprise SSO in production, live Salesforce/SAP connectors, SOC2.

---

## Public repo safety

Secrets are **not** in git (`.env` and Firebase JSON are gitignored). CI runs gitleaks.  
See [LICENSE](LICENSE) (MIT). Demo data is synthetic.

<details>
<summary>Pre-public audit checklist</summary>

| Check | Status |
| --- | --- |
| API keys in tracked files | None |
| Firebase credentials in git | Never committed |
| Tests on main | 24 passing |

Rotate Neon, Qdrant, Groq, Brevo, and Firebase credentials after open-sourcing as a precaution.

</details>

---

<div align="center">

## Author

**Nikhil Maguwala**

Full-stack: system design · multi-tenant API · LangGraph agent · RAG · HITL approvals · Next.js UI · evals · CI/CD

<br />

Portfolio project · MIT License · synthetic demo data only

</div>
