import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowUpRight,
  CheckCircle2,
  MessageSquare,
  ShieldAlert,
  Wrench,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";

export const metadata: Metadata = {
  title: "Dashboard",
};

const metrics = [
  {
    label: "Conversations Today",
    value: "1,248",
    delta: "12%",
    icon: MessageSquare,
    alert: false,
  },
  {
    label: "Resolution Rate",
    value: "74.0%",
    delta: "2.1%",
    icon: CheckCircle2,
    alert: false,
  },
  {
    label: "Tool Success Rate",
    value: "98.2%",
    delta: "Avg 1.2s",
    icon: Wrench,
    alert: false,
  },
  {
    label: "Pending Approvals",
    value: "12",
    delta: "Needs review",
    icon: ShieldAlert,
    alert: true,
  },
];

const pillars = [
  {
    title: "Grounded answers",
    body: "Tenant-scoped hybrid RAG with citations — policy excerpts stay attached to every claim.",
  },
  {
    title: "Safe mutations",
    body: "Address changes pause for explicit approval, then run once with idempotency and verify-read.",
  },
  {
    title: "Operator visibility",
    body: "Inbox handoffs, run inspectors, evaluation metrics, and queue health in one console.",
  },
];

export default function DashboardPage() {
  return (
    <AppShell showTopBar>
      <div className="space-y-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-secondary">
              Overview
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-on-surface">
              Observable AI support operations
            </h1>
            <p className="mt-2 max-w-2xl text-base text-on-surface-variant">
              Multi-tenant demo agent for delayed-order explanations and
              human-approved address changes — grounded in policy, gated by RBAC.
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/chat">
              <Button>Open chat</Button>
            </Link>
            <Link href="/architecture">
              <Button variant="secondary">Architecture</Button>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {metrics.map((metric) => {
            const Icon = metric.icon;
            return (
              <article
                key={metric.label}
                className={`bento-card flex h-28 flex-col justify-between ${
                  metric.alert ? "border-error-container bg-error-container/10" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-on-surface-variant">
                    {metric.label}
                  </span>
                  <Icon className="size-[18px] text-secondary" />
                </div>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-semibold tabular-nums text-on-surface">
                    {metric.value}
                  </span>
                  <span
                    className={`mb-1 flex items-center text-xs font-semibold uppercase tracking-wide ${
                      metric.alert ? "text-warning" : "text-success"
                    }`}
                  >
                    {!metric.alert ? (
                      <ArrowUpRight className="size-3.5" />
                    ) : null}
                    {metric.delta}
                  </span>
                </div>
              </article>
            );
          })}
        </div>

        <section className="grid gap-4 md:grid-cols-3">
          {pillars.map((item) => (
            <article key={item.title} className="glass-card p-5">
              <h2 className="text-base font-semibold text-on-surface">
                {item.title}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-on-surface-variant">
                {item.body}
              </p>
            </article>
          ))}
        </section>

        <section className="glass-card p-6">
          <h2 className="text-lg font-semibold text-on-surface">
            Architecture at a glance
          </h2>
          <p className="mt-2 max-w-3xl text-sm text-on-surface-variant">
            Next.js on Vercel talks to a FastAPI modular monolith over JWT + SSE.
            Postgres is the system of record; Qdrant holds tenant-filtered chunks;
            mock CRM / ERP / carrier / ticketing services prove tool isolation.
          </p>
          <ul className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
            {[
              "Auth0 OIDC + local HS256 dev tokens",
              "LangGraph workflow with approval pauses",
              "Durable Postgres job queue + outbox",
              "Evaluations and audit trail dashboards",
            ].map((item) => (
              <li
                key={item}
                className="rounded-md bg-surface-container-low px-3 py-2 text-on-surface"
              >
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </AppShell>
  );
}
