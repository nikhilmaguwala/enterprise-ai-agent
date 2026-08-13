"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { DevUserSwitcher } from "@/components/auth/DevUserSwitcher";
import { Button } from "@/components/ui/Button";
import { isDevAuthEnabled, isRegistrationEnabled } from "@/lib/client";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/cn";

const NAV: Array<{
  href: string;
  label: string;
  exact?: boolean;
}> = [
  { href: "/", label: "Landing", exact: true },
  { href: "/dashboard", label: "Overview" },
  { href: "/chat", label: "Conversations" },
  { href: "/architecture", label: "Architecture" },
];

export function LandingHeader() {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-outline-variant bg-surface/95 backdrop-blur">
      <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-4 px-6 py-3 sm:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex size-8 items-center justify-center rounded bg-primary text-sm font-bold text-on-primary">
              R
            </div>
            <div>
              <p className="text-base font-bold leading-none text-primary">
                ResolveAI
              </p>
              <p className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
                Enterprise Support
              </p>
            </div>
          </Link>
          <nav className="hidden items-center gap-6 md:flex">
            {NAV.map((item) => {
              const active = item.exact
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "text-sm font-medium transition",
                    active
                      ? "border-b-2 border-secondary pb-0.5 text-secondary"
                      : "text-on-surface-variant hover:text-secondary",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {isRegistrationEnabled() ? (
            <>
              {!user ? (
                <Link
                  href="/login"
                  className="hidden text-sm font-medium text-on-surface-variant hover:text-secondary sm:block"
                >
                  Sign in
                </Link>
              ) : null}
              <Link href={user ? "/chat" : "/signup"}>
                <Button icon={<ArrowRight className="size-4" />}>
                  {user ? "Open app" : "Create account"}
                </Button>
              </Link>
            </>
          ) : (
            <Link href={user ? "/chat" : "/dashboard"}>
              <Button icon={<ArrowRight className="size-4" />}>
                {user ? "Open demo" : "Get started"}
              </Button>
            </Link>
          )}
          {isDevAuthEnabled() ? <DevUserSwitcher variant="landing" /> : null}
        </div>
      </div>
    </header>
  );
}
