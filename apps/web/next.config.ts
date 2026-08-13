import type { NextConfig } from "next";

const LOCAL_API_URL = "http://localhost:8000";

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
  return LOCAL_API_URL;
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
