# ADR-003: PostgreSQL as system of record

- Status: Accepted
- Date: 2026-08-12

## Context

Conversations, approvals, idempotency, jobs, and audit must survive restarts and remain queryable.

## Decision

Neon/PostgreSQL is the durable source of truth for business and operational state. SQLAlchemy 2.x + Alembic manage schema. Vector search and object storage are secondary indexes/blobs.

## Consequences

- Strong transactional guarantees for approvals + outbox.
- Hobby cold starts are mitigated with external job drain against Postgres.
- Redis is never authoritative for jobs.
