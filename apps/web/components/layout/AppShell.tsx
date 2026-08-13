"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";
import {
  Bell,
  Building2,
  ChevronDown,
  LogOut,
  Menu,
  X,
} from "lucide-react";
import { DevUserSwitcher } from "@/components/auth/DevUserSwitcher";
import { PageHeader } from "@/components/layout/PageHeader";
import { canAccessPath } from "@/lib/auth";
import { isDemoMode } from "@/lib/client";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/cn";
import type { NavItem } from "@/lib/navigation";
import { MAIN_NAV } from "@/lib/navigation";
import type { User } from "@/lib/schemas";

type AppShellProps = {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  headerActions?: React.ReactNode;
  fullBleed?: boolean;
  showTopBar?: boolean;
};

function isNavActive(
  pathname: string,
  href: string,
  match?: (pathname: string) => boolean,
) {
  if (match) return match(pathname);
  return pathname === href || pathname.startsWith(`${href}/`);
}

type SidebarContentProps = {
  pathname: string;
  user: User | null;
  visibleNav: NavItem[];
  logout: () => void;
  onNavigate?: () => void;
};

function SidebarContent({
  pathname,
  user,
  visibleNav,
  logout,
  onNavigate,
}: SidebarContentProps) {
  return (
    <>
      <Link
        href={user ? "/dashboard" : "/"}
        onClick={onNavigate}
        className="mb-6 flex items-center gap-2 px-2"
      >
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

      <div className="flex-1 space-y-1 overflow-y-auto">
        {visibleNav.map((item) => {
          const active = isNavActive(pathname, item.href, item.match);
          const Icon = item.icon;
          return (
            <Link
              key={`${item.href}-${item.label}`}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-secondary-container font-semibold text-on-secondary-container"
                  : "text-on-surface-variant hover:bg-surface-container-high",
              )}
            >
              <Icon className="size-5 shrink-0" />
              <span>{item.label}</span>
              {item.badge ? (
                <span className="ml-auto rounded-full bg-error px-2 py-0.5 text-[10px] font-bold text-white">
                  {item.badge}
                </span>
              ) : null}
            </Link>
          );
        })}
      </div>

      <div className="mt-auto space-y-1 border-t border-outline-variant pt-2">
        <Link
          href="/"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-on-surface-variant transition-colors hover:bg-surface-container-high"
        >
          ← Back to landing
        </Link>
        {user ? (
          <button
            type="button"
            onClick={() => {
              logout();
              onNavigate?.();
            }}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-on-surface-variant transition-colors hover:bg-surface-container-high"
          >
            <LogOut className="size-5" />
            Logout
          </button>
        ) : null}
      </div>
    </>
  );
}

export function AppShell({
  children,
  title,
  subtitle,
  headerActions,
  fullBleed = false,
  showTopBar = true,
}: AppShellProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const visibleNav = useMemo(() => {
    return MAIN_NAV.filter((item) => {
      if (!item.roles) return true;
      if (!user) return false;
      return item.roles.includes(user.role);
    }).filter((item) => canAccessPath(user?.role, item.href));
  }, [user]);

  const greeting = user?.name?.split(" ")[0] ?? "there";

  return (
    <div className="flex h-screen overflow-hidden bg-background text-on-surface">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-3 focus:py-2 focus:shadow-soft"
      >
        Skip to content
      </a>

      <nav
        aria-label="Primary"
        className="hidden w-64 shrink-0 flex-col border-r border-outline-variant bg-surface-container-low p-4 md:flex"
      >
        <SidebarContent
          pathname={pathname}
          user={user}
          visibleNav={visibleNav}
          logout={logout}
        />
      </nav>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Close menu"
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileOpen(false)}
          />
          <nav className="relative flex h-full w-72 flex-col border-r border-outline-variant bg-surface-container-low p-4 shadow-soft">
            <button
              type="button"
              aria-label="Close"
              className="absolute right-3 top-3 rounded-md p-1 hover:bg-surface-container-high"
              onClick={() => setMobileOpen(false)}
            >
              <X className="size-5" />
            </button>
            <SidebarContent
              pathname={pathname}
              user={user}
              visibleNav={visibleNav}
              logout={logout}
              onNavigate={() => setMobileOpen(false)}
            />
          </nav>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {showTopBar ? (
          <header className="flex h-16 shrink-0 items-center justify-between border-b border-outline-variant bg-surface px-4 sm:px-8">
            <div className="flex items-center gap-3">
              <button
                type="button"
                className="rounded-md border border-border-base p-2 md:hidden"
                aria-label="Open menu"
                onClick={() => setMobileOpen(true)}
              >
                <Menu className="size-4" />
              </button>
              <div className="hidden items-center gap-3 sm:flex">
                <h2 className="text-base font-semibold text-on-surface">
                  Good morning, {greeting}
                </h2>
                <div className="mx-1 h-4 w-px bg-outline-variant" />
                <button
                  type="button"
                  className="inline-flex items-center gap-1 rounded-md border border-outline-variant px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-on-surface"
                >
                  <Building2 className="size-3.5" />
                  {user?.organization_name ?? "Demo Tenant"}
                  <ChevronDown className="size-3.5" />
                </button>
                <div
                  className={cn(
                    "flex items-center gap-1.5 rounded-md px-2 py-1",
                    isDemoMode()
                      ? "bg-surface-container-highest"
                      : "bg-secondary-container",
                  )}
                >
                  <span
                    className={cn(
                      "size-2 rounded-full",
                      isDemoMode() ? "bg-warning" : "bg-success",
                    )}
                  />
                  <span className="text-xs font-semibold uppercase tracking-wide">
                    {isDemoMode() ? "Demo" : "Live"}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 sm:gap-6">
              {user ? (
                <div className="hidden text-right sm:block">
                  <p className="text-sm font-medium">{user.email}</p>
                  <p className="text-xs capitalize text-on-surface-variant">
                    {user.role}
                  </p>
                </div>
              ) : null}
              {isDemoMode() ? <DevUserSwitcher /> : null}

              <div className="hidden flex-col items-end lg:flex">
                <div className="mb-1 flex items-center gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-on-surface-variant">
                    AI Quota
                  </span>
                  <span className="tabular-nums text-sm">78%</span>
                </div>
                <div className="h-1.5 w-32 overflow-hidden rounded-full bg-surface-variant">
                  <div className="h-full w-[78%] bg-secondary" />
                </div>
              </div>

              <button
                type="button"
                aria-label="Notifications"
                className="flex size-8 items-center justify-center rounded-full border border-outline-variant hover:bg-surface-container-low"
              >
                <Bell className="size-4 text-on-surface-variant" />
              </button>
            </div>
          </header>
        ) : null}

        {title ? (
          <PageHeader
            title={title}
            subtitle={subtitle}
            actions={headerActions}
          />
        ) : null}

        <main
          id="main"
          className={cn(
            "flex-1 overflow-hidden",
            !fullBleed && "overflow-y-auto bg-canvas p-8",
          )}
        >
          {fullBleed ? children : (
            <div className="mx-auto max-w-[1440px]">{children}</div>
          )}
        </main>
      </div>
    </div>
  );
}
