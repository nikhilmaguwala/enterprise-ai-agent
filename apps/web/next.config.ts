import type { NextConfig } from "next";

const LOCAL_API_URL = "http://localhost:8000";
const PRODUCTION_API_URL =
  "https://enterprise-ai-support-agent.fastapicloud.dev";

function resolveUpstreamApiUrl(): string {
  const candidates = [process.env.API_URL, process.env.NEXT_PUBLIC_API_URL];
  for (const candidate of candidates) {
    if (
      candidate &&
      !candidate.includes("SENSITIVE") &&
      /^https?:\/\//.test(candidate)
    ) {
      return candidate.replace(/\/$/, "");
    }
  }
  return process.env.NODE_ENV === "production"
    ? PRODUCTION_API_URL
    : LOCAL_API_URL;
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    const upstream = resolveUpstreamApiUrl();
    return [
      {
        source: "/api/v1/:path*",
        destination: `${upstream}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
