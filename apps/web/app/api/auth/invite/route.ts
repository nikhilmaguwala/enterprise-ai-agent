import { z } from "zod";
import { NextResponse } from "next/server";
import { env } from "@/lib/env";
import { InviteResponseSchema } from "@/lib/schemas";

const BodySchema = z.object({
  email: z.string().email(),
  full_name: z.string().min(1),
  role: z.string().min(1),
});

export async function POST(request: Request) {
  if (!env.registrationEnabled) {
    return NextResponse.json({ detail: "Invites are disabled" }, { status: 403 });
  }

  const authorization = request.headers.get("authorization");
  if (!authorization) {
    return NextResponse.json({ detail: "missing bearer token" }, { status: 401 });
  }

  let body: z.infer<typeof BodySchema>;
  try {
    body = BodySchema.parse(await request.json());
  } catch {
    return NextResponse.json({ detail: "Invalid invite payload" }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${env.apiUrl.replace(/\/$/, "")}/api/v1/auth/invite`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: authorization,
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const text = await upstream.text();
    const parsed = text ? (JSON.parse(text) as unknown) : null;
    if (!upstream.ok) {
      return NextResponse.json(parsed ?? { detail: upstream.statusText }, {
        status: upstream.status,
      });
    }
    return NextResponse.json(InviteResponseSchema.parse(parsed));
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
