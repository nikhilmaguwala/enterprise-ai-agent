import Link from "next/link";
import {
  ArrowRight,
  Bot,
  CheckCircle2,
  GitBranch,
  Shield,
  Sparkles,
} from "lucide-react";
import { LandingHeader } from "@/components/marketing/LandingHeader";
import { Button } from "@/components/ui/Button";

const features = [
  {
    title: "Grounded by policy",
    body: "Hybrid RAG attaches citations to every claim so agents never guess in a vacuum.",
    icon: Sparkles,
  },
  {
    title: "Human-in-the-loop",
    body: "Address changes and mutations pause for explicit approval before ERP writes.",
    icon: Shield,
  },
  {
    title: "Observable runs",
    body: "LangGraph steps, tool progress, and evaluation suites in one operator console.",
    icon: GitBranch,
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface">
      <LandingHeader />

      <main className="mx-auto max-w-[1440px]">
        <section className="relative grid items-center gap-12 overflow-hidden px-6 py-16 md:grid-cols-2 md:px-8 md:py-24">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 opacity-40"
            style={{
              background:
                "radial-gradient(600px 400px at 20% 0%, #dbe1ff 0%, transparent 60%), radial-gradient(500px 350px at 80% 20%, #eaddff 0%, transparent 55%)",
            }}
          />

          <div className="relative z-10">
            <span className="ai-chip mb-4 inline-flex">
              <Sparkles className="size-3.5" />
              Enterprise Support Automation
            </span>
            <h1 className="text-4xl font-semibold tracking-tight text-primary sm:text-5xl sm:leading-[1.1]">
              AI support that can{" "}
              <span className="bg-gradient-to-br from-ai-text to-secondary bg-clip-text text-transparent">
                explain, act and escalate
              </span>{" "}
              safely.
            </h1>
            <p className="mt-4 max-w-xl text-lg text-on-surface-variant">
              ResolveAI connects knowledge, customer records, orders and delivery
              systems to resolve support requests with citations, controlled actions
              and complete auditability.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/chat">
                <Button icon={<ArrowRight className="size-4" />}>
                  Try the live demo
                </Button>
              </Link>
              <Link href="/architecture">
                <Button variant="secondary" icon={<GitBranch className="size-4" />}>
                  View architecture
                </Button>
              </Link>
            </div>
          </div>

          <div className="relative z-10">
            <div className="flex h-[480px] flex-col overflow-hidden rounded-xl border border-border-base bg-surface shadow-soft">
              <div className="flex items-center justify-between border-b border-border-base bg-table-header px-4 py-2">
                <div className="flex gap-1.5">
                  <span className="size-3 rounded-full bg-red-400" />
                  <span className="size-3 rounded-full bg-yellow-400" />
                  <span className="size-3 rounded-full bg-green-400" />
                </div>
                <span className="text-xs font-semibold uppercase tracking-wide text-on-surface-variant">
                  Active Run: #A-7492
                </span>
              </div>
              <div className="flex flex-1 flex-col gap-3 overflow-y-auto bg-canvas p-4">
                <div className="ml-auto max-w-[85%] rounded-lg rounded-tr-none bg-surface-variant px-3 py-2 text-sm shadow-soft">
                  My order #88492 is delayed. Can you check where it is?
                </div>
                <div className="max-w-[85%] space-y-2">
                  <div className="flex items-center gap-2 rounded-lg border border-ai-border bg-surface px-2 py-1.5 text-xs text-on-surface-variant">
                    <Bot className="size-3.5 animate-pulse text-ai-text" />
                    Querying Order System for #88492…
                  </div>
                  <div className="flex items-center gap-2 rounded-lg border border-ai-border bg-surface px-2 py-1.5 text-xs text-on-surface-variant">
                    <CheckCircle2 className="size-3.5 text-success" />
                    SwiftShip API: Status &quot;In Transit — Delayed&quot;
                  </div>
                </div>
                <div className="flex max-w-[85%] gap-2">
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-container text-on-primary-container">
                    <Bot className="size-4" />
                  </div>
                  <div className="rounded-lg rounded-tl-none border border-border-base bg-surface p-3 text-sm shadow-soft">
                    I found your order #88492. It is delayed by SwiftShip due to a
                    regional hub disruption.
                    <div className="mt-2 flex items-center justify-between rounded border border-ai-border bg-ai-bg p-2 text-xs">
                      <span className="font-medium text-ai-text">
                        Proposed: Address Change
                      </span>
                      <span className="rounded bg-ai-text px-2 py-0.5 text-white">
                        Request Approval
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-t border-outline-variant bg-surface-container-lowest px-6 py-16 md:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-2xl font-semibold text-on-surface">
              Built for enterprise operators
            </h2>
            <p className="mt-2 text-on-surface-variant">
              Every surface follows the ResolveAI design system — dense, auditable,
              and production-ready.
            </p>
          </div>
          <div className="mx-auto mt-10 grid max-w-5xl gap-6 md:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <article key={feature.title} className="glass-card p-5">
                  <Icon className="size-5 text-secondary" />
                  <h3 className="mt-3 font-semibold text-on-surface">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-sm text-on-surface-variant">
                    {feature.body}
                  </p>
                </article>
              );
            })}
          </div>
        </section>
      </main>

      <footer className="border-t border-outline-variant bg-surface-container-lowest">
        <div className="mx-auto flex max-w-[1440px] flex-col items-center justify-between gap-6 px-6 py-10 md:flex-row md:px-8">
          <div className="text-center md:text-left">
            <p className="font-bold text-primary">ResolveAI</p>
            <p className="mt-1 text-sm text-on-surface-variant">
              © 2026 ResolveAI Enterprise. All rights reserved.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-on-surface-variant">
            <Link href="/architecture" className="hover:text-secondary">
              Architecture
            </Link>
            <Link href="/dashboard" className="hover:text-secondary">
              Overview
            </Link>
            <Link href="/chat" className="hover:text-secondary">
              Live demo
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
