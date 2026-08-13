# Demo script (≈2 minutes)

Synthetic tenants only. No real customer data.

## Setup (before recording)

1. `make setup && make dev` (or open hosted Vercel + FastAPI Cloud URLs).
2. Confirm Acme + Globex seed users exist.
3. Knowledge docs ingested (shipping delay + address change policies).
4. `DEV_AUTH_ENABLED` only for local; production uses Auth0.

## Cast

| Role | Account |
| --- | --- |
| Customer | `customer@acme-demo.test` |
| Support | `agent@acme-demo.test` |
| Cross-tenant | `customer@globex-demo.test` |

## Shot list

### 0:00–0:20 — Problem & architecture

- Landing page brand + one-line problem.
- Cut to architecture diagram (modular monolith + mocks).

### 0:20–0:50 — Grounded delay explanation

1. Sign in as Acme customer.
2. Ask: “Why is order ORD-1001 delayed?”
3. Show SSE tool progress (CRM → ERP → carrier → policy retrieve).
4. Highlight citations resolving to policy chunks (not invented policy).

### 0:50–1:20 — Address change with approval

1. Ask to change delivery address for the same order.
2. Show approval card with exact proposed payload.
3. Approve once; show idempotent ERP mutation + verify-read.
4. Mention audit event / receipt.

### 1:20–1:40 — Safety: isolation & injection

1. Briefly switch to Globex user — cannot see Acme order.
2. Paste a prompt-injection style message; show refusal / no privileged tool.

### 1:40–2:00 — Ops & close

1. Support inbox escalation / handoff summary (or evals page).
2. Close on: human approval, tenant filters, durable jobs, free-tier deploy map.

## Narration cues

- “Authorization is deterministic code — never the model.”
- “PostgreSQL is system of record; Redis is optional.”
- “Mutations pause for explicit approval and run once.”

## B-roll / screenshots to capture

- Chat with citations
- Approval card
- Agent-run inspector
- Ops / queue health
- Eval dashboard

## Measured results

Fill only after real runs (latency, eval pass rate, cost). Do not invent numbers.
