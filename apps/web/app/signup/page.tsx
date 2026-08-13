"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LandingHeader } from "@/components/marketing/LandingHeader";
import { Button } from "@/components/ui/Button";
import { registerAccount } from "@/lib/client";

export default function SignUpPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [starterOrder, setStarterOrder] = useState<string | null>(null);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const data = await registerAccount({
        email,
        password,
        fullName,
        companyName,
      });
      setStarterOrder(data.starter_order_number ?? null);
      router.push("/chat");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-on-surface">
      <LandingHeader />
      <main className="mx-auto flex max-w-md flex-col px-6 py-16">
        <h1 className="text-3xl font-semibold text-primary">Create your workspace</h1>
        <p className="mt-2 text-sm text-on-surface-variant">
          Real account with your company, demo order, and AI support chat.
        </p>
        <form onSubmit={(e) => void onSubmit(e)} className="mt-8 space-y-4">
          <label className="block text-sm">
            <span className="font-medium">Full name</span>
            <input
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-outline-variant bg-surface px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium">Company</span>
            <input
              required
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-outline-variant bg-surface px-3 py-2"
            />
          </label>
          <label className="block text-sm">
            <span className="font-medium">Work email</span>
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
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-outline-variant bg-surface px-3 py-2"
            />
          </label>
          {error ? <p className="text-sm text-danger">{error}</p> : null}
          {starterOrder ? (
            <p className="text-sm text-success">
              Workspace ready. Starter order: {starterOrder}
            </p>
          ) : null}
          <Button type="submit" disabled={busy} className="w-full justify-center">
            {busy ? "Creating account…" : "Create account"}
          </Button>
        </form>
        <p className="mt-6 text-sm text-on-surface-variant">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-secondary hover:underline">
            Sign in
          </Link>
        </p>
      </main>
    </div>
  );
}
