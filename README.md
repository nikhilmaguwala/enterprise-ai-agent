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

<br />

**[What it does](#what-it-does)** · **[UI design](#ui-design)** · **[How it works](#how-it-works)** · **[Architecture](#architecture)** · **[Tech stack](#tech-stack)** · **[Quick start](#quick-start)**

</div>

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

```mermaid
flowchart LR
  STITCH["Stitch by Google<br/>UI prototypes"] --> NEXT["Next.js implementation"]
  NEXT --> UI["ResolveAI console<br/>chat · inbox · admin"]

  classDef design fill:#fef3c7,stroke:#d97706
  classDef code fill:#dbeafe,stroke:#2563eb
  class STITCH design
  class NEXT,UI code
```

---

## How it works

### The happy path (read this first)

```mermaid
flowchart LR
  classDef step fill:#eff6ff,stroke:#3b82f6,stroke-width:2px
  classDef gate fill:#fef3c7,stroke:#d97706,stroke-width:2px
  classDef done fill:#ecfdf5,stroke:#059669,stroke-width:2px

  A["1. User asks<br/>Why is my order late?"]:::step
  B["2. Agent researches<br/>RAG + CRM + carrier tools"]:::step
  C["3. User approves<br/>Address change card"]:::gate
  D["4. System writes once<br/>Idempotent ERP update"]:::done

  A --> B --> C --> D
```

### End-to-end request flow

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant UI as Next.js UI
  participant API as FastAPI
  participant Agent as LangGraph
  participant Data as Postgres + Qdrant

  User->>UI: Send message
  UI->>API: POST /conversations/.../messages
  API->>Agent: Run agent turn
  Agent->>Data: Policy RAG + order lookup
  Agent-->>API: Reply + citations
  API-->>UI: SSE tool progress + message
  UI-->>User: Grounded answer

  Note over User,Agent: If mutation needed
  Agent-->>UI: Approval card
  User->>UI: Approve
  UI->>API: POST /approvals/.../approve
  Agent->>API: Execute + verify + audit
```

---

## Architecture

```mermaid
flowchart TB
  classDef fe fill:#ede9fe,stroke:#7c3aed
  classDef be fill:#dbeafe,stroke:#2563eb
  classDef store fill:#d1fae5,stroke:#059669
  classDef ext fill:#f3f4f6,stroke:#6b7280

  U([Users]) --> FE

  subgraph FE [Frontend]
    WEB[Next.js console on Vercel]:::fe
  end

  subgraph BE [Backend]
    API[FastAPI REST + SSE]:::be
    AG[LangGraph agent]:::be
  end

  subgraph STORE [Data layer]
    PG[(Postgres)]:::store
    VEC[(Qdrant vectors)]:::store
  end

  subgraph EXT [External]
    LLM[LLM Groq Gemini]:::ext
    TOOLS[Mock CRM ERP carrier]:::ext
    MAIL[Email Brevo]:::ext
  end

  WEB -->|/api/v1 proxy| API
  API --> AG
  AG --> LLM
  AG --> TOOLS
  API --> PG
  API --> VEC
  API --> MAIL
  WEB -. SSE .-> API
```

| Layer | Location | Role |
| --- | --- | --- |
| **UI** | `apps/web` | Chat, inbox, knowledge, admin screens |
| **API** | `apps/api` | Auth, conversations, approvals, jobs |
| **Agent** | `packages/agent` | LangGraph workflow + tool calls |
| **RAG** | `packages/knowledge` | Ingest docs, search with tenant filter |
| **Integrations** | `packages/integrations` | HTTP clients for enterprise mocks |

---

## Features

### Platform capabilities

```mermaid
flowchart TB
  ROOT[ResolveAI platform]

  ROOT --> ID[Identity signup invites RBAC]
  ROOT --> AG[Agent LangGraph tools approvals]
  ROOT --> KN[Knowledge RAG citations]
  ROOT --> RL[Reliability jobs audit quotas]

  ID --- ID1[Tenant isolation tests]
  AG --- AG1[SSE streaming]
  KN --- KN1[PDF ingest pipeline]
  RL --- RL1[Idempotency keys]
```

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

The agent runs a **13-node LangGraph** workflow. Grouped for readability:

```mermaid
flowchart TB
  classDef phase fill:#f8fafc,stroke:#64748b

  subgraph P1 [Understand]
    direction TB
    A1[Auth + context]:::phase
    A2[Classify intent]:::phase
    A3[Load customer and order]:::phase
  end

  subgraph P2 [Research]
    direction TB
    B1[Retrieve policy RAG]:::phase
    B2[Check carrier status]:::phase
    B3[Write grounded reply]:::phase
  end

  subgraph P3 [Act safely]
    direction TB
    C1[Validate action]:::phase
    C2{Needs mutation?}
    C3[Request approval]:::phase
    C4[Execute idempotent write]:::phase
    C5[Verify result]:::phase
  end

  P1 --> P2 --> P3
  C2 -->|no| OUT[Reply only]
  C2 -->|yes| C3 --> C4 --> C5 --> OUT
  C2 -->|unsafe| ESC[Escalate to inbox]
```

### Knowledge ingestion (RAG)

```mermaid
flowchart LR
  U[Upload PDF] --> V[Validate file]
  V --> E[Extract text]
  E --> C[Chunk sections]
  C --> M[Embed]
  M --> Q[(Qdrant)]
  Q --> R[Retrieve on question]
  R --> S[Cite in answer]
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

Full breakdown by layer — what runs where:

```mermaid
flowchart TB
  subgraph DESIGN [Design]
    ST[Stitch by Google]
  end

  subgraph FE [Frontend - Vercel]
    NJS[Next.js 16 React 19]
    TW[Tailwind CSS 4]
  end

  subgraph BE [Backend - FastAPI Cloud]
    FA[FastAPI Uvicorn]
    LG[LangGraph agent]
  end

  subgraph DATA [Data]
    PG[(Neon Postgres)]
    QD[(Qdrant Cloud)]
    RD[(Upstash Redis)]
  end

  subgraph AI [AI and email]
    GQ[Groq Gemini]
    BR[Brevo email]
  end

  ST -. UI specs .-> NJS
  NJS --> FA
  FA --> LG
  FA --> PG
  FA --> QD
  FA --> RD
  LG --> GQ
  FA --> BR
```

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

```mermaid
flowchart LR
  PR[Pull request] --> CI[Lint + test + gitleaks]
  MAIN[Merge to main] --> FULL[Full suite + evals]
  FULL --> DEPLOY[Deploy Vercel + FastAPI Cloud]
```

```mermaid
pie title Eval dataset by category
  "Policy" : 20
  "Orders" : 15
  "Address change" : 10
  "Prompt injection" : 5
  "Missing evidence" : 5
  "Dependency failure" : 5
```

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
