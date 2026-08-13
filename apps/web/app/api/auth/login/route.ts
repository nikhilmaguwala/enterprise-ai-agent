import { z } from "zod";
import { NextResponse } from "next/server";
import { env } from "@/lib/env";
import { DevLoginResponseSchema } from "@/lib/schemas";

const BodySchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

export async function POST(request: Request) {
  if (!env.registrationEnabled) {
    return NextResponse.json({ detail: "Login is disabled" }, { status: 403 });
  }

  let body: z.infer<typeof BodySchema>;
  try {
    body = BodySchema.parse(await request.json());
  } catch {
    return NextResponse.json({ detail: "Invalid login payload" }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${env.apiUrl.replace(/\/$/, "")}/api/v1/auth/login`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
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
    return NextResponse.json(DevLoginResponseSchema.parse(parsed));
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
