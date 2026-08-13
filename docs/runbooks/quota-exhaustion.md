# Runbook: Quota exhaustion

## Symptoms

- Users receive quota exceeded errors.
- Global model call counter near `MAX_GLOBAL_MODEL_CALLS_PER_DAY`.
- Groq dashboard shows rate/budget limits.

## Immediate actions

1. Confirm which quota fired (anonymous, authenticated, global, per-turn).
2. Do **not** remove safety caps in production to “keep the demo going.”
3. For portfolio demos: switch to recorded walkthrough or wait for UTC day reset / raise caps intentionally in env after review.

## Tuning (operator)

| Variable | Meaning |
| --- | --- |
| `MAX_ANONYMOUS_MESSAGES_PER_DAY` | Unauth chat cap |
| `MAX_AUTHENTICATED_MESSAGES_PER_DAY` | Per-user cap |
| `MAX_GLOBAL_MODEL_CALLS_PER_DAY` | Estate-wide LLM calls |
| `MAX_MODEL_CALLS_PER_TURN` | Graph breadth control |
| `MAX_GRAPH_STEPS` | Hard stop |
| `MAX_OUTPUT_TOKENS` | Completion size |

## Verification

- Counter reset or raised deliberately.
- One controlled successful turn.
- Abuse test still blocked at new ceiling.
