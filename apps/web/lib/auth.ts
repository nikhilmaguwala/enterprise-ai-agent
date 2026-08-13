import type { Role, User } from "@/lib/schemas";

const TOKEN_KEY = "ea_access_token";
const USER_KEY = "ea_user";
const AUTH_EVENT = "ea-auth-changed";

function canUseStorage(): boolean {
  return typeof window !== "undefined";
}

export function notifyAuthChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function subscribeAuth(onStoreChange: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  const onStorage = (event: StorageEvent) => {
    if (event.key === TOKEN_KEY || event.key === USER_KEY) {
      onStoreChange();
    }
  };
  window.addEventListener("storage", onStorage);
  window.addEventListener(AUTH_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(AUTH_EVENT, onStoreChange);
  };
}

export function getAccessToken(): string | null {
  if (!canUseStorage()) return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  if (!canUseStorage()) return;
  window.localStorage.setItem(TOKEN_KEY, token);
  notifyAuthChanged();
}

export function clearAccessToken(): void {
  if (!canUseStorage()) return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  notifyAuthChanged();
}

export function getStoredUser(): User | null {
  if (!canUseStorage()) return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function setStoredUser(user: User): void {
  if (!canUseStorage()) return;
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  notifyAuthChanged();
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}

/** Role-gated nav visibility for demo UX. */
export function canAccessPath(role: Role | undefined, path: string): boolean {
  const publicPaths = ["/", "/dashboard", "/chat", "/architecture"];
  if (!role) {
    return publicPaths.some(
      (p) => path === p || path.startsWith(`${p}/`),
    );
  }
  if (role === "customer") {
    return ["/", "/dashboard", "/chat", "/architecture"].some(
      (p) => path === p || path.startsWith(`${p}/`),
    );
  }
  if (role === "agent") {
    return (
      !path.startsWith("/operations") && !path.startsWith("/evaluations")
    );
  }
  return true;
}

export const DEV_USERS = [
  {
    email: "customer@acme-demo.test",
    label: "Customer (Acme)",
    role: "customer" as const,
  },
  {
    email: "agent@acme-demo.test",
    label: "Support agent",
    role: "agent" as const,
  },
  {
    email: "supervisor@acme-demo.test",
    label: "Supervisor",
    role: "supervisor" as const,
  },
  {
    email: "admin@acme-demo.test",
    label: "Admin",
    role: "admin" as const,
  },
  {
    email: "customer@globex-demo.test",
    label: "Customer (Globex)",
    role: "customer" as const,
  },
] as const;
