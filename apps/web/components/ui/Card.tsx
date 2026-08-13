import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type CardProps = {
  children: ReactNode;
  className?: string;
  padding?: boolean;
};

export function Card({ children, className, padding = true }: CardProps) {
  return (
    <div className={cn("glass-card", padding && "p-4", className)}>{children}</div>
  );
}

type CardHeaderProps = {
  title: string;
  action?: ReactNode;
  className?: string;
};

export function CardHeader({ title, action, className }: CardHeaderProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between border-b border-border-base px-4 py-3",
        className,
      )}
    >
      <h3 className="text-base font-semibold text-on-surface">{title}</h3>
      {action}
    </div>
  );
}
