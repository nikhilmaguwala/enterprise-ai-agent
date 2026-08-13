import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "ai";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  icon?: ReactNode;
};

const VARIANTS: Record<ButtonVariant, string> = {
  primary:
    "bg-[#2563EB] text-white hover:bg-[#1d4ed8] border border-transparent",
  secondary:
    "bg-surface text-on-surface border border-border-base hover:bg-surface-container-low",
  ghost:
    "bg-transparent text-on-surface-variant border border-transparent hover:bg-surface-container-high",
  ai: "bg-ai-bg text-ai-text border border-[color-mix(in_srgb,var(--ai-text)_20%,transparent)] hover:bg-[#EDE9FE]",
};

export function Button({
  className,
  variant = "primary",
  icon,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        VARIANTS[variant],
        className,
      )}
      {...props}
    >
      {icon}
      {children}
    </button>
  );
}
