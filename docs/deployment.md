# Deployment guide

Complete free/hobby-tier setup for the Enterprise AI Support Agent demo.

Legend:

- **YOU must do** — interactive account/console steps that cannot be automated safely from this repo.
- **Automated / repo-provided** — code, Makefile targets, CI, or docs already in the monorepo.

Never commit real secrets. Use `.env` locally and cloud dashboards / secret stores for hosted environments.

---

## 0. Already available (assumed)

| Service | Status | Notes |
| --- | --- | --- |
| Neon Postgres | **YOU already have** | Paste connection string into `.env` / FastAPI Cloud as `DATABASE_URL` |
| Qdrant Cloud | **YOU already have** | Set `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` |
| Groq | **YOU already have** | Set `GROQ_API_KEY`, keep model via `LLM_PRIMARY_MODEL` |

**Automated:** adapters and config keys exist in `.env.example`.

---

## 1. Neon (Postgres) — already provisioned

### YOU must do

1. Open [https://console.neon.tech](https://console.neon.tech).
2. Copy the pooled connection string.
3. Convert the driver for SQLAlchemy async:

```text
postgresql://...  →  postgresql+asyncpg://...
```

4. Set `DATABASE_URL` in local `.env` and FastAPI Cloud env (secret).

### Automated

- Alembic migrations: `make migrate`
- Seed: `make seed`
- Health check hits Postgres on `/health` (when API is implemented)

---

## 2. Qdrant Cloud — already provisioned

### YOU must do

1. Open [https://cloud.qdrant.io](https://cloud.qdrant.io).
2. Copy cluster URL and API key.
3. Set:

```text
QDRANT_URL=https://....aws.cloud.qdrant.io
QDRANT_API_KEY=...
QDRANT_COLLECTION=enterprise_ai_chunks
```

### Automated

- Collection creation / upsert during knowledge ingest
- Tenant filter enforced in retrieval code

---

## 3. Groq — already provisioned

### YOU must do

1. Open [https://console.groq.com](https://console.groq.com).
2. Create/rotate an API key.
3. Set `GROQ_API_KEY`, `LLM_PRIMARY_PROVIDER=groq`, `LLM_PRIMARY_MODEL=openai/gpt-oss-20b`.

### Automated

- Provider adapter, token/latency metrics hooks, quota guards

---

## 4. FastAPI Cloud Hobby — manual interactive

### YOU must do

1. Sign up: [https://fastapicloud.com](https://fastapicloud.com).
2. Locally:

```bash
cd apps/api
fastapi login          # browser opens
fastapi cloud env set ...   # or set vars in dashboard
fastapi deploy
```

3. Copy the public URL into Vercel `NEXT_PUBLIC_API_URL` and Auth0 callbacks allowlists as needed.
4. Set `DEV_AUTH_ENABLED=false` in production.
5. Configure CORS to the Vercel origin only.

Exact steps: [infra/fastapi-cloud/README.md](../infra/fastapi-cloud/README.md).

### Automated

- App packaging via official `fastapi deploy`
- CI documents the manual gate (does not invent unsupported deploy flags)

---

## 5. Vercel Hobby (frontend)

### YOU must do (one-time account / project link)

1. Sign up / log in: [https://vercel.com/signup](https://vercel.com/signup).
2. Install Vercel GitHub integration or use Vercel CLI login.
3. Import this repository.
4. Set **Root Directory** to `apps/web` (preferred) **or** use root `vercel.json` which points build/install into `apps/web`.
5. Add environment variables:

| Name | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | FastAPI Cloud public URL |
| `NEXT_PUBLIC_APP_URL` | Vercel deployment URL |
| `NEXT_PUBLIC_DEV_AUTH_ENABLED` | `false` in production |

6. Optional GitHub Actions secret: `VERCEL_TOKEN`, plus `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` for CLI deploy from `main`.

### Automated

- Root `vercel.json` and `infra/vercel.json`
- `.github/workflows/main.yml` deploys with `amondnet/vercel-action` **only if** `VERCEL_TOKEN` is present
- Preview deploys on PRs when the Vercel GitHub app is connected

---

## 6. Upstash Redis Free

### YOU must do

1. Sign up: [https://console.upstash.com](https://console.upstash.com).
2. Create a Redis database (free tier).
3. Copy REST URL + token.
4. Set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` in FastAPI Cloud (and local `.env` if desired).

### Automated

- Redis used only for ephemeral rate limits / locks / short cache
- App degrades safely if Redis is unavailable (Postgres remains system of record)

---

## 7. Cloudflare R2

### YOU must do

1. Sign up / open: [https://dash.cloudflare.com](https://dash.cloudflare.com) → R2.
2. Create bucket (e.g. `enterprise-ai-docs`).
3. Create an R2 API token with object read/write on that bucket.
4. Set:

```text
OBJECT_STORAGE_BACKEND=s3
R2_ENDPOINT=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=enterprise-ai-docs
```

### Automated

- Local MinIO in Docker Compose for S3-compatible development
- Filesystem backend via `OBJECT_STORAGE_BACKEND=filesystem` for offline work

---

## 8. Auth0 (OIDC)

### YOU must do

1. Sign up: [https://auth0.com/signup](https://auth0.com/signup).
2. Create a Regular Web Application (or SPA + API as preferred).
3. Create an **API** with audience, e.g. `https://api.enterprise-ai-support.local`.
4. Configure Allowed Callback URLs:

```text
http://localhost:3000/api/auth/callback
https://<your-vercel-domain>/api/auth/callback
```

5. Configure Allowed Logout URLs and Web Origins for local + Vercel.
6. Set:

```text
OIDC_ISSUER=https://<tenant>.auth0.com/
OIDC_AUDIENCE=https://api.enterprise-ai-support.local
OIDC_CLIENT_ID=...
OIDC_CLIENT_SECRET=...
DEV_AUTH_ENABLED=false
```

7. Map demo users/roles via Auth0 Actions or post-login claims to `org_id` / `role` (or rely on DB membership mapping by email for the synthetic demo).

### Automated

- JWT validation middleware, RBAC outside the LLM
- Local `DEV_AUTH_ENABLED=true` HS256 tokens for offline demos

---

## 9. Langfuse Hobby

### YOU must do

1. Sign up: [https://cloud.langfuse.com](https://cloud.langfuse.com).
2. Create a project; copy public/secret keys.
3. Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST=https://cloud.langfuse.com`.

### Automated

- Optional tracing hooks; missing Langfuse does not block requests

---

## 10. Mock enterprise services (hosted or local)

### YOU must do (hosted demo)

- Run mocks on a free host, container, or tunnel, **or** run them only for local demos.
- Point `CRM_BASE_URL`, `ERP_BASE_URL`, `CARRIER_BASE_URL`, `TICKETING_BASE_URL` at reachable HTTPS endpoints.
- Rotate `MOCK_SERVICE_TOKEN` away from the default for any public deployment.

### Automated

- Docker Compose services `mock-crm`, `mock-erp`, `mock-carrier`, `mock-ticketing`
- `make docker-up` / `make dev`

---

## 11. Post-deploy checklist

1. `GET {API_URL}/health` returns healthy dependencies (or degraded optional ones).
2. Open Vercel URL; authenticate; chat as Acme customer.
3. Confirm tenant isolation with Globex user.
4. Run address-change approval path once.
5. Trigger `/internal/jobs/drain` via HMAC-signed scheduler (external cron) if scale-to-zero.
6. Confirm no secrets in git: `git secrets` / CI gitleaks.

---

## Production mapping (conceptual)

| Demo | Production |
| --- | --- |
| FastAPI Cloud | ECS/Fargate |
| Neon | RDS PostgreSQL |
| Qdrant Cloud | Managed Qdrant / OpenSearch k-NN |
| Postgres jobs | SQS + DLQ |
| Cloudflare R2 | S3 |
| Groq/Gemini | Bedrock or approved enterprise model |
| Upstash Redis | ElastiCache |
| Auth0 | Enterprise OIDC/SAML |
| Langfuse | Self-hosted or enterprise observability |

Terraform under `infra/terraform` is conceptual and must not auto-create chargeable AWS resources.
