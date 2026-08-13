# ADR-007: Deterministic authorization outside the LLM

- Status: Accepted
- Date: 2026-08-12

## Context

LLMs are non-deterministic and susceptible to prompt injection. Permissions must never be model-decided.

## Decision

Enforce OIDC JWT validation, org membership, and RBAC in FastAPI middleware/services. Tool gateway rejects unauthorized calls before HTTP integration. Approvals revalidate authz and entity state after human consent.

## Consequences

- Prompt injection cannot grant privileges by itself.
- Graders assert forbidden tool use independently of model text.
- Slightly more boilerplate than “ask the model what the user can do.”
