/**
 * Public env only — never put secrets in NEXT_PUBLIC_* vars.
 */
const LOCAL_API_URL = "http://localhost:8000";
const PRODUCTION_API_URL =
  "https://enterprise-ai-support-agent.fastapicloud.dev";

function isUsableHttpUrl(raw: string | undefined): raw is string {
  if (!raw || raw.includes("SENSITIVE")) return false;
  try {
    const parsed = new URL(raw);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

function resolveApiUrl(): string {
  const candidates = [process.env.API_URL, process.env.NEXT_PUBLIC_API_URL];
  for (const candidate of candidates) {
    if (isUsableHttpUrl(candidate)) {
      return candidate.replace(/\/$/, "");
    }
  }
  return process.env.NODE_ENV === "production"
    ? PRODUCTION_API_URL
    : LOCAL_API_URL;
}

function resolveAppUrl(): string {
  const raw = process.env.NEXT_PUBLIC_APP_URL;
  if (isUsableHttpUrl(raw)) {
    return raw.replace(/\/$/, "");
  }
  return process.env.NODE_ENV === "production"
    ? "https://enterprise-ai-support-agent.vercel.app"
    : "http://localhost:3000";
}

export const env = {
  apiUrl: resolveApiUrl(),
  appUrl: resolveAppUrl(),
  devAuthEnabled: process.env.NEXT_PUBLIC_DEV_AUTH_ENABLED === "true",
  registrationEnabled: process.env.NEXT_PUBLIC_REGISTRATION_ENABLED !== "false",
} as const;
