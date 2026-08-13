import {
  BarChart3,
  Database,
  Inbox,
  LayoutDashboard,
  MessageSquare,
  Network,
  Settings2,
  type LucideIcon,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  roles?: readonly string[] | null;
  badge?: string;
  match?: (pathname: string) => boolean;
};

/** Sidebar links — only real routes, no disabled placeholders. */
export const MAIN_NAV: NavItem[] = [
  {
    href: "/dashboard",
    label: "Overview",
    icon: LayoutDashboard,
    roles: null,
    match: (pathname) => pathname.startsWith("/dashboard"),
  },
  {
    href: "/chat",
    label: "Conversations",
    icon: MessageSquare,
    roles: null,
    match: (pathname) => pathname.startsWith("/chat"),
  },
  {
    href: "/inbox",
    label: "Support Inbox",
    icon: Inbox,
    roles: ["agent", "supervisor", "admin"],
    match: (pathname) => pathname.startsWith("/inbox"),
  },
  {
    href: "/knowledge",
    label: "Knowledge",
    icon: Database,
    roles: ["agent", "supervisor", "admin"],
    match: (pathname) => pathname.startsWith("/knowledge"),
  },
  {
    href: "/evaluations",
    label: "Evaluations",
    icon: BarChart3,
    roles: ["supervisor", "admin"],
    match: (pathname) => pathname.startsWith("/evaluations"),
  },
  {
    href: "/operations",
    label: "Operations",
    icon: Settings2,
    roles: ["admin"],
    match: (pathname) => pathname.startsWith("/operations"),
  },
  {
    href: "/architecture",
    label: "Architecture",
    icon: Network,
    roles: null,
    match: (pathname) => pathname.startsWith("/architecture"),
  },
];
