# Seed policies (source index)

Fictional policy documents for RAG and evaluations. All content is synthetic for the Enterprise AI Support Agent portfolio demo. No real employer or customer data.

| File | Purpose |
| --- | --- |
| [shipping-delay-policy.md](../data/policies/shipping-delay-policy.md) | Delay explanation rules, SLA language, citation-friendly sections |
| [address-change-rules.md](../data/policies/address-change-rules.md) | When address changes are allowed/denied; approval requirements |
| [prompt-injection-canary.md](../data/policies/prompt-injection-canary.md) | Canary document with injection-style text for safety evals |

## Ingestion notes

1. Upload via Knowledge UI or seed job.
2. Chunk by section headings; store `organization_id` on every Qdrant point.
3. Never treat canary instructions as system policy — retrieval must still pass through deterministic authorization and tool allowlists.

## Related

- `make seed` loads these into demo tenants when the seed script is present.
- Eval categories that reference these docs: policy questions, address-change, prompt-injection.
