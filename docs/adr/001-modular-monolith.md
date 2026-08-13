# ADR-001: Modular monolith instead of microservices

- Status: Accepted
- Date: 2026-08-12

## Context

The portfolio demo must show multi-system tool use, approvals, jobs, and RAG without operational sprawl on hobby tiers.

## Decision

Ship a FastAPI modular monolith with explicit internal modules (identity, conversations, agent, knowledge, integrations, approvals, jobs, audit, evals, observability). Mock CRM/ERP/carrier/ticketing remain separate HTTP services only because they simulate external enterprise systems.

## Consequences

- Simpler local/dev/deploy story (one API process).
- Clear module boundaries without network hops for core domain.
- Future extraction of modules remains possible without rewriting contracts.
