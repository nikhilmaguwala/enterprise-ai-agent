# FastAPI Cloud deployment (Hobby)

This project deploys the backend with the official FastAPI Cloud CLI (`fastapi deploy`).
Do not invent unsupported flags. Prefer interactive login via browser.

Official docs:

- [Quick start](https://fastapicloud.com/docs/getting-started/)
- [Existing projects](https://fastapicloud.com/docs/getting-started/existing-project/)
- [Deploy command](https://fastapicloud.com/docs/fastapi-cloud-cli/deploy/)

## Prerequisites (YOU must do)

1. Create a FastAPI Cloud account at [https://fastapicloud.com](https://fastapicloud.com).
2. Ensure `apps/api` has `fastapi[standard]` in dependencies and `requires-python >= 3.12`.
3. Ensure the FastAPI app is importable (recommended entrypoint `app.main:app`).
4. Optionally set entrypoint in `apps/api/pyproject.toml`:

```toml
[tool.fastapi]
entrypoint = "app.main:app"
```

5. Collect secrets for Neon, Qdrant, Groq, Auth0, Upstash, R2, Langfuse (see [docs/deployment.md](../../docs/deployment.md)). Never commit them.

## Local verify before deploy

From `apps/api`:

```bash
cd apps/api
# Prefer uv or pip-installed fastapi[standard]
fastapi dev
```

If `fastapi dev` works without an explicit path argument, configuration is correct.

## Login (interactive, browser)

```bash
cd apps/api
fastapi login
```

Your browser opens to complete authentication. This step is manual and cannot be automated safely for Hobby without operator consent.

## First deploy

```bash
cd apps/api
fastapi deploy
```

Supported options (official):

| Option | Purpose |
| --- | --- |
| `[PATH]` | Optional path to the app folder |
| `--no-wait` | Return after upload without waiting for status |
| `--app-id` | Target an existing app (also `FASTAPI_CLOUD_APP_ID`) |
| `--large-file-threshold` | Warn threshold in MB for large files (default 10) |

First run may prompt you to select/create a team and create/link an app. A local `.fastapicloud` directory is created after success. Add `.fastapicloud/` to local ignore lists if it contains machine-specific linkage you do not want shared (team policy dependent).

## Environment variables (YOU must set)

Prefer the FastAPI Cloud **dashboard → Environment Variables**, or the official CLI:

```bash
fastapi cloud env set APP_ENV "production"
fastapi cloud env set --secret DATABASE_URL "postgresql+asyncpg://..."
```

### Required for production demo

| Variable | Notes |
| --- | --- |
| `APP_ENV` | `production` |
| `APP_URL` | Vercel frontend URL |
| `API_URL` | FastAPI Cloud public URL |
| `DATABASE_URL` | Neon connection string (`asyncpg` driver) |
| `QDRANT_URL` | Qdrant Cloud cluster URL |
| `QDRANT_API_KEY` | Qdrant API key (secret) |
| `QDRANT_COLLECTION` | e.g. `enterprise_ai_chunks` |
| `GROQ_API_KEY` | Groq secret |
| `LLM_PRIMARY_PROVIDER` | `groq` |
| `LLM_PRIMARY_MODEL` | `openai/gpt-oss-20b` |
| `OIDC_ISSUER` | Auth0 issuer URL trailing slash |
| `OIDC_AUDIENCE` | API audience |
| `OIDC_CLIENT_ID` | Auth0 app client id |
| `OIDC_CLIENT_SECRET` | Auth0 secret (if confidential client) |
| `DEV_AUTH_ENABLED` | **must be `false` in production** |
| `INTERNAL_JOB_SECRET` | Random high-entropy secret |
| `INTERNAL_JOB_HMAC_KEY` | ≥32 byte secret for job drain HMAC |
| `CORS_ORIGINS` | Exact Vercel origin(s) |
| `CRM_BASE_URL` / `ERP_BASE_URL` / `CARRIER_BASE_URL` / `TICKETING_BASE_URL` | Hosted mock URLs or tunnel |
| `MOCK_SERVICE_TOKEN` | Shared mock auth token |

### Strongly recommended

| Variable | Notes |
| --- | --- |
| `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` | Ephemeral rate limits / locks |
| `R2_ENDPOINT` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET` | Document storage |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | Optional tracing |
| `MAX_*` quota vars | Copy from `.env.example` |
| `GIT_SHA` / `GRAPH_VERSION` | Observability labels |

### Optional / degrade safely

| Variable | Behavior if missing |
| --- | --- |
| Redis / Langfuse | App continues; logs limitation |
| `GEMINI_API_KEY` / fallback model | No silent mutation fallback |
| `SENTRY_DSN` | Error reporting skipped |

## Subsequent deploys

```bash
cd apps/api
fastapi deploy
```

## CI deploy (GitHub Actions)

Pushes to `main` run `.github/workflows/deploy.yml`, which deploys in parallel:

- **API** → FastAPI Cloud via `fastapi cloud deploy` (requires repo secrets `FASTAPI_CLOUD_TOKEN`, `FASTAPI_CLOUD_APP_ID`)
- **Web** → Vercel via `amondnet/vercel-action` (requires `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`)

Bootstrap secrets once from a logged-in machine:

```bash
cd apps/api
fastapi cloud setup-ci --secrets-only --app-id <your-app-id>
# Vercel: create a token at https://vercel.com/account/tokens then:
gh secret set VERCEL_TOKEN
gh secret set VERCEL_ORG_ID
gh secret set VERCEL_PROJECT_ID
```

The workflow runs `scripts/prepare-fastapi-cloud.sh` before each API deploy so monorepo packages are vendored into `apps/api/packages`.

## Troubleshooting

- **App not found**: confirm `fastapi login` account matches the dashboard app; use `fastapi cloud unlink` then redeploy if the cloud app was deleted.
- **Large files warning**: exclude via `.gitignore` or `.fastapicloudignore`.
- **Import errors**: verify `[tool.fastapi] entrypoint` and package layout under `apps/api`.
