import { Loader2 } from "lucide-react";
import type { ToolProgress } from "@/lib/schemas";
import { StatusBadge, toneForStatus } from "@/components/ui/StatusBadge";

type ToolProgressListProps = {
  items: ToolProgress[];
};

export function ToolProgressList({ items }: ToolProgressListProps) {
  if (items.length === 0) return null;

  return (
    <div className="mt-3 space-y-2" aria-live="polite">
      {items.map((item, index) => (
        <div
          key={`${item.tool_name}-${index}`}
          className="flex w-max max-w-full items-center gap-2 rounded-md border border-border-base bg-surface px-3 py-2 text-sm text-on-surface-variant shadow-soft"
        >
          {item.status === "running" ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : null}
          <span>{item.detail ?? item.tool_name}</span>
          <StatusBadge label={item.status} tone={toneForStatus(item.status)} />
        </div>
      ))}
    </div>
  );
}
