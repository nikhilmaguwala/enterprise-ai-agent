"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Filter, MoreVertical, Plus, Search, SortAsc } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { AiChip } from "@/components/ui/AiChip";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { StatusBadge, toneForStatus } from "@/components/ui/StatusBadge";
import { listEscalations } from "@/lib/client";
import { ApiClientError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

export default function InboxPage() {
  const { token, ready } = useAuth();
  const query = useQuery({
    queryKey: ["inbox"],
    queryFn: listEscalations,
    enabled: ready && Boolean(token),
    retry: false,
  });

  const items = query.data?.items ?? [];

  return (
    <AppShell
      title="Support Inbox"
      subtitle="Manage and resolve customer inquiries."
      headerActions={
        <>
          <div className="relative hidden sm:block">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-outline" />
            <input
              type="search"
              placeholder="Search orders, customers..."
              className="w-64 rounded-lg border border-outline-variant bg-surface py-2 pl-9 pr-3 text-sm outline-none transition focus:border-secondary focus:ring-2 focus:ring-secondary/10"
            />
          </div>
          <Button icon={<Plus className="size-4" />}>New Ticket</Button>
        </>
      }
    >
      {!token ? (
        <EmptyState
          title="Sign in required"
          description="Support and admin roles can review escalations after Dev sign in."
        />
      ) : query.isError ? (
        <div className="space-y-4">
          <ErrorBanner
            message={
              query.error instanceof ApiClientError
                ? query.error.message
                : "Unable to load inbox"
            }
            onRetry={() => void query.refetch()}
          />
          <EmptyState
            title="No escalations loaded"
            description="The API may be offline. Empty inbox state is shown when the service returns no items."
          />
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-outline-variant pb-2">
            <div className="flex flex-wrap gap-6">
              <button
                type="button"
                className="-mb-[3px] border-b-2 border-primary pb-2 text-sm font-bold text-primary"
              >
                Escalated{" "}
                <span className="ml-2 rounded-full bg-surface-container-high px-2 py-0.5 text-xs font-semibold text-on-surface-variant">
                  {items.length}
                </span>
              </button>
              <button
                type="button"
                className="-mb-[3px] pb-2 text-sm font-medium text-on-surface-variant hover:text-primary"
              >
                Assigned to me
              </button>
              <button
                type="button"
                className="-mb-[3px] pb-2 text-sm font-medium text-on-surface-variant hover:text-primary"
              >
                Unassigned
              </button>
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" className="px-3 py-1.5 text-xs">
                <Filter className="size-4" />
                Filter
              </Button>
              <Button variant="secondary" className="px-3 py-1.5 text-xs">
                <SortAsc className="size-4" />
                Sort
              </Button>
            </div>
          </div>

          {items.length === 0 ? (
            <EmptyState
              title="Inbox is clear"
              description="Escalations appear here when the agent is under-evidenced, unsafe, or hits a quota limit."
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-outline-variant bg-surface shadow-soft">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[800px] border-collapse text-left">
                  <thead className="border-b border-outline-variant bg-table-header text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                    <tr>
                      <th className="p-4">Customer / Order</th>
                      <th className="p-4">Reason</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Created</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant text-sm">
                    {items.map((item) => (
                      <tr
                        key={item.id}
                        className="group transition hover:bg-canvas"
                      >
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <div className="flex size-8 items-center justify-center rounded-full bg-surface-container-high text-xs font-bold text-primary">
                              {(item.customer_email ?? "?")
                                .slice(0, 2)
                                .toUpperCase()}
                            </div>
                            <div>
                              <div className="font-semibold text-on-surface">
                                {item.customer_email ?? "Unknown customer"}
                              </div>
                              <div className="text-xs tabular-nums text-on-surface-variant">
                                {item.conversation_id.slice(0, 8)}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <span className="font-medium text-on-surface">
                            {item.reason}
                          </span>
                          <p className="mt-0.5 max-w-xs truncate text-xs text-on-surface-variant">
                            {item.handoff_summary}
                          </p>
                        </td>
                        <td className="p-4">
                          <div className="flex flex-col gap-2">
                            <StatusBadge
                              label={item.status}
                              tone={toneForStatus(item.status)}
                            />
                            {item.priority ? (
                              <AiChip showIcon={false}>
                                Priority: {item.priority}
                              </AiChip>
                            ) : null}
                          </div>
                        </td>
                        <td className="p-4 tabular-nums text-on-surface-variant">
                          {new Date(item.created_at).toLocaleString()}
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Link
                              href={`/chat?c=${item.conversation_id}`}
                              className="text-sm font-medium text-secondary hover:underline"
                            >
                              Open
                            </Link>
                            <button
                              type="button"
                              className="rounded p-1.5 text-on-surface-variant opacity-0 transition hover:bg-surface-container-high group-hover:opacity-100"
                              aria-label="More actions"
                            >
                              <MoreVertical className="size-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-between border-t border-outline-variant bg-surface-container-lowest px-4 py-2 text-xs text-on-surface-variant">
                <span>
                  Showing {items.length} escalation{items.length === 1 ? "" : "s"}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
