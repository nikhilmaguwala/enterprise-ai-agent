/**
 * Public env only — never put secrets in NEXT_PUBLIC_* vars.
 */
export const env = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  appUrl: process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
  devAuthEnabled: process.env.NEXT_PUBLIC_DEV_AUTH_ENABLED === "true",
} as const;
