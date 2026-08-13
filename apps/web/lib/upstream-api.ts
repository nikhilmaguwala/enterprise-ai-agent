import { env } from "@/lib/env";

const HOP_BY_HOP = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailers",
  "transfer-encoding",
  "upgrade",
]);

export function upstreamApiUrl(path: string, search = ""): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${env.apiUrl.replace(/\/$/, "")}${normalized}`);
  if (search) {
    url.search = search.startsWith("?") ? search.slice(1) : search;
  }
  return url.toString();
}

export async function proxyToUpstream(request: Request, apiPath: string): Promise<Response> {
  const requestUrl = new URL(request.url);
  const upstreamUrl = upstreamApiUrl(apiPath, requestUrl.search);

  const headers = new Headers();
  const forward = [
    "authorization",
    "accept",
    "content-type",
    "idempotency-key",
    "last-event-id",
  ] as const;

  for (const name of forward) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(upstreamUrl, init);
  } catch (error) {
    return Response.json(
      {
        detail:
          error instanceof Error
            ? `API unreachable: ${error.message}`
            : "API unreachable",
      },
      { status: 502 },
    );
  }

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (!HOP_BY_HOP.has(key.toLowerCase())) {
      responseHeaders.set(key, value);
    }
  });

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}
