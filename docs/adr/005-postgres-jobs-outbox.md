# ADR-005: Postgres durable jobs and transactional outbox

- Status: Accepted
- Date: 2026-08-12

## Context

Background ingest, verification, and ticket creation must not be lost on API restart. Hobby hosts may scale to zero.

## Decision

Implement a Postgres job queue with `FOR UPDATE SKIP LOCKED`, dead-letter support, and a transactional outbox. Expose HMAC-signed `/internal/jobs/drain` for external schedulers.

## Consequences

- Jobs survive process death.
- No dependency on Redis/SQS for correctness in the demo.
- Operators must configure a cron/drain for hosted scale-to-zero.
