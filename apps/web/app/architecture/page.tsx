import type { Metadata } from "next";
import { AppShell } from "@/components/layout/AppShell";
import { MermaidDiagram } from "@/components/architecture/MermaidDiagram";

export const metadata: Metadata = {
  title: "Architecture",
};

const CONTEXT_DIAGRAM = `
flowchart LR
  Customer[Customer] --> Web[Next.js Web]
  Agent[Support Agent] --> Web
  Admin[Administrator] --> Web
  Web -->|JWT + SSE| API[FastAPI Modular Monolith]
  API --> PG[(Neon Postgres)]
  API --> QD[(Qdrant)]
  API --> Redis[(Upstash Redis)]
  API --> Mocks[Mock CRM ERP Carrier Ticketing]
  API --> Groq[Groq LLM]
`;

const WORKFLOW_DIAGRAM = `
flowchart TD
  A[authenticate_and_load_context] --> B[classify_intent]
  B --> C[load_customer]
  C --> D[load_order]
  D --> E[retrieve_policy]
  E --> F[check_delivery]
  F --> G[compose_grounded_explanation]
  G --> H[validate_proposed_action]
  H -->|needs mutation| I[request_human_approval]
  I -->|approved| J[execute_approved_action]
  J --> K[verify_action_result]
  K --> L[finalize_response]
  H -->|unsafe / low confidence| M[create_escalation]
  M --> L
`;

const tradeoffs = [
  {
    title: "Modular monolith over microservices",
    body: "Keeps transactional consistency for approvals, jobs, and audit without distributed saga complexity on hobby tier.",
  },
  {
    title: "Postgres queue over always-on workers",
    body: "FOR UPDATE SKIP LOCKED + outbox survives scale-to-zero; Redis stays ephemeral.",
  },
  {
    title: "Deterministic authz outside the LLM",
    body: "RBAC and tenant filters are backend code. The model proposes; the platform enforces.",
  },
];

const freeDemoLimits = [
  "Hobby LLM budgets — daily model-call caps in env",
  "Qdrant free cluster — small synthetic corpus only",
  "Cold starts on FastAPI Cloud / serverless edges",
  "Synthetic tenants and mock enterprise systems only",
];

export default function ArchitecturePage() {
  return (
    <AppShell
      title="Technical Architecture"
      subtitle="System context, agent workflow, tradeoffs, and free-demo limits."
    >
      <div className="space-y-8">
        <MermaidDiagram chart={CONTEXT_DIAGRAM} title="System context" />
        <MermaidDiagram chart={WORKFLOW_DIAGRAM} title="Agent workflow" />

        <section>
          <h2 className="text-lg font-semibold text-on-surface">Tradeoffs</h2>
          <ul className="mt-4 grid gap-4 md:grid-cols-3">
            {tradeoffs.map((item) => (
              <li key={item.title} className="glass-card p-4">
                <h3 className="text-sm font-semibold text-on-surface">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm text-on-surface-variant">
                  {item.body}
                </p>
              </li>
            ))}
          </ul>
        </section>

        <section className="glass-card p-5">
          <h2 className="text-lg font-semibold text-on-surface">
            Free demo limits
          </h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-on-surface-variant">
            {freeDemoLimits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      </div>
    </AppShell>
  );
}
