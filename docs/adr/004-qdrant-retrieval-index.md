# ADR-004: Qdrant as retrieval index

- Status: Accepted
- Date: 2026-08-12

## Context

Grounded policy answers require tenant-scoped hybrid retrieval with resolvable citations.

## Decision

Use Qdrant Cloud (local Qdrant in Compose) as the vector/sparse retrieval index. Every point stores `organization_id` and chunk metadata; every query applies an organization filter.

## Consequences

- Citations resolve to chunk IDs stored in Postgres + Qdrant.
- Free-tier corpus size stays small by design.
- Relational policy metadata remains in Postgres for auditability.
