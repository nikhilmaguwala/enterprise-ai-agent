"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { use } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { StatusBadge, toneForStatus } from "@/components/ui/StatusBadge";
import { getAgentRun } from "@/lib/client";
import { ApiClientError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default function RunInspectorPage({ params }: PageProps) {
  const { id } = use(params);
  const { token, ready } = useAuth();

  const query = useQuery({
    queryKey: ["run", id],
    queryFn: () => getAgentRun(id),
    enabled: ready && Boolean(token && id),
    retry: false,
  });

  const run = query.data;

  return (
    <AppShell
      title="Agent Run Observability"
      subtitle="Step timeline, graph version, and failure detail for a single orchestration."
    >
      {!token ? (
        <EmptyState
          title="Sign in required"
          description="Run details require an authenticated session."
        />
      ) : query.isError ? (
        <ErrorBanner
          message={
            query.error instanceof ApiClientError
              ? query.error.message
              : `Unable to load run ${id}`
          }
          onRetry={() => void query.refetch()}
        />
      ) : !run ? (
        <EmptyState
          title="Loading run…"
          description="Fetching orchestration steps from the API."
        />
      ) : (
        <div className="space-y-4">
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-mono text-sm text-on-surface-variant">
                  {run.id}
                </p>
                <p className="mt-1 text-sm text-on-surface">
                  Conversation{" "}
                  <Link
                    href={`/chat?c=${run.conversation_id}`}
                    className="font-medium text-secondary hover:underline"
                  >
                    {run.conversation_id}
                  </Link>
                </p>
              </div>
              <StatusBadge label={run.status} tone={toneForStatus(run.status)} />
            </div>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                  Graph
                </dt>
                <dd className="font-medium text-on-surface">
                  {run.graph_version ?? "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                  Started
                </dt>
                <dd className="font-medium tabular-nums text-on-surface">
                  {run.started_at
                    ? new Date(run.started_at).toLocaleString()
                    : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                  Finished
                </dt>
                <dd className="font-medium tabular-nums text-on-surface">
                  {run.finished_at
                    ? new Date(run.finished_at).toLocaleString()
                    : "—"}
                </dd>
              </div>
            </dl>
            {run.error ? (
              <p className="mt-4 rounded-md bg-error-container/40 px-3 py-2 text-sm text-danger">
                {run.error}
              </p>
            ) : null}
          </Card>

          {run.steps.length === 0 ? (
            <EmptyState
              title="No steps recorded"
              description="Steps appear as the LangGraph workflow progresses."
            />
          ) : (
            <ol className="space-y-3">
              {run.steps.map((step, index) => (
                <li key={step.id}>
                  <Card>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-on-surface">
                        <span className="mr-2 text-on-surface-variant">
                          {index + 1}.
                        </span>
                        {step.name}
                      </p>
                      <StatusBadge
                        label={step.status}
                        tone={toneForStatus(step.status)}
                      />
                    </div>
                    {step.detail ? (
                      <p className="mt-2 text-sm text-on-surface-variant">
                        {step.detail}
                      </p>
                    ) : null}
                    {(step.input != null || step.output != null) && (
                      <div className="mt-3 grid gap-3 lg:grid-cols-2">
                        {step.input != null ? (
                          <pre className="overflow-x-auto rounded-md bg-surface-container-low p-3 text-xs text-on-surface">
                            {JSON.stringify(step.input, null, 2)}
                          </pre>
                        ) : null}
                        {step.output != null ? (
                          <pre className="overflow-x-auto rounded-md bg-surface-container-low p-3 text-xs text-on-surface">
                            {JSON.stringify(step.output, null, 2)}
                          </pre>
                        ) : null}
                      </div>
                    )}
                  </Card>
                </li>
              ))}
            </ol>
          )}
        </div>
      )}
    </AppShell>
  );
}
