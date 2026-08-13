# Enterprise AI Support — Web

Next.js App Router frontend for the Enterprise AI Support Agent.

## Stack

- Next.js (App Router) + TypeScript strict
- Tailwind CSS
- TanStack Query
- Zod schemas for API responses
- SSE (`EventSource` + `Last-Event-ID` reconnection)

## Setup

```bash
cd apps/web
cp .env.example .env.local
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000).

## Environment

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Backend base URL (default `http://localhost:8000`) |
| `NEXT_PUBLIC_APP_URL` | Frontend URL |
| `NEXT_PUBLIC_DEV_AUTH_ENABLED` | Show Dev sign-in when `true` |

No Auth0 client secrets belong in this app. Dev login proxies to `POST /v1/auth/dev-login` via `/api/auth/dev-login`.

## Scripts

```bash
pnpm dev
pnpm build
pnpm start
pnpm lint
```

## Routes

| Path | Purpose |
| --- | --- |
| `/` | Landing + architecture summary |
| `/chat` | Conversations, SSE stream, citations, approvals |
| `/inbox` | Escalations / handoffs |
| `/knowledge` | Document list + upload status |
| `/runs/[id]` | Agent-run inspector |
| `/evaluations` | Metrics dashboard (mock fallback) |
| `/operations` | Queues, integration health, replay |
| `/architecture` | Diagrams, tradeoffs, free-demo limits |
