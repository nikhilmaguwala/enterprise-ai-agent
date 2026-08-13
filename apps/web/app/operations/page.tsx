"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { StatusBadge, toneForStatus } from "@/components/ui/StatusBadge";
import { getOperations, replayJob } from "@/lib/client";
import { ApiClientError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import type { OperationsDashboard } from "@/lib/schemas";

const MOCK_OPS: OperationsDashboard = {
  queues: [
    {
      name: "ingestion",
      depth: 0,
      oldest_age_seconds: null,
      processing: 0,
      failed: 0,
    },
    {
      name: "embeddings",
      depth: 0,
      oldest_age_seconds: null,
      processing: 0,
      failed: 0,
    },
    {
      name: "outbox",
      depth: 0,
      oldest_age_seconds: null,
      processing: 0,
      failed: 0,
    },
  ],
  integrations: [
    { name: "CRM", status: "unknown", latency_ms: null },
    { name: "ERP", status: "unknown", latency_ms: null },
    { name: "Carrier", status: "unknown", latency_ms: null },
    { name: "Ticketing", status: "unknown", latency_ms: null },
    { name: "Qdrant", status: "unknown", latency_ms: null },
    { name: "Postgres", status: "unknown", latency_ms: null },
  ],
  recent_replays: [],
};

export default function OperationsPage() {
  const { token, ready } = useAuth();
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState("");

  const query = useQuery({
    queryKey: ["operations"],
    queryFn: getOperations,
    enabled: ready && Boolean(token),
    retry: false,
  });

  const replayMutation = useMutation({
    mutationFn: (id: string) => replayJob(id),
    onSuccess: async () => {
      setJobId("");
      await queryClient.invalidateQueries({ queryKey: ["operations"] });
    },
  });

  const usingMock = Boolean(token && query.isError);
  const data = query.data ?? (usingMock ? MOCK_OPS : undefined);

  return (
    <AppShell
      title="Operations"
      subtitle="Queue depth, integration health, and job replay controls."
    >
      {!token ? (
        <EmptyState
          title="Sign in as admin"
          description="Operations controls are limited to admin roles in the demo."
        />
      ) : (
        <div className="space-y-8">
          {query.isError ? (
            <ErrorBanner
              title="API unavailable — showing empty operations scaffold"
              message={
                query.error instanceof ApiClientError
                  ? query.error.message
                  : "Unable to reach operations dashboard"
              }
              onRetry={() => void query.refetch()}
            />
          ) : null}

          <section>
            <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
              Queues
            </h2>
            {!data || data.queues.length === 0 ? (
              <EmptyState title="No queue stats" />
            ) : (
              <div className="grid gap-4 sm:grid-cols-3">
                {data.queues.map((queue) => (
                  <article key={queue.name} className="bento-card">
                    <p className="text-sm font-semibold capitalize text-on-surface">
                      {queue.name}
                    </p>
                    <p className="mt-2 text-4xl font-semibold tabular-nums text-on-surface">
                      {queue.depth}
                    </p>
                    <p className="mt-1 text-xs text-on-surface-variant">
                      processing {queue.processing ?? 0} · failed{" "}
                      {queue.failed ?? 0}
                    </p>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
              Integrations
            </h2>
            {!data || data.integrations.length === 0 ? (
              <EmptyState title="No integration checks" />
            ) : (
              <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {data.integrations.map((item) => (
                  <li key={item.name}>
                    <Card>
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-medium text-on-surface">{item.name}</p>
                        <StatusBadge
                          label={item.status}
                          tone={toneForStatus(item.status)}
                        />
                      </div>
                      <p className="mt-2 text-xs text-on-surface-variant">
                        {item.latency_ms != null
                          ? `${item.latency_ms} ms`
                          : "Latency n/a"}
                        {item.detail ? ` · ${item.detail}` : ""}
                      </p>
                    </Card>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <Card>
            <h2 className="text-sm font-semibold text-on-surface">Replay job</h2>
            <p className="mt-1 text-sm text-on-surface-variant">
              Re-queue a failed durable job by ID. Requires admin token and a
              reachable API.
            </p>
            <form
              className="mt-4 flex flex-wrap gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                const id = jobId.trim();
                if (!id) return;
                replayMutation.mutate(id);
              }}
            >
              <label htmlFor="job-id" className="sr-only">
                Job ID
              </label>
              <input
                id="job-id"
                value={jobId}
                onChange={(e) => setJobId(e.target.value)}
                placeholder="job uuid"
                className="min-w-[16rem] flex-1 rounded-md border border-border-base px-3 py-2 text-sm outline-none focus:border-secondary focus:ring-2 focus:ring-secondary/10"
              />
              <Button
                type="submit"
                disabled={!jobId.trim() || replayMutation.isPending}
              >
                Replay
              </Button>
            </form>
            {replayMutation.isError ? (
              <p className="mt-2 text-xs text-danger">
                {replayMutation.error instanceof Error
                  ? replayMutation.error.message
                  : "Replay failed"}
              </p>
            ) : null}
            {replayMutation.isSuccess ? (
              <p className="mt-2 text-xs text-success">Replay accepted.</p>
            ) : null}
          </Card>
        </div>
      )}
    </AppShell>
  );
}
