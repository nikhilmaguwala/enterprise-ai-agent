# ADR-006: Redis for ephemeral coordination only

- Status: Accepted
- Date: 2026-08-12

## Context

Rate limiting, short-lived caches, and distributed locks benefit from Redis, but Redis outages must not halt core support flows.

## Decision

Use Upstash Redis (or Compose Redis) only for ephemeral coordination. If Redis is unavailable, degrade: fall back to Postgres counters / allow-with-warning / skip non-critical locks, and log the limitation.

## Consequences

- Optional dependency aligns with hobby reliability.
- Prevents Redis from becoming a silent single point of failure for business truth.
