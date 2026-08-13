# ADR-002: LangGraph for agent orchestration

- Status: Accepted
- Date: 2026-08-12

## Context

The critical path requires multi-step tool use, pause/resume for human approval, and durable run state.

## Decision

Use LangGraph to model the support workflow as an explicit state machine with named nodes (classify, retrieve, compose, request approval, execute, verify, escalate).

## Consequences

- Approvals map naturally to interrupt/resume semantics.
- Graph version (`GRAPH_VERSION`) is auditable per run.
- Complexity is higher than a single prompt loop, but control is stronger for safety demos.
