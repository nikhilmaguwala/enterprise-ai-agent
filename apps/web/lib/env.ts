/**
 * Public env only — never put secrets in NEXT_PUBLIC_* vars.
 */
const LOCAL_API_URL = "http://localhost:8000";
const LOCAL_APP_URL = "http://localhost:3000";

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
  return LOCAL_API_URL;
}

function resolveAppUrl(): string {
  const raw = process.env.NEXT_PUBLIC_APP_URL;
  if (isUsableHttpUrl(raw)) {
    return raw.replace(/\/$/, "");
  }
  return LOCAL_APP_URL;
}

export const env = {
  apiUrl: resolveApiUrl(),
  appUrl: resolveAppUrl(),
  devAuthEnabled: process.env.NEXT_PUBLIC_DEV_AUTH_ENABLED === "true",
  registrationEnabled: process.env.NEXT_PUBLIC_REGISTRATION_ENABLED !== "false",
} as const;
