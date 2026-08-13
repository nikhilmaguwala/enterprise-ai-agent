# ADR-008: Provider-neutral model adapter

- Status: Accepted
- Date: 2026-08-12

## Context

Primary provider is Groq; Gemini and Ollama are optional. Hard-coding one SDK into graph nodes would lock the portfolio.

## Decision

Define a provider protocol for text, tools, structured output, embeddings (where available), usage, latency, health, and error normalization. Configure provider/model via environment variables. Never silent-fallback during mutations.

## Consequences

- Local Ollama profile works without code changes.
- Mutation safety remains explicit when primary LLM is down (pause/escalate).
- Browser never receives provider API keys.
