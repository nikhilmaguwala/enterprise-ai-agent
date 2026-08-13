import { cn } from "@/lib/cn";

const TONE_DOT = {
  neutral: "bg-outline",
  info: "bg-secondary",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
} as const;

const TONE_TEXT = {
  neutral: "text-on-surface",
  info: "text-secondary",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
} as const;

export type StatusTone = keyof typeof TONE_DOT;

type StatusBadgeProps = {
  label: string;
  tone?: StatusTone;
  dot?: boolean;
  className?: string;
};

export function StatusBadge({
  label,
  tone = "neutral",
  dot = true,
  className,
}: StatusBadgeProps) {
  if (dot) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1.5 text-xs font-medium capitalize",
          TONE_TEXT[tone],
          className,
        )}
      >
        <span className={cn("size-2 rounded-full", TONE_DOT[tone])} />
        {label.replaceAll("_", " ")}
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full bg-surface-container-high px-2 py-0.5 text-xs font-medium text-on-surface-variant",
        className,
      )}
    >
      {label.replaceAll("_", " ")}
    </span>
  );
}

export function toneForStatus(status: string): StatusTone {
  const value = status.toLowerCase();
  if (
    [
      "active",
      "succeeded",
      "healthy",
      "resolved",
      "approved",
      "passed",
      "open",
      "indexed",
      "completed",
    ].includes(value)
  ) {
    return value === "open" ? "info" : "success";
  }
  if (
    [
      "pending",
      "processing",
      "running",
      "queued",
      "waiting_approval",
      "paused",
      "degraded",
      "idle",
    ].includes(value)
  ) {
    return "warning";
  }
  if (
    ["failed", "down", "rejected", "escalated", "cancelled", "expired"].includes(
      value,
    )
  ) {
    return "danger";
  }
  return "neutral";
}
