# ResolveAI — Enterprise AI Support Agent

**Portfolio project · Full-stack multi-tenant AI support platform**

A production-deployed B2B support agent for e-commerce operations. It grounds answers in tenant policy (RAG), calls enterprise systems through typed tools, requires human approval before mutations, executes writes idempotently, and records a full audit trail.

> **For reviewers:** Start with [System overview](#system-overview) and [LangGraph agent workflow](#langgraph-agent-workflow), then [Project scope](#project-scope).

---

## At a glance

```mermaid
flowchart LR
  subgraph Problem
    P1[Order delay questions]
    P2[Address change requests]
    P3[Policy must be cited]
    P4[Mutations must be safe]
  end

  subgraph Solution
    S1[Multi-tenant API]
    S2[LangGraph agent]
    S3[RAG + tools]
    S4[HITL approvals]
  end

  subgraph Proof
    T1[24 pytest tests]
    T2[60 eval cases]
    T3[CI + deploy]
  end

  Problem --> Solution --> Proof
```

| | |
| --- | --- |
| **Problem** | Explain order issues with evidence; change addresses safely — no hallucinated policy, no double mutations. |
| **Approach** | FastAPI monolith + LangGraph + Next.js console, multi-tenant from day one. |
| **Domain** | Fictional e-commerce (delays, address changes, escalations). |
| **Hosting** | Vercel · FastAPI Cloud · Neon · Qdrant · Groq |
| **Docs** | Architecture · 11 ADRs · threat model · runbooks |

---

## System overview

```mermaid
flowchart TB
  User([Customer / Agent / Admin])
  Web[Next.js on Vercel]
  Proxy["/api/v1 proxy"]
  API[FastAPI Cloud API]
  PG[(Neon Postgres)]
  QD[(Qdrant Cloud)]
  LLM[Groq / Gemini]
  Store[(Object storage)]
  Email[Brevo]
  Mocks[CRM · ERP · Carrier · Ticketing]

  User --> Web
  Web --> Proxy --> API
  API --> PG
  API --> QD
  API --> LLM
  API --> Store
  API --> Email
  API --> Mocks
  Web -. SSE events .-> API
```

---

## Monorepo map

```mermaid
flowchart TB
  Root[enterprise-ai-agent]

  Root --> Apps
  Root --> Packages
  Root --> Services
  Root --> Evals

  subgraph Apps
    API[apps/api<br/>FastAPI · Alembic · tests]
    WEB[apps/web<br/>Next.js ResolveAI UI]
  end

  subgraph Packages
    DOM[domain<br/>policy engine]
    AGT[agent<br/>LangGraph]
    KNO[knowledge<br/>RAG]
    INT[integrations<br/>tool clients]
    OBS[observability]
  end

  subgraph Services
    CRM[mock-crm]
    ERP[mock-erp]
    CAR[mock-carrier]
    TKT[mock-ticketing]
  end

  Evals[evals/<br/>60 cases · graders]

  API --> Packages
  AGT --> INT
  AGT --> KNO
  AGT --> DOM
```

---

## LangGraph agent workflow

13-node graph (`packages/agent`, `graph_version=v1`):

```mermaid
flowchart TD
  A[authenticate_and_load_context] --> B{classified?}
  B -->|no| Z[finalize_response]
  B -->|yes| C[classify_intent]
  C --> D[load_customer]
  D --> E[load_order]
  E --> F[retrieve_policy]
  F --> G[check_delivery]
  G --> H[compose_grounded_explanation]
  H --> I[validate_proposed_action]
  I -->|approve path| J[request_human_approval]
  I -->|escalate| K[create_escalation]
  I -->|info only| Z
  J --> L{approved?}
  L -->|pending| Z
  L -->|yes| M[execute_approved_action]
  M --> N[verify_action_result]
  N --> Z
  K --> Z
```

---

## Human-in-the-loop approval

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant UI as Next.js /chat
  participant API as FastAPI
  participant Graph as LangGraph
  participant ERP as Mock ERP

  User->>UI: Ask to change shipping address
  UI->>API: POST /conversations/{id}/messages
  API->>Graph: Run turn
  Graph->>ERP: GET order
  Graph->>API: Persist approval (paused)
  API-->>UI: SSE approval_required
  UI-->>User: Approval card
  User->>UI: Approve
  UI->>API: POST /approvals/{id}/approve
  API->>Graph: Resume + revalidate
  Graph->>ERP: POST address change (Idempotency-Key)
  Graph->>ERP: GET order verify
  Graph->>API: Final assistant message + audit
  API-->>UI: SSE message_completed
```

---

## RAG ingestion pipeline

```mermaid
flowchart LR
  U[Upload PDF] --> P[Presign + validate MIME]
  P --> J[Enqueue extract job]
  J --> X[Extract text]
  X --> C[Chunk sections]
  C --> E[Embed vectors]
  E --> Q[Upsert Qdrant<br/>organization_id filter]
  Q --> R[Retrieve at query time]
  R --> M[Citations in chat]
```

---

## Multi-tenancy & roles

```mermaid
flowchart TB
  subgraph Tenant A
    OA[Organization A]
    UA1[Admin]
    UA2[Agent]
    UA3[Customer]
    DA[Data + RAG index A]
  end

  subgraph Tenant B
    OB[Organization B]
    UB1[Admin]
    UB2[Customer]
    DB[Data + RAG index B]
  end

  JWT[JWT carries org_id from membership]
  JWT --> Tenant A
  JWT --> Tenant B

  UA3 -->|cannot read| DB
  UB2 -->|cannot read| DA
```

| Role | Chat | Inbox | Knowledge | Evals | Ops | Invite |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Customer | ✓ | | | | | |
| Agent | ✓ | ✓ | ✓ | | | |
| Supervisor | ✓ | ✓ | ✓ | ✓ | | |
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

---

## User journeys

### Real signup → first conversation

```mermaid
journey
  title New workspace onboarding
  section Signup
    Visit /signup: 5: User
    Create org + admin + order ORD-XXXXXX: 5: API
  section Chat
    Open /chat (Live mode): 5: User
    Ask about order delay: 4: User
    Agent cites policy + order status: 5: Agent
  section Team
    Admin invites agent at /team/invite: 5: Admin
    Agent logs in via email: 5: Agent
```

### Local demo (dev only)

| Role | Email | Org |
| --- | --- | --- |
| Customer | `customer@acme-demo.test` | Acme Retail |
| Agent | `agent@acme-demo.test` | Acme Retail |
| Admin | `admin@acme-demo.test` | Acme Retail |

Demo order: `ACM-10001` · set `DEV_AUTH_ENABLED=true`

---

## Project scope

I designed and built this end to end as a **portfolio-grade enterprise AI application**, not a thin chat wrapper.

| Layer | What I shipped |
| --- | --- |
| **Backend** | Multi-tenant Postgres, JWT auth, signup/login/invites, quotas, idempotency, job queue, audit log |
| **Agent** | LangGraph 13-node workflow, tool gateway, SSE streaming, Groq/Gemini providers |
| **RAG** | Upload pipeline, Qdrant with tenant filters, inline citations |
| **Frontend** | ResolveAI console — 12 routes, role nav, approval cards, run inspector |
| **Quality** | 24 pytest tests, 60-case eval suite, gitleaks, CI on every PR |
| **Ops** | GitHub Actions deploy to Vercel + FastAPI Cloud, Alembic migrations |
| **Docs** | Architecture, ADRs, threat model, runbooks, deployment guide |

### Frontend routes

| Route | Access | Purpose |
| --- | --- | --- |
| `/signup`, `/login` | Public | Workspace registration |
| `/chat` | All | Streaming chat + approvals |
| `/inbox` | Agent+ | Escalations |
| `/knowledge` | Agent+ | Document upload |
| `/evaluations` | Supervisor+ | Eval dashboard |
| `/operations` | Admin | Job queue health |
| `/team/invite` | Admin | Team invites |
| `/runs/[id]` | All | Agent run inspector |
| `/architecture` | All | In-app diagram |

---

## CI/CD pipeline

```mermaid
flowchart LR
  PR[Pull request] --> CI[ci.yml<br/>lint · test · gitleaks]
  Main[Push to main] --> Tests[main.yml<br/>full suite · eval smoke]
  Tests --> Deploy[deploy.yml]
  Deploy --> API[FastAPI Cloud]
  Deploy --> Web[Vercel]
```

---

## Eval coverage

60 deterministic cases in `evals/datasets/cases.jsonl`:

```mermaid
pie showData
  title Eval case categories (60 total)
  "Policy / grounding" : 20
  "Order / shipment" : 15
  "Address change" : 10
  "Prompt injection" : 5
  "Missing evidence" : 5
  "Dependency failure" : 5
```

Categories include grounding checks, forbidden-tool guards, approval behavior, and injection resistance.

---

## SaaS maturity

Architecturally **SaaS-grade** for portfolio / pilot — **not** a commercial SaaS business yet.

```mermaid
flowchart TB
  subgraph Done["Implemented (core SaaS patterns)"]
    D1[Multi-tenant model]
    D2[Signup · login · invites]
    D3[RBAC + tenant isolation tests]
    D4[RAG + citations]
    D5[HITL approvals]
    D6[Idempotency + audit log]
    D7[Job queue + CI/CD deploy]
  end

  subgraph Next["Not built yet (commercial SaaS)"]
    N1[Stripe billing]
    N2[Enterprise SSO in prod]
    N3[Live CRM / ERP APIs]
    N4[SOC2 / compliance pack]
  end
```

| Capability | Status |
| --- | --- |
| Multi-tenant model, signup, invites, RBAC | **Done** |
| RAG, HITL, idempotency, audit, quotas | **Done** |
| Production deploy + CI/CD | **Done** |
| Billing / Stripe | Not built |
| Enterprise SSO in prod | Auth0 wired; JWT auth in prod |
| Live CRM/ERP | Mock HTTP services |
| SOC2 | Threat model + runbooks only |

---

## Engineering highlights

1. **Multi-tenancy** — org from JWT membership, not request body; isolation tests in CI  
2. **Safe agent actions** — policy engine + approval gate before ERP mutations  
3. **Production patterns** — idempotency, audit log, job queue, SSE, API proxy  
4. **Monorepo packages** — domain, agent, knowledge, integrations, observability  
5. **Eval-driven QA** — 60 labeled cases, deterministic graders  
6. **Honest scope** — mocks documented; gaps listed above  

---

## Tech stack

```mermaid
mindmap
  root((ResolveAI))
    Backend
      FastAPI
      SQLAlchemy 2
      Alembic
      Pydantic v2
    Agent
      LangGraph
      Groq
      Gemini
    Frontend
      Next.js 16
      React 19
      TanStack Query
      Tailwind 4
    Data
      Neon Postgres
      Qdrant
      Redis optional
    Ops
      GitHub Actions
      Vercel
      FastAPI Cloud
```

---

## API modules

| Module | Endpoints |
| --- | --- |
| Auth | register · login · invite · me |
| Conversations | threads · messages · SSE events |
| Approvals | get · approve · reject |
| Knowledge | presign · upload · ingest · list |
| Inbox | escalations |
| Operations | dashboard · job replay |
| Evaluations | runs · dashboard |
| Audit | append-only log |
| Jobs | queue · HMAC drain |

OpenAPI: `/docs` on running API.

---

## Run locally

```bash
cp .env.example .env
make setup    # deps, migrate, seed
make dev      # API + web + mocks
make test     # 24 pytest tests
make eval     # eval smoke
```

---

## Deploy

Push to `main` → `.github/workflows/deploy.yml` → FastAPI Cloud + Vercel.

**Secrets:** `FASTAPI_CLOUD_TOKEN`, `FASTAPI_CLOUD_APP_ID`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`  
**Variables:** `PUBLIC_API_URL`, `PUBLIC_APP_URL`

Details: [docs/deployment.md](docs/deployment.md)

---

## Security model

```mermaid
flowchart LR
  T[Tenant spoofing] --> M1[JWT org from membership]
  I[Prompt injection] --> M2[RBAC outside LLM]
  D[Double mutation] --> M3[Idempotency keys]
  L[Secret leak] --> M4[gitleaks + gitignore]
  C[Cost abuse] --> M5[Daily quotas]
```

Full write-up: [docs/threat-model.md](docs/threat-model.md)

---

## Results

```mermaid
flowchart LR
  subgraph Quality metrics
    M1["24<br/>pytest tests"]
    M2["60<br/>eval cases"]
    M3["11<br/>ADRs"]
    M4["12<br/>UI routes"]
    M5["13<br/>graph nodes"]
  end
```

| Metric | Value |
| --- | --- |
| Pytest | 24 passing |
| Eval dataset | 60 cases · 6 categories |
| CI | Green on main |
| Documentation | Architecture + 11 ADRs + runbooks |

---

## Documentation index

| Doc | Contents |
| --- | --- |
| [docs/architecture.md](docs/architecture.md) | C4 · agent · RAG diagrams |
| [docs/threat-model.md](docs/threat-model.md) | Threats + mitigations |
| [docs/deployment.md](docs/deployment.md) | Hosting setup |
| [docs/adr/](docs/adr/) | Architecture decisions |
| [docs/runbooks/](docs/runbooks/) | Incident runbooks |
| [docs/demo-script.md](docs/demo-script.md) | Live demo script |

---

## Author

**Nikhil Maguwala**

Full-stack build: system design, multi-tenant backend, LangGraph agent, RAG pipeline, human-in-the-loop approvals, durable jobs, ResolveAI frontend, evaluation harness, CI/CD, and technical documentation.

---

## License

See repository license file. Demo data is synthetic; do not use production PII.
