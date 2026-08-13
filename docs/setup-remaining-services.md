# Remaining free-tier service setup (YOU do these)

Neon, Qdrant, and Groq are already wired in local `.env` (never commit that file).
Vercel frontend is deployed.

## Status

| Service | Status | Action |
| --- | --- | --- |
| Neon Postgres | Done | Migrated + seeded |
| Qdrant Cloud | Credentials present | Collection auto-created on first upsert; adapter uses `query_points` |
| Groq | Credentials present | Primary LLM |
| Vercel Hobby | Done | https://enterprise-ai-support-agent.vercel.app |
| FastAPI Cloud Hobby | **You** | Steps below |
| Upstash Redis Free | **You** | Rate limits / locks |
| Cloudflare R2 | **You** | Doc uploads (local filesystem works meanwhile) |
| Auth0 | **You** | Production OIDC (dev auth works locally) |
| Langfuse Hobby | Optional | Tracing |

---

## 1) FastAPI Cloud Hobby (required for hosted API)

Official docs: https://fastapicloud.com/docs/getting-started/

```bash
# From machine with browser login available
cd apps/api
python3 -m pip install 'fastapi[standard]'
fastapi login          # opens browser
fastapi deploy         # deploys detected FastAPI app
```

Then set secrets in the FastAPI Cloud dashboard (Apps → your app → Environment):

```text
APP_ENV=production
DEV_AUTH_ENABLED=false   # after Auth0 is ready; keep true only for temporary demos
DATABASE_URL=<neon connection string>
QDRANT_URL=...
QDRANT_API_KEY=...
GROQ_API_KEY=...
LLM_PRIMARY_PROVIDER=groq
LLM_PRIMARY_MODEL=openai/gpt-oss-20b
INTERNAL_JOB_SECRET=...
INTERNAL_JOB_HMAC_KEY=...   # >=16 chars
CORS_ORIGINS=https://enterprise-ai-support-agent.vercel.app
API_URL=https://<your-app>.fastapicloud.dev
APP_URL=https://enterprise-ai-support-agent.vercel.app
CRM_BASE_URL=...   # mock services or deployed mocks
ERP_BASE_URL=...
CARRIER_BASE_URL=...
TICKETING_BASE_URL=...
MOCK_SERVICE_TOKEN=...
```

After deploy:

1. Run migrations against Neon (already applied once locally; re-run if schema changes):  
   `cd apps/api && alembic upgrade head`
2. Update Vercel env `NEXT_PUBLIC_API_URL` to the FastAPI Cloud URL and redeploy web.
3. Schedule `POST /api/v1/internal/jobs/drain` externally (Hobby may scale to zero) using HMAC headers.

Do **not** invent unsupported CLI flags. If `fastapi deploy` prompts for project settings, follow the interactive flow.

---

## 2) Upstash Redis Free

1. Create database at https://console.upstash.com  
2. Copy REST URL + token into:
   - `UPSTASH_REDIS_REST_URL`
   - `UPSTASH_REDIS_REST_TOKEN`
3. App degrades safely if unset (in-memory / Postgres counters).

---

## 3) Cloudflare R2

1. Create bucket `enterprise-ai-docs`  
2. Create API token with Object Read/Write  
3. Set `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`  
4. Until then, `OBJECT_STORAGE_BACKEND=filesystem` works locally.

---

## 4) Auth0

1. Create Regular Web Application + API audience  
2. Allowed callback: `https://enterprise-ai-support-agent.vercel.app/api/auth/callback`  
3. Allowed logout/origin: the Vercel URL  
4. Set `OIDC_ISSUER`, `OIDC_AUDIENCE`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`  
5. Set `DEV_AUTH_ENABLED=false` in production once OIDC works.

---

## 5) Langfuse Hobby (optional)

https://cloud.langfuse.com → create project → set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`.

---

## Security note

You pasted live Neon/Groq/Qdrant secrets in chat. **Rotate them** after this session and never commit `.env`.
