import Link from "next/link";
import { Bot } from "lucide-react";
import type { Message } from "@/lib/schemas";
import { CitationList } from "@/components/chat/CitationList";
import { MessageMarkdown } from "@/components/chat/MessageMarkdown";
import { ToolProgressList } from "@/components/chat/ToolProgress";
import { ApprovalCard } from "@/components/chat/ApprovalCard";
import { cn } from "@/lib/cn";

type ChatMessageProps = {
  message: Message;
  onApprovalDecide?: (
    approvalId: string,
    decision: "approve" | "reject",
  ) => Promise<void> | void;
};

export function ChatMessage({ message, onApprovalDecide }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  return (
    <article
      className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}
      aria-label={`${message.role} message`}
    >
      {isAssistant ? (
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-ai-bg text-ai-text">
          <Bot className="size-4" />
        </div>
      ) : null}

      <div
        className={cn(
          "max-w-[min(100%,42rem)] text-sm leading-relaxed",
          isUser
            ? "rounded-lg rounded-tr-none bg-secondary px-4 py-3 text-white shadow-soft"
            : "rounded-lg rounded-tl-none border border-border-base bg-surface px-4 py-3 text-on-surface shadow-soft",
        )}
      >
        {isAssistant ? (
          <MessageMarkdown content={message.content} />
        ) : (
          <p className="whitespace-pre-wrap">{message.content}</p>
        )}
        {isAssistant && message.citations ? (
          <CitationList citations={message.citations} />
        ) : null}
        {isAssistant && message.tool_progress ? (
          <ToolProgressList items={message.tool_progress} />
        ) : null}
        {isAssistant && message.approval ? (
          <ApprovalCard
            approval={message.approval}
            onDecide={onApprovalDecide}
          />
        ) : null}
        {message.run_id ? (
          <p className="mt-2 text-xs text-on-surface-variant">
            Run{" "}
            <Link
              href={`/runs/${message.run_id}`}
              className="font-medium text-secondary underline-offset-2 hover:underline"
            >
              {message.run_id.slice(0, 8)}…
            </Link>
          </p>
        ) : null}
        <span className="mt-2 block text-xs tabular-nums text-outline">
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {isUser ? (
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-surface-variant text-xs font-bold text-on-surface">
          You
        </div>
      ) : null}
    </article>
  );
}
