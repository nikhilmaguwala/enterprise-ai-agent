import { NextResponse } from "next/server";
import { env } from "@/lib/env";
import { MeResponseSchema } from "@/lib/schemas";

export async function GET(request: Request) {
  const authorization = request.headers.get("authorization");
  if (!authorization) {
    return NextResponse.json({ detail: "missing bearer token" }, { status: 401 });
  }

  try {
    const upstream = await fetch(`${env.apiUrl.replace(/\/$/, "")}/api/v1/auth/me`, {
      headers: { Accept: "application/json", Authorization: authorization },
      cache: "no-store",
    });
    const text = await upstream.text();
    const parsed = text ? (JSON.parse(text) as unknown) : null;
    if (!upstream.ok) {
      return NextResponse.json(parsed ?? { detail: upstream.statusText }, {
        status: upstream.status,
      });
    }
    const data = MeResponseSchema.parse(parsed);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error
            ? `Auth service unreachable: ${error.message}`
            : "Auth service unreachable",
      },
      { status: 502 },
    );
  }
}
