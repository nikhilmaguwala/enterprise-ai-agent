# ADR-011: Human approval before mutations

- Status: Accepted
- Date: 2026-08-12

## Context

Address changes and similar writes are high impact and must not auto-execute from model suggestions alone.

## Decision

Any mutating tool proposal creates an approval record with a payload hash, pauses the graph, and resumes only after explicit approve/reject. Post-approval revalidation checks authz, order state, and idempotency key before execution and verify-read.

## Consequences

- Demo clearly shows HITL safety.
- Duplicate clicks execute once.
- Slightly longer UX path for customers.
