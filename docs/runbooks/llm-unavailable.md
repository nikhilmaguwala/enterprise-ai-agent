# Runbook: LLM provider unavailable

## Symptoms

- Chat turns fail with provider error classification.
- Health shows LLM degraded/unhealthy.
- Metrics: elevated provider 5xx / timeout.

## Immediate actions

1. Confirm Groq status / API key validity in dashboard (no key rotation in git).
2. Check `LLM_PRIMARY_PROVIDER` / `LLM_PRIMARY_MODEL` env on FastAPI Cloud.
3. Verify quotas (`MAX_GLOBAL_MODEL_CALLS_PER_DAY`) not exhausted (see quota-exhaustion runbook).

## Expected product behavior

- Read-only explanations may fail closed with a user-visible error.
- **Mutations must not silently fall back** to another provider.
- Graph should pause or escalate rather than invent tool results.

## Mitigation options

1. Wait for primary provider recovery.
2. If explicitly configured, enable fallback provider for **non-mutation** paths only.
3. Local demo: start Ollama profile (`docker compose --profile ollama up`) and point adapter to Ollama.
4. Show recorded demo / architecture pages if live LLM budget is spent.

## Verification

- `/health` LLM check green.
- One successful grounded Q&A without mutation.
- Approval path still requires human confirmation after recovery.

## Escalation

Page on-call owner of Groq/Auth secrets if keys were rotated unexpectedly.
