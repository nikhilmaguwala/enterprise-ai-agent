"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState, type ChangeEvent } from "react";
import { MoreVertical, Search, Sparkles, Upload } from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { StatusBadge, toneForStatus } from "@/components/ui/StatusBadge";
import { listDocuments, uploadKnowledgeDocument } from "@/lib/client";
import { ApiClientError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

function formatBytes(value?: number): string {
  if (value == null) return "—";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function KnowledgePage() {
  const { token, ready } = useAuth();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["knowledge-documents"],
    queryFn: listDocuments,
    enabled: ready && Boolean(token),
    retry: false,
  });

  const uploadMutation = useMutation({
    mutationFn: uploadKnowledgeDocument,
    onSuccess: async () => {
      setUploadError(null);
      await queryClient.invalidateQueries({ queryKey: ["knowledge-documents"] });
    },
    onError: (error) => {
      setUploadError(
        error instanceof Error ? error.message : "Upload failed",
      );
    },
  });

  const items = query.data?.items ?? [];

  function handleFileSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    uploadMutation.mutate(file);
  }

  return (
    <AppShell
      title="Knowledge Library"
      subtitle="Tenant document corpus — upload status, chunk counts, and ingestion health."
    >
      {!token ? (
        <EmptyState
          title="Sign in required"
          description="Knowledge management is available to agent, supervisor, and admin roles."
        />
      ) : (
        <div className="space-y-6">
          <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
            <div className="relative w-full max-w-md">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-outline" />
              <input
                type="search"
                placeholder="Search knowledge base..."
                className="w-full rounded-md border border-outline-variant bg-surface py-2 pl-9 pr-3 text-sm outline-none transition focus:border-secondary focus:ring-1 focus:ring-secondary/20"
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select className="rounded-md border border-outline-variant bg-surface px-3 py-2 text-sm">
                <option>Status: All</option>
              </select>
              <Button variant="ai" icon={<Sparkles className="size-4" />}>
                Optimize RAG
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,image/*,.md,.txt,.doc,.docx"
                className="hidden"
                onChange={handleFileSelected}
              />
              <Button
                icon={<Upload className="size-4" />}
                disabled={uploadMutation.isPending}
                onClick={() => fileInputRef.current?.click()}
              >
                {uploadMutation.isPending ? "Uploading…" : "Upload Document"}
              </Button>
            </div>
          </div>

          <div className="rounded-lg border border-dashed border-outline-variant bg-surface-container-low p-4">
            <p className="text-sm font-medium text-on-surface">
              Firebase storage layout
            </p>
            <p className="mt-1 text-sm text-on-surface-variant">
              Files land in{" "}
              <code className="text-xs">resolve-ai/&#123;org&#125;/documents/pdfs|images|other/</code>{" "}
              on bucket <code className="text-xs">atmiya-db.appspot.com</code>.
              PDFs and images are sorted automatically by MIME type.
            </p>
            {uploadError ? (
              <p className="mt-2 text-xs text-danger">{uploadError}</p>
            ) : null}
          </div>

          {query.isError ? (
            <ErrorBanner
              message={
                query.error instanceof ApiClientError
                  ? query.error.message
                  : "Unable to load documents"
              }
              onRetry={() => void query.refetch()}
            />
          ) : null}

          {items.length === 0 ? (
            <EmptyState
              title="No documents yet"
              description="When policies are ingested, processing and active states appear here."
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-outline-variant bg-surface shadow-soft">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] border-collapse text-left">
                  <thead className="bg-table-header text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                    <tr>
                      <th className="px-4 py-3">Document Title</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Chunks</th>
                      <th className="px-4 py-3">Size</th>
                      <th className="px-4 py-3">Updated</th>
                      <th className="w-10 px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant text-sm">
                    {items.map((doc) => (
                      <tr
                        key={doc.id}
                        className="group transition hover:bg-canvas"
                      >
                        <td className="px-4 py-3">
                          <p className="font-medium text-on-surface group-hover:text-secondary">
                            {doc.title}
                          </p>
                          {doc.error_message ? (
                            <p className="mt-1 text-xs text-danger">
                              {doc.error_message}
                            </p>
                          ) : null}
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge
                            label={doc.status}
                            tone={toneForStatus(doc.status)}
                          />
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-on-surface">
                          {doc.chunk_count ?? "—"}
                        </td>
                        <td className="px-4 py-3 tabular-nums text-on-surface-variant">
                          {formatBytes(doc.byte_size)}
                        </td>
                        <td className="px-4 py-3 tabular-nums text-on-surface-variant">
                          {new Date(
                            doc.updated_at ?? doc.created_at,
                          ).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            type="button"
                            className="rounded p-1 text-outline hover:bg-surface-container-high hover:text-on-surface"
                            aria-label="More"
                          >
                            <MoreVertical className="size-4" />
                          </button>
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
