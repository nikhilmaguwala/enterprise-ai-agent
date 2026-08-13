"use client";

import Link from "next/link";
import { useState } from "react";
import {
  CheckCircle2,
  Mail,
  Send,
  Shield,
  User,
  UserCog,
  UserRound,
  Users,
  XCircle,
} from "lucide-react";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { inviteTeamMember } from "@/lib/client";
import type { InviteRole } from "@/lib/schemas";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/cn";

const ROLE_OPTIONS: Array<{
  id: InviteRole;
  label: string;
  icon: typeof User;
}> = [
  { id: "customer", label: "Customer", icon: UserRound },
  { id: "agent", label: "Support agent", icon: User },
  { id: "supervisor", label: "Supervisor", icon: Users },
  { id: "admin", label: "Administrator", icon: UserCog },
];

const PERMISSIONS: Record<
  InviteRole,
  Array<{ allowed: boolean; text: string }>
> = {
  customer: [
    { allowed: true, text: "Chat with the AI about their orders." },
    { allowed: true, text: "Respond to approval prompts on their requests." },
    { allowed: false, text: "Cannot access team or operations settings." },
  ],
  agent: [
    { allowed: true, text: "View and respond to support conversations." },
    { allowed: true, text: "Access the knowledge base and agent runs." },
    { allowed: false, text: "Cannot invite team members or replay jobs." },
  ],
  supervisor: [
    { allowed: true, text: "Everything a support agent can do." },
    { allowed: true, text: "Approve risky actions such as address changes." },
    { allowed: true, text: "Access evaluations and inbox tooling." },
  ],
  admin: [
    { allowed: true, text: "Full workspace access including operations." },
    { allowed: true, text: "Invite teammates and manage integrations." },
    { allowed: true, text: "Configure knowledge and replay background jobs." },
  ],
};

export default function InviteTeamPage() {
  const { token, user } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<InviteRole>("agent");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ email: string; role: InviteRole } | null>(
    null,
  );

  const isAdmin = user?.role === "admin";

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await inviteTeamMember({ email, fullName, role });
      setSuccess({ email: result.email, role: result.role as InviteRole });
      setFullName("");
      setEmail("");
      setRole("agent");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invite failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell
      title="Invite team member"
      subtitle="Send a workspace invite with a temporary password by email."
    >
      {!token ? (
        <EmptyState
          title="Sign in required"
          description="Log in as a workspace admin to invite teammates."
          action={
            <Link href="/login">
              <Button>Sign in</Button>
            </Link>
          }
        />
      ) : !isAdmin ? (
        <EmptyState
          title="Admin access required"
          description="Only workspace administrators can invite new team members."
          action={
            <Link href="/dashboard">
              <Button variant="secondary">Back to overview</Button>
            </Link>
          }
        />
      ) : (
        <div className="mx-auto max-w-2xl">
          <Card padding={false} className="overflow-hidden">
            <div className="border-b border-outline-variant px-6 py-4">
              <h2 className="text-lg font-semibold text-on-surface">
                Invite team member
              </h2>
              <p className="mt-1 text-sm text-on-surface-variant">
                Send an invitation to join{" "}
                <span className="font-medium text-on-surface">
                  {user.organization_name ?? "your workspace"}
                </span>
                .
              </p>
            </div>

            <form onSubmit={(e) => void onSubmit(e)} className="space-y-6 p-6">
              <label className="block text-sm">
                <span className="font-medium">Full name</span>
                <input
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                  className="mt-1 w-full rounded-lg border border-outline-variant bg-surface px-3 py-2"
                />
              </label>

              <label className="block text-sm">
                <span className="font-medium">Email address</span>
                <div className="relative mt-1">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-on-surface-variant" />
                  <input
                    required
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="colleague@yourcompany.com"
                    className="w-full rounded-lg border border-outline-variant bg-surface py-2 pl-10 pr-3"
                  />
                </div>
              </label>

              <fieldset>
                <legend className="text-sm font-medium">Role assignment</legend>
                <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {ROLE_OPTIONS.map((option) => {
                    const Icon = option.icon;
                    const selected = role === option.id;
                    return (
                      <label
                        key={option.id}
                        className={cn(
                          "relative cursor-pointer rounded-lg border p-4 transition-colors",
                          selected
                            ? "border-secondary bg-secondary/5"
                            : "border-outline-variant hover:bg-surface-container-low",
                        )}
                      >
                        <input
                          type="radio"
                          name="role"
                          value={option.id}
                          checked={selected}
                          onChange={() => setRole(option.id)}
                          className="sr-only"
                        />
                        <div className="flex items-center gap-2">
                          <Icon
                            className={cn(
                              "size-4",
                              selected ? "text-secondary" : "text-on-surface-variant",
                            )}
                          />
                          <span
                            className={cn(
                              "text-sm font-semibold",
                              selected ? "text-secondary" : "text-on-surface",
                            )}
                          >
                            {option.label}
                          </span>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </fieldset>

              <div className="rounded-lg border border-outline-variant bg-surface-container-lowest p-4">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-on-surface">
                  <Shield className="size-4 text-on-surface-variant" />
                  Permission summary
                </h3>
                <ul className="mt-3 space-y-2">
                  {PERMISSIONS[role].map((item) => (
                    <li
                      key={item.text}
                      className={cn(
                        "flex items-start gap-2 text-sm",
                        item.allowed
                          ? "text-on-surface-variant"
                          : "text-outline",
                      )}
                    >
                      {item.allowed ? (
                        <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-secondary" />
                      ) : (
                        <XCircle className="mt-0.5 size-4 shrink-0" />
                      )}
                      <span>{item.text}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {error ? <p className="text-sm text-danger">{error}</p> : null}

              {success ? (
                <div className="rounded-lg border border-success-container bg-success-container/30 px-4 py-3 text-sm text-on-surface">
                  <p className="font-medium text-success">
                    Invitation sent to {success.email}
                  </p>
                  <p className="mt-1 text-on-surface-variant">
                    They will receive a temporary password by email and can sign in at{" "}
                    <Link href="/login" className="font-medium text-secondary hover:underline">
                      /login
                    </Link>
                    .
                  </p>
                </div>
              ) : null}

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-outline-variant pt-4">
                <p className="text-xs text-on-surface-variant">
                  Temporary password expires when they change it after first login.
                </p>
                <div className="flex gap-3">
                  <Link href="/dashboard">
                    <Button type="button" variant="secondary">
                      Cancel
                    </Button>
                  </Link>
                  <Button
                    type="submit"
                    disabled={busy}
                    icon={<Send className="size-4" />}
                  >
                    {busy ? "Sending…" : "Send invitation"}
                  </Button>
                </div>
              </div>
            </form>
          </Card>
        </div>
      )}
    </AppShell>
  );
}
