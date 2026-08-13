"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LandingHeader } from "@/components/marketing/LandingHeader";
import { Button } from "@/components/ui/Button";
import { loginAccount } from "@/lib/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await loginAccount({ email, password });
      router.push("/chat");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-on-surface">
      <LandingHeader />
      <main className="mx-auto flex max-w-md flex-col px-6 py-16">
        <h1 className="text-3xl font-semibold text-primary">Sign in</h1>
        <p className="mt-2 text-sm text-on-surface-variant">
          Use the email and password from your workspace signup or team invite.
        </p>
        <form onSubmit={(e) => void onSubmit(e)} className="mt-8 space-y-4">
          <label className="block text-sm">
            <span className="font-medium">Email</span>
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg border border-outline-variant bg-surface px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium">Password</span>
            <input
              required
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-outline-variant bg-surface px-3 py-2"
            />
          </label>
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          <Button type="submit" disabled={busy} className="w-full justify-center">
            {busy ? "Signing in…" : "Sign in"}
          </Button>
        </form>
        <p className="mt-6 text-sm text-on-surface-variant">
          New here?{" "}
          <Link href="/signup" className="font-medium text-secondary hover:underline">
            Create an account
          </Link>
        </p>
      </main>
    </div>
  );
}
