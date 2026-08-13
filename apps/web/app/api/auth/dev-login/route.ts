import { z } from "zod";
import { NextResponse } from "next/server";
import { env } from "@/lib/env";
import { DevLoginResponseSchema } from "@/lib/schemas";

const BodySchema = z.object({
  email: z.string().email(),
});

/**
 * Dev-only token exchange. Proxies to the backend so the browser
 * does not need CORS during local development.
 * Never accepts or stores Auth0 client secrets here.
 */
export async function POST(request: Request) {
  if (!env.devAuthEnabled) {
    return NextResponse.json(
      { detail: "Dev auth is disabled" },
      { status: 403 },
    );
  }

  let body: z.infer<typeof BodySchema>;
  try {
    body = BodySchema.parse(await request.json());
  } catch {
    return NextResponse.json({ detail: "Invalid email" }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${env.apiUrl.replace(/\/$/, "")}/api/v1/auth/dev-login`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: body.email }),
      cache: "no-store",
    });

    const text = await upstream.text();
    let parsed: unknown = null;
    if (text) {
      try {
        parsed = JSON.parse(text) as unknown;
      } catch {
        parsed = { detail: text };
      }
    }

    if (!upstream.ok) {
      return NextResponse.json(
        typeof parsed === "object" && parsed
          ? parsed
          : { detail: `Upstream auth failed (${upstream.status})` },
        { status: upstream.status },
      );
    }

    const data = DevLoginResponseSchema.parse(parsed);
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
