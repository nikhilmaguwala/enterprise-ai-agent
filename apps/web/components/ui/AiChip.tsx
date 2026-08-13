import type { ReactNode } from "react";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/cn";

type AiChipProps = {
  children: ReactNode;
  className?: string;
  showIcon?: boolean;
};

export function AiChip({ children, className, showIcon = true }: AiChipProps) {
  return (
    <span className={cn("ai-chip", className)}>
      {showIcon ? <Sparkles className="size-3.5" /> : null}
      {children}
    </span>
  );
}
