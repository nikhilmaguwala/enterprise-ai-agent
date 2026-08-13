# ADR-010: Synthetic-data policy

- Status: Accepted
- Date: 2026-08-12

## Context

The demo must look realistic without using real customer, patient, or employer data.

## Decision

Seed only obviously fictional organizations (Acme Retail, Globex Shop), emails on `.test` domains, and policy documents labeled fictional. Include a prompt-injection canary document for evals. Forbid real PII in fixtures and screenshots.

## Consequences

- Safe public portfolio demos.
- Clear eval scenarios (delay, address change, injection, conflicts).
- Not a substitute for production anonymization programs.
