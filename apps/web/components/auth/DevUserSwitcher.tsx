"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, Users } from "lucide-react";
import { DEV_USERS, canAccessPath } from "@/lib/auth";
import { devLogin, isDevAuthEnabled } from "@/lib/client";
import { env } from "@/lib/env";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/cn";

type DevUserSwitcherProps = {
  className?: string;
  variant?: "header" | "landing";
};

export function DevUserSwitcher({
  className,
  variant = "header",
}: DevUserSwitcherProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, refresh } = useAuth();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  if (!isDevAuthEnabled()) return null;

  async function handleDevLogin(email: string) {
    setBusy(true);
    setError(null);
    try {
      const data = await devLogin(email);
      refresh();
      setOpen(false);
      if (!canAccessPath(data.user.role, pathname)) {
        router.push(data.user.role === "customer" ? "/chat" : "/dashboard");
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dev login failed");
    } finally {
      setBusy(false);
    }
  }

  const summaryLabel = user
    ? `Switch demo user (${user.role})`
    : "Dev sign in";

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="listbox"
        onClick={() => setOpen((value) => !value)}
        className={cn(
          "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          variant === "landing"
            ? "border border-outline-variant bg-surface text-on-surface hover:bg-surface-container-low"
            : "bg-secondary text-white hover:bg-[#1d4ed8]",
        )}
      >
        <Users className="size-4 shrink-0" />
        <span className="max-w-[10rem] truncate sm:max-w-none">{summaryLabel}</span>
        <ChevronDown
          className={cn(
            "size-3.5 shrink-0 opacity-80 transition-transform",
            open && "rotate-180",
          )}
        />
      </button>
      {open ? (
        <div
          role="listbox"
          className="absolute right-0 z-40 mt-2 w-72 rounded-lg border border-border-base bg-surface p-3 shadow-soft"
        >
        <p className="text-xs text-on-surface-variant">
          Local demo accounts only ({env.apiUrl}).
        </p>
        {user ? (
          <p className="mt-1 text-xs text-on-surface">
            Signed in as <span className="font-medium">{user.email}</span>
          </p>
        ) : null}
        <ul className="mt-2 space-y-1">
          {DEV_USERS.map((demoUser) => {
            const active = user?.email === demoUser.email;
            return (
              <li key={demoUser.email}>
                <button
                  type="button"
                  disabled={busy || active}
                  onClick={() => void handleDevLogin(demoUser.email)}
                  className={cn(
                    "w-full rounded-md px-2 py-2 text-left text-sm transition-colors disabled:opacity-60",
                    active
                      ? "bg-secondary-container font-semibold text-on-secondary-container"
                      : "hover:bg-surface-container-high",
                  )}
                >
                  <span className="font-medium">{demoUser.label}</span>
                  <span className="block text-xs text-on-surface-variant">
                    {demoUser.email}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
        {error ? (
          <p className="mt-2 text-xs text-danger">{error}</p>
        ) : null}
        </div>
      ) : null}
    </div>
  );
}
