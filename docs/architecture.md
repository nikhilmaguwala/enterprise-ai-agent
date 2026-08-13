# Architecture — Enterprise AI Support Agent

## Product context

A multi-tenant AI support agent for a fictional e-commerce company. Primary demo: explain an order delay with grounded citations, then propose an address change that requires explicit human approval, single-execution idempotent mutation, verification, and full audit trail.

## System context

```mermaid
C4Context
title System Context
Person(customer, "Customer")
Person(agent, "Support Agent")
Person(admin, "Administrator")
System(app, "Enterprise AI Support Agent")
System_Ext(auth0, "Auth0")
System_Ext(groq, "Groq LLM")
System_Ext(neon, "Neon Postgres")
System_Ext(qdrant, "Qdrant Cloud")
System_Ext(crm, "Mock CRM")
System_Ext(erp, "Mock ERP")
System_Ext(carrier, "Mock Carrier")
System_Ext(tickets, "Mock Ticketing")
Rel(customer, app, "Chat / approve")
Rel(agent, app, "Inbox / escalate")
Rel(admin, app, "Knowledge / audit")
Rel(app, auth0, "OIDC JWT")
Rel(app, groq, "Tool calling")
Rel(app, neon, "System of record")
Rel(app, qdrant, "Tenant-filtered RAG")
Rel(app, crm, "HTTP tools")
Rel(app, erp, "HTTP tools")
Rel(app, carrier, "HTTP tools")
Rel(app, tickets, "HTTP handoffs")
```

## Containers

```mermaid
flowchart LR
  Web[Next.js Web / Vercel]
  API[FastAPI Modular Monolith / FastAPI Cloud]
  PG[(Neon PostgreSQL)]
  QD[(Qdrant)]
  Redis[(Upstash Redis)]
  R2[(R2 / MinIO)]
  Mocks[Mock CRM ERP Carrier Ticketing]
  Web -->|JWT + SSE| API
  API --> PG
  API --> QD
  API --> Redis
  API --> R2
  API --> Mocks
```

## Modular monolith modules

| Module | Responsibility |
| --- | --- |
| Identity & tenancy | OIDC validation, memberships, RBAC, trusted tenant context |
| Conversations | Threads, messages, SSE event persistence |
| Agent orchestration | LangGraph workflow, pauses for approval |
| Knowledge | Ingestion, chunking, embeddings, hybrid retrieval |
| Integrations | Typed tool gateway to mock enterprise APIs |
| Approvals | Deterministic validation, hash, pause/resume |
| Jobs | Postgres durable queue + transactional outbox |
| Audit | Immutable audit events |
| Evaluations | Datasets, graders, dashboards |
| Observability | structlog, OTEL hooks, Langfuse (optional) |

## Agent workflow

```mermaid
flowchart TD
  A[authenticate_and_load_context] --> B[classify_intent]
  B --> C[load_customer]
  C --> D[load_order]
  D --> E[retrieve_policy]
  E --> F[check_delivery]
  F --> G[compose_grounded_explanation]
  G --> H[validate_proposed_action]
  H -->|needs mutation| I[request_human_approval]
  I -->|approved| J[execute_approved_action]
  J --> K[verify_action_result]
  K --> L[finalize_response]
  H -->|unsafe / low confidence| M[create_escalation]
  M --> L
  A -->|auth fail| X[stop]
```

## RAG ingestion

```mermaid
flowchart LR
  U[Upload / presign] --> V[Verify MIME checksum]
  V --> J[Enqueue extract job]
  J --> X[Extract text]
  X --> C[Chunk sections]
  C --> E[Embed dense + sparse]
  E --> Q[Upsert Qdrant with tenant metadata]
  Q --> A[Activate document version]
```

## Approval sequence

```mermaid
sequenceDiagram
  participant U as User
  participant API as API
  participant G as LangGraph
  participant ERP as Mock ERP
  U->>API: Ask address change
  API->>G: Run graph
  G->>ERP: GET order
  G->>API: Persist approval + pause
  API-->>U: SSE approval_required
  U->>API: POST approve
  API->>G: Resume with revalidation
  G->>ERP: POST address-change Idempotency-Key
  G->>ERP: GET order verify
  G-->>U: Receipt + audit
```

## Deployment topology (demo)

```mermaid
flowchart TB
  subgraph Vercel
    WEB[apps/web]
  end
  subgraph FastAPI Cloud
    API[apps/api]
  end
  Neon[(Neon)]
  Qdrant[(Qdrant Cloud)]
  Upstash[(Upstash Redis)]
  WEB --> API
  API --> Neon
  API --> Qdrant
  API --> Upstash
```

## Key invariants

1. Authorization is deterministic backend code — never LLM-decided.
2. PostgreSQL is the system of record for business state, jobs, approvals, audit.
3. Every Qdrant search filters by `organization_id`.
4. Mutations require validation + approval + idempotency + verify-read.
5. Optional deps (Redis, Langfuse) degrade safely.
