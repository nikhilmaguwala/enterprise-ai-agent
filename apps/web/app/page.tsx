import type { Metadata } from "next";
import { LandingPage } from "@/components/marketing/LandingPage";

export const metadata: Metadata = {
  title: "ResolveAI — Explainable, Actionable, Safe AI Support",
  description:
    "Enterprise AI support with grounded citations, human approvals, and observable agent operations.",
};

export default function HomePage() {
  return <LandingPage />;
}
