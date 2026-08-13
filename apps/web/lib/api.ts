import { z } from "zod";
import { env } from "@/lib/env";
import { clearAccessToken, getAccessToken } from "@/lib/auth";
import { ApiErrorSchema } from "@/lib/schemas";

export class ApiClientError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(message: string, status: number, body: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.body = body;
  }
}

type ApiOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  schema?: z.ZodType;
  signal?: AbortSignal;
  headers?: Record<string, string>;
};

function buildUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  // Browser calls stay same-origin; Next rewrites proxy to the API upstream.
  if (typeof window !== "undefined") {
    return normalized;
  }
  return `${env.apiUrl.replace(/\/$/, "")}${normalized}`;
}

export async function apiFetch<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const {
    method = "GET",
    body,
    token = getAccessToken(),
    schema,
    signal,
    headers = {},
  } = options;

  const requestHeaders: Record<string, string> = {
    Accept: "application/json",
    ...headers,
  };

  if (body !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
  }

  if (token) {
    requestHeaders.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      method,
      headers: requestHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
      cache: "no-store",
    });
  } catch (error) {
    throw new ApiClientError(
      error instanceof Error ? error.message : "Network request failed",
      0,
      null,
    );
  }

  const text = await response.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text) as unknown;
    } catch {
      parsed = text;
    }
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearAccessToken();
    }
    const err = ApiErrorSchema.safeParse(parsed);
    const message =
      (err.success && (err.data.message ?? stringifyDetail(err.data.detail))) ||
      `Request failed (${response.status})`;
    throw new ApiClientError(message, response.status, parsed);
  }

  if (schema) {
    return schema.parse(parsed) as T;
  }
  return parsed as T;
}

function stringifyDetail(detail: unknown): string | undefined {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return JSON.stringify(detail);
  return undefined;
}

export function apiUrl(path: string): string {
  return buildUrl(path);
}

export async function apiUpload(
  pathOrUrl: string,
  file: File,
  options: { token?: string | null } = {},
): Promise<void> {
  const url = pathOrUrl.startsWith("http") ? pathOrUrl : buildUrl(pathOrUrl);
  const token = options.token ?? getAccessToken();

  const form = new FormData();
  form.append("file", file);

  const headers: Record<string, string> = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(url, {
      method: "PUT",
      headers,
      body: form,
    });
  } catch (error) {
    throw new ApiClientError(
      error instanceof Error ? error.message : "Upload failed",
      0,
      null,
    );
  }

  if (!response.ok) {
    const text = await response.text();
    let parsed: unknown = text;
    try {
      parsed = JSON.parse(text) as unknown;
    } catch {
      // keep text
    }
    if (response.status === 401) {
      clearAccessToken();
    }
    throw new ApiClientError(
      `Upload failed (${response.status})`,
      response.status,
      parsed,
    );
  }
}
