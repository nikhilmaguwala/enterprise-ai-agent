import { env } from "@/lib/env";
import { getAccessToken } from "@/lib/auth";

export type SseHandlers = {
  onEvent: (event: { id?: string; type: string; data: unknown }) => void;
  onOpen?: () => void;
  onError?: (error: Event) => void;
};

export type SseConnection = {
  close: () => void;
  getLastEventId: () => string | undefined;
};

/**
 * EventSource wrapper with Last-Event-ID reconnection.
 * Auth token is passed as a query param because EventSource cannot set headers.
 */
export function connectSse(
  path: string,
  handlers: SseHandlers,
  options?: { lastEventId?: string; token?: string | null },
): SseConnection {
  let lastEventId = options?.lastEventId;
  let source: EventSource | null = null;
  let closed = false;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let attempt = 0;

  const open = () => {
    if (closed) return;

    const base = env.apiUrl.replace(/\/$/, "");
    const normalized = path.startsWith("/") ? path : `/${path}`;
    const url = new URL(`${base}${normalized}`);
    const token = options?.token ?? getAccessToken();
    if (token) {
      url.searchParams.set("access_token", token);
    }
    if (lastEventId) {
      url.searchParams.set("last_event_id", lastEventId);
    }

    source = new EventSource(url.toString());

    source.onopen = () => {
      attempt = 0;
      handlers.onOpen?.();
    };

    source.onmessage = (event) => {
      if (event.lastEventId) {
        lastEventId = event.lastEventId;
      }
      let data: unknown = event.data;
      try {
        data = JSON.parse(event.data) as unknown;
      } catch {
        // keep raw string
      }
      handlers.onEvent({
        id: event.lastEventId || undefined,
        type: event.type || "message",
        data,
      });
    };

    const namedTypes = [
      "message_delta",
      "message_completed",
      "tool_started",
      "tool_finished",
      "approval_required",
      "run_status",
      "error",
      "ping",
    ];

    for (const type of namedTypes) {
      source.addEventListener(type, (raw) => {
        const event = raw as MessageEvent<string>;
        if (event.lastEventId) {
          lastEventId = event.lastEventId;
        }
        let data: unknown = event.data;
        try {
          data = JSON.parse(event.data) as unknown;
        } catch {
          // keep raw
        }
        handlers.onEvent({
          id: event.lastEventId || undefined,
          type,
          data,
        });
      });
    }

    source.onerror = (error) => {
      handlers.onError?.(error);
      source?.close();
      source = null;
      if (closed) return;
      const delay = Math.min(1000 * 2 ** attempt, 15000);
      attempt += 1;
      reconnectTimer = setTimeout(open, delay);
    };
  };

  open();

  return {
    close: () => {
      closed = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      source?.close();
      source = null;
    },
    getLastEventId: () => lastEventId,
  };
}
