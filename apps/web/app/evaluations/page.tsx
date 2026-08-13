"use client";

import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { AiChip } from "@/components/ui/AiChip";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { StatusBadge, toneForStatus } from "@/components/ui/StatusBadge";
import { getEvaluations } from "@/lib/client";
import { ApiClientError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { EvaluationsDashboard } from "@/lib/schemas";

const MOCK_DASHBOARD: EvaluationsDashboard = {
  metrics: [
    {
      name: "Groundedness",
      value: 0.91,
      unit: "pass rate",
      target: 0.9,
      trend: "up",
    },
    {
      name: "Citation coverage",
      value: 0.88,
      unit: "pass rate",
      target: 0.85,
      trend: "flat",
    },
    {
      name: "Approval compliance",
      value: 1,
      unit: "pass rate",
      target: 1,
      trend: "flat",
    },
    {
      name: "Tenant isolation",
      value: 1,
      unit: "pass rate",
      target: 1,
      trend: "up",
    },
  ],
  suites: [
    {
      id: "suite-delay",
      name: "Order delay explanations",
      last_run_at: null,
      pass_rate: null,
      case_count: 12,
      status: "idle",
    },
    {
      id: "suite-address",
      name: "Address-change approvals",
      last_run_at: null,
      pass_rate: null,
      case_count: 8,
      status: "idle",
    },
  ],
};

export default function EvaluationsPage() {
  const { token, ready } = useAuth();
  const query = useQuery({
    queryKey: ["evaluations"],
    queryFn: getEvaluations,
    enabled: ready && Boolean(token),
    retry: false,
  });

  const usingMock = Boolean(token && query.isError);
  const data = query.data ?? (usingMock ? MOCK_DASHBOARD : undefined);
  const metrics = data?.metrics ?? [];
  const suites = data?.suites ?? [];

  return (
    <AppShell
      title="Evaluations"
      subtitle="Offline graders and live suite health for observable AI quality."
    >
      {!token ? (
        <EmptyState
          title="Sign in required"
          description="Supervisor and admin roles can view evaluation dashboards."
        />
      ) : (
        <div className="space-y-8">
          {query.isError ? (
            <ErrorBanner
              title="API unavailable — showing sample metrics"
              message={
                query.error instanceof ApiClientError
                  ? query.error.message
                  : "Falling back to local mock evaluation data"
              }
              onRetry={() => void query.refetch()}
            />
          ) : null}

          {metrics.length === 0 ? (
            <EmptyState
              title="No metrics yet"
              description="Run make eval once the evaluation harness is wired."
            />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {metrics.map((metric) => (
                <article key={metric.name} className="bento-card">
                  <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                    {metric.name}
                  </p>
                  <p className="mt-2 text-3xl font-semibold tabular-nums text-on-surface">
                    {metric.unit?.includes("rate")
                      ? `${Math.round(metric.value * 100)}%`
                      : metric.value}
                  </p>
                  <p className="mt-1 text-xs text-on-surface-variant">
                    {metric.target != null
                      ? `Target ${Math.round(metric.target * 100)}%`
                      : metric.unit ?? ""}
                    {metric.trend ? ` · ${metric.trend}` : ""}
                  </p>
                </article>
              ))}
            </div>
          )}

          {suites.length === 0 ? (
            <EmptyState title="No evaluation suites" />
          ) : (
            <div className="overflow-hidden rounded-xl border border-border-base bg-surface shadow-soft">
              <div className="flex items-center justify-between border-b border-border-base bg-surface-container-lowest px-4 py-3">
                <h3 className="text-base font-semibold text-on-surface">
                  Evaluation Suites
                </h3>
                <AiChip>
                  <Sparkles className="size-3.5" />
                  Groq primary
                </AiChip>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] border-collapse text-left">
                  <thead className="bg-table-header text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                    <tr>
                      <th className="p-4">Suite</th>
                      <th className="p-4">Cases</th>
                      <th className="p-4">Pass rate</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Last run</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-base text-sm">
                    {suites.map((suite) => (
                      <tr
                        key={suite.id}
                        className="transition hover:bg-canvas"
                      >
                        <td className="p-4 font-medium text-on-surface">
                          {suite.name}
                        </td>
                        <td className="p-4 tabular-nums text-on-surface-variant">
                          {suite.case_count ?? "—"}
                        </td>
                        <td className="p-4 tabular-nums text-on-surface">
                          {suite.pass_rate == null
                            ? "—"
                            : `${Math.round(suite.pass_rate * 100)}%`}
                        </td>
                        <td className="p-4">
                          <StatusBadge
                            label={suite.status ?? "idle"}
                            tone={toneForStatus(suite.status ?? "idle")}
                          />
                        </td>
                        <td className="p-4 tabular-nums text-on-surface-variant">
                          {suite.last_run_at
                            ? new Date(suite.last_run_at).toLocaleString()
                            : "Never"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
