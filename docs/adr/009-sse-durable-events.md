# ADR-009: SSE with durable event recovery

- Status: Accepted
- Date: 2026-08-12

## Context

Agent progress (tool calls, citations, approval cards) must stream to the UI and recover after reconnects.

## Decision

Use Server-Sent Events for live progress while persisting events in Postgres keyed by conversation/run. Clients resume from last event cursor.

## Consequences

- Better UX than polling for multi-minute graphs.
- Reconnect does not lose approval prompts.
- Requires careful heartbeat and idempotent client rendering.
