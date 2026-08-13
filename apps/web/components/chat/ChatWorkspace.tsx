"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Paperclip,
  Search,
  Send,
  ShoppingBag,
  Truck,
  BookOpen,
} from "lucide-react";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Button } from "@/components/ui/Button";
import { StatusBadge, toneForStatus } from "@/components/ui/StatusBadge";
import { getStarterOrderNumber } from "@/lib/auth";
import {
  conversationEventsPath,
  createConversation,
  decideApproval,
  fetchCurrentUser,
  isDemoMode,
  listConversations,
  listMessages,
  sendMessage,
} from "@/lib/client";
import type { Message, ToolProgress } from "@/lib/schemas";
import { connectSse } from "@/lib/sse";
import { ApiClientError } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/cn";

export function ChatWorkspace() {
  const queryClient = useQueryClient();
  const { token, ready, user } = useAuth();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [liveTools, setLiveTools] = useState<ToolProgress[]>([]);
  const [streamHint, setStreamHint] = useState<string | null>(null);
  const [filter, setFilter] = useState<"active" | "waiting" | "resolved">(
    "active",
  );

  const [starterOrder, setStarterOrder] = useState<string | null>(() =>
    getStarterOrderNumber(),
  );

  const exampleOrder = useMemo(() => {
    if (starterOrder) return starterOrder;
    if (user?.email.endsWith("@acme-demo.test")) return "ACM-10001";
    return "your order";
  }, [starterOrder, user?.email]);

  useEffect(() => {
    if (!ready || !token || isDemoMode()) return;
    if (getStarterOrderNumber()) return;
    void fetchCurrentUser()
      .then((data) => {
        if (data.starter_order_number) {
          setStarterOrder(data.starter_order_number);
        }
      })
      .catch(() => undefined);
  }, [ready, token]);

  const conversationsQuery = useQuery({
    queryKey: ["conversations"],
    queryFn: listConversations,
    enabled: ready && Boolean(token),
    retry: false,
  });

  const messagesQuery = useQuery({
    queryKey: ["messages", selectedId],
    queryFn: () => listMessages(selectedId!),
    enabled: ready && Boolean(token && selectedId),
    retry: false,
  });

  const createMutation = useMutation({
    mutationFn: () => createConversation("New conversation"),
    onSuccess: async (conversation) => {
      await queryClient.invalidateQueries({ queryKey: ["conversations"] });
      setSelectedId(conversation.id);
      setLiveTools([]);
      setStreamHint("Connecting to agent stream…");
    },
  });

  const sendMutation = useMutation({
    mutationFn: (content: string) => sendMessage(selectedId!, content),
    onSuccess: async () => {
      setDraft("");
      await queryClient.invalidateQueries({
        queryKey: ["messages", selectedId],
      });
      await queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const approvalMutation = useMutation({
    mutationFn: ({
      approvalId,
      decision,
    }: {
      approvalId: string;
      decision: "approve" | "reject";
    }) => decideApproval(approvalId, decision),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["messages", selectedId],
      });
    },
  });

  useEffect(() => {
    if (!selectedId || !token) return;

    const connection = connectSse(
      conversationEventsPath(selectedId),
      {
        onOpen: () => setStreamHint("Listening for agent events"),
        onEvent: (event) => {
          if (event.type === "tool_started" || event.type === "tool_finished") {
            const data = event.data as {
              tool_name?: string;
              status?: ToolProgress["status"];
              detail?: string;
            };
            if (!data.tool_name) return;
            setLiveTools((prev) => {
              const next = [...prev];
              const idx = next.findIndex((t) => t.tool_name === data.tool_name);
              const item: ToolProgress = {
                tool_name: data.tool_name!,
                status:
                  data.status ??
                  (event.type === "tool_started" ? "running" : "succeeded"),
                detail: data.detail,
              };
              if (idx >= 0) next[idx] = item;
              else next.push(item);
              return next;
            });
          }
          if (
            event.type === "message_completed" ||
            event.type === "approval_required" ||
            event.type === "run_status"
          ) {
            void queryClient.invalidateQueries({
              queryKey: ["messages", selectedId],
            });
          }
          if (event.type === "error") {
            setStreamHint("Stream reported an error");
          }
        },
        onError: () => setStreamHint("Stream disconnected — retrying…"),
      },
      { token },
    );

    return () => connection.close();
  }, [selectedId, token, queryClient]);

  function selectConversation(id: string) {
    setSelectedId(id);
    setLiveTools([]);
    setStreamHint("Connecting to agent stream…");
  }

  const conversations = conversationsQuery.data?.items ?? [];
  const messages: Message[] = useMemo(
    () => messagesQuery.data?.items ?? [],
    [messagesQuery.data],
  );
  const selectedConversation = conversations.find((c) => c.id === selectedId);

  const authMissing = !token;
  const listError =
    conversationsQuery.error instanceof ApiClientError
      ? conversationsQuery.error.message
      : conversationsQuery.error
        ? "Unable to load conversations"
        : null;

  return (
    <div className="flex h-full min-h-0 flex-1 overflow-hidden">
      <aside className="flex w-80 shrink-0 flex-col border-r border-border-base bg-surface">
        <div className="space-y-2 border-b border-border-base p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-on-surface">
              Conversations
            </h2>
            <Button
              className="px-2.5 py-1.5 text-xs"
              disabled={authMissing || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              New
            </Button>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-outline" />
            <input
              type="search"
              placeholder="Search conversations..."
              className="w-full rounded-md border border-border-base bg-surface py-2 pl-9 pr-3 text-sm outline-none transition focus:border-secondary focus:ring-2 focus:ring-secondary/10"
            />
          </div>
          <div className="flex gap-2">
            {(["active", "waiting", "resolved"] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setFilter(tab)}
                className={cn(
                  "flex-1 rounded py-1 text-xs font-semibold uppercase tracking-wide transition",
                  filter === tab
                    ? "border border-border-base bg-surface-container-lowest text-on-surface shadow-soft"
                    : "text-on-surface-variant hover:bg-surface-container-highest",
                )}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {authMissing ? (
            <div className="p-4">
              <EmptyState
                title="Sign in to chat"
                description="Use Dev sign in in the top bar to exchange a local demo token."
              />
            </div>
          ) : listError ? (
            <div className="p-4">
              <ErrorBanner
                message={listError}
                onRetry={() => void conversationsQuery.refetch()}
              />
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-4">
              <EmptyState
                title="No conversations yet"
                description="Start a thread to ask about an order delay or address change."
              />
            </div>
          ) : (
            <ul>
              {conversations.map((c) => {
                const active = c.id === selectedId;
                return (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() => selectConversation(c.id)}
                      className={cn(
                        "w-full border-b border-border-base p-4 text-left transition hover:bg-surface-container-lowest",
                        active &&
                          "border-l-4 border-l-secondary bg-surface-container-lowest",
                      )}
                    >
                      <div className="mb-1 flex items-start justify-between gap-2">
                        <span className="text-sm font-semibold text-on-surface">
                          {c.title || "Untitled conversation"}
                        </span>
                        <span className="text-xs tabular-nums text-outline">
                          {new Date(c.updated_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      <p className="truncate text-sm text-on-surface-variant">
                        {c.status.replaceAll("_", " ")}
                      </p>
                      <div className="mt-2">
                        <StatusBadge
                          label={c.status}
                          tone={toneForStatus(c.status)}
                        />
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </aside>

      <section className="flex min-w-[400px] flex-1 flex-col bg-canvas">
        {!selectedId ? (
          <div className="flex flex-1 items-center justify-center p-6">
            <EmptyState
              title="Select a conversation"
              description="Or create a new one to stream grounded answers, tool progress, and approval cards."
            />
          </div>
        ) : (
          <>
            <header className="flex items-center justify-between border-b border-border-base bg-surface px-4 py-3 shadow-soft">
              <div>
                <h2 className="text-base font-semibold text-on-surface">
                  {selectedConversation?.title ?? "Conversation"}
                </h2>
                <p className="text-sm text-on-surface-variant">
                  {streamHint ?? "Idle"} · SSE stream
                </p>
              </div>
              <StatusBadge label="live" tone="info" />
            </header>

            <div className="flex-1 space-y-6 overflow-y-auto px-6 py-6">
              {messagesQuery.isError ? (
                <ErrorBanner
                  message={
                    messagesQuery.error instanceof Error
                      ? messagesQuery.error.message
                      : "Failed to load messages"
                  }
                  onRetry={() => void messagesQuery.refetch()}
                />
              ) : null}
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  onApprovalDecide={async (approvalId, decision) => {
                    await approvalMutation.mutateAsync({
                      approvalId,
                      decision,
                    });
                  }}
                />
              ))}
              {liveTools.length > 0 ? (
                <ChatMessage
                  message={{
                    id: "live-tools",
                    conversation_id: selectedId,
                    role: "assistant",
                    content: "Working…",
                    created_at: new Date().toISOString(),
                    tool_progress: liveTools,
                  }}
                />
              ) : null}
            </div>

            <form
              className="border-t border-border-base bg-surface p-4"
              onSubmit={(event) => {
                event.preventDefault();
                const content = draft.trim();
                if (!content || sendMutation.isPending) return;
                sendMutation.mutate(content);
              }}
            >
              <div className="rounded-lg border border-border-base bg-surface-container-lowest shadow-soft focus-within:border-secondary focus-within:ring-2 focus-within:ring-secondary/10">
                <label htmlFor="chat-input" className="sr-only">
                  Message
                </label>
                <textarea
                  id="chat-input"
                  rows={2}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder={`Ask why order ${exampleOrder} is delayed, or request an address change…`}
                  className="min-h-[80px] w-full resize-none border-none bg-transparent p-4 text-sm outline-none"
                />
                <div className="flex items-center justify-between border-t border-border-base p-2">
                  <div className="flex gap-1">
                    <button
                      type="button"
                      className="rounded p-2 text-on-surface-variant hover:bg-surface-variant"
                      aria-label="Attach file"
                    >
                      <Paperclip className="size-4" />
                    </button>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs tabular-nums text-outline">
                      {isDemoMode() ? "Quota: demo" : "Quota: live"}
                    </span>
                    <Button
                      type="submit"
                      disabled={!draft.trim() || sendMutation.isPending}
                      icon={<Send className="size-4" />}
                    >
                      Send
                    </Button>
                  </div>
                </div>
              </div>
              {sendMutation.isError ? (
                <p className="mt-2 text-xs text-danger">
                  {sendMutation.error instanceof Error
                    ? sendMutation.error.message
                    : "Send failed"}
                </p>
              ) : null}
            </form>
          </>
        )}
      </section>

      <aside className="hidden w-80 shrink-0 flex-col overflow-y-auto border-l border-border-base bg-surface xl:flex">
        <div className="space-y-6 p-4">
          <ContextPanel
            icon={<ShoppingBag className="size-4" />}
            title="Order Summary"
          >
            <p className="text-sm font-semibold text-on-surface">
              {exampleOrder === "your order"
                ? "Your workspace order"
                : `Order ${exampleOrder}`}
            </p>
            <p className="mt-1 text-sm text-on-surface-variant">
              {exampleOrder === "your order"
                ? "Start a conversation and mention your order number from signup."
                : "Delayed shipment with hub backlog — ask the agent for status or an address change."}
            </p>
          </ContextPanel>
          <ContextPanel icon={<Truck className="size-4" />} title="Shipment">
            <p className="text-sm text-on-surface-variant">
              Carrier timeline and tracking events will populate from tool
              results.
            </p>
          </ContextPanel>
          <ContextPanel
            icon={<BookOpen className="size-4" />}
            title="Retrieved Sources"
          >
            <p className="text-sm text-on-surface-variant">
              Policy citations from RAG appear inline in assistant messages.
            </p>
          </ContextPanel>
        </div>
      </aside>
    </div>
  );
}

function ContextPanel({
  icon,
  title,
  children,
}: {
  icon: ReactNode;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-border-base bg-surface-container-lowest shadow-soft">
      <div className="flex items-center gap-2 border-b border-border-base bg-surface-container-low px-3 py-2 text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
        {icon}
        {title}
      </div>
      <div className="p-3">{children}</div>
    </div>
  );
}
