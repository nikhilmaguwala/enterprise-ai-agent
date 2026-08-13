"use client";

import { useCallback, useMemo, useSyncExternalStore } from "react";
import {
  clearAccessToken,
  getAccessToken,
  getStoredUser,
  subscribeAuth,
} from "@/lib/auth";
import type { User } from "@/lib/schemas";

function getTokenSnapshot() {
  return getAccessToken();
}

function getUserSnapshot() {
  const user = getStoredUser();
  return user ? JSON.stringify(user) : null;
}

function getServerSnapshot() {
  return null;
}

export function useAuth() {
  const token = useSyncExternalStore(
    subscribeAuth,
    getTokenSnapshot,
    getServerSnapshot,
  );
  const userJson = useSyncExternalStore(
    subscribeAuth,
    getUserSnapshot,
    getServerSnapshot,
  );

  const user = useMemo<User | null>(() => {
    if (!userJson) return null;
    try {
      return JSON.parse(userJson) as User;
    } catch {
      return null;
    }
  }, [userJson]);

  const refresh = useCallback(() => {
    // Storage writes already notify; this is a no-op escape hatch for callers.
  }, []);

  const logout = useCallback(() => {
    clearAccessToken();
  }, []);

  return {
    token,
    user,
    ready: true,
    refresh,
    logout,
    isAuthenticated: Boolean(token),
  };
}
