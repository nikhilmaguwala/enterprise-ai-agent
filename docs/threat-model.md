# Threat model

Scope: Enterprise AI Support Agent demo (multi-tenant chat, RAG, tools, approvals, jobs). Synthetic data only.

## Assets

| Asset | Sensitivity |
| --- | --- |
| Tenant conversation content | High within tenant |
| Order/customer records via mocks | Medium (fictional) |
| Policy corpus + embeddings | Medium |
| OIDC tokens / API secrets | Critical |
| Approval / audit trails | High integrity |
| LLM budget / quotas | Availability / cost |

## Trust boundaries

1. Browser → Vercel web → FastAPI API (JWT)
2. API → Neon / Qdrant / Redis / R2
3. API → mock CRM/ERP/carrier/ticketing (service token)
4. API → Groq (server-side key only)
5. Internal job drain endpoint (HMAC)

## Threats and mitigations

### Tenant isolation

- **Threat:** Cross-org data read/write via IDs or RAG leakage.
- **Mitigation:** Trusted `organization_id` from membership, never from client body alone; Qdrant filter on every search; repository methods require tenant context; isolation tests in CI.

### Prompt injection

- **Threat:** Documents or user text coerce tool misuse or secret exfiltration.
- **Mitigation:** Deterministic RBAC outside LLM; tool allowlists; canary injection doc in corpus; graders for forbidden tools; no provider keys in prompts/logs.

### Unauthorized actions

- **Threat:** Customer triggers supervisor-only mutation or another user’s order change.
- **Mitigation:** Policy engine + RBAC; approval required for mutations; revalidation after approve; mock services enforce token + org scoping where applicable.

### Duplicate mutations

- **Threat:** Double-submit approval or retry applies address change twice.
- **Mitigation:** Idempotency keys, durable approval state machine, verify-read after write, audit of single execution.

### Secret leakage

- **Threat:** Keys in git, logs, traces, or client bundles.
- **Mitigation:** `.env` gitignored; `.env.example` placeholders only; gitleaks in CI; structlog redaction; Langfuse optional and scrubbed; never expose Groq/Auth0 secrets to Next.js.

### Malicious uploads

- **Threat:** Oversized/malware/MIME-spoofed knowledge files.
- **Mitigation:** Presigned upload with size/MIME checks; checksum verify; async extract in jobs; virus scanning noted as production follow-up (not claimed in hobby demo).

### Cost exhaustion

- **Threat:** Abuse drives Groq spend or DoS via long graphs.
- **Mitigation:** Per-anonymous / per-user / global daily quotas; max model calls per turn; max graph steps; max output tokens; degrade with clear errors.

### Audit integrity

- **Threat:** Tampering with who approved what.
- **Mitigation:** Append-only audit events; approval payload hashes; immutable run event log; restricted admin read APIs.

## Residual risks (accepted for hobby)

- Scale-to-zero cold starts delay job drain until external cron fires.
- Free LLM budget exhaustion stops live demos (recorded walkthrough remains).
- Mock services are not hardened enterprise systems.

## Out of scope

Real payment fraud, physical security, full SOC2 evidence collection.
