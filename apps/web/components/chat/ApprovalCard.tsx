"use client";

import { useState } from "react";
import { AlertTriangle, Check } from "lucide-react";
import type { Approval } from "@/lib/schemas";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";

type ApprovalCardProps = {
  approval: Approval;
  onDecide?: (
    approvalId: string,
    decision: "approve" | "reject",
  ) => Promise<void> | void;
  busy?: boolean;
};

export function ApprovalCard({
  approval,
  onDecide,
  busy = false,
}: ApprovalCardProps) {
  const [localBusy, setLocalBusy] = useState(false);
  const pending = approval.status === "pending";
  const loading = busy || localBusy;

  async function handle(decision: "approve" | "reject") {
    if (!onDecide || loading) return;
    setLocalBusy(true);
    try {
      await onDecide(approval.id, decision);
    } finally {
      setLocalBusy(false);
    }
  }

  const payload = approval.payload as Record<string, unknown> | undefined;
  const currentAddress =
    typeof payload?.current_address === "string"
      ? payload.current_address
      : null;
  const proposedAddress =
    typeof payload?.proposed_address === "string"
      ? payload.proposed_address
      : null;

  return (
    <div className="mt-3 w-full rounded-lg border border-border-base bg-surface p-4 shadow-soft">
      <div className="mb-3 flex items-center gap-2 border-b border-border-base pb-3">
        <AlertTriangle className="size-4 text-warning" />
        <span className="text-sm font-semibold text-on-surface">
          Approval Required: {approval.action_type.replaceAll("_", " ")}
        </span>
        <div className="ml-auto">
          <StatusBadge label={approval.status} />
        </div>
      </div>

      <p className="text-sm text-on-surface-variant">{approval.summary}</p>

      {currentAddress || proposedAddress ? (
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {currentAddress ? (
            <div className="rounded-md border border-border-base bg-surface-container-low p-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-outline">
                Current
              </span>
              <p className="mt-1 text-sm text-on-surface">{currentAddress}</p>
            </div>
          ) : null}
          {proposedAddress ? (
            <div className="rounded-md border border-ai-border bg-ai-bg p-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-ai-text">
                Proposed
              </span>
              <p className="mt-1 text-sm text-on-surface">{proposedAddress}</p>
            </div>
          ) : null}
        </div>
      ) : approval.payload ? (
        <pre className="mt-3 overflow-x-auto rounded-md border border-border-base bg-surface-container-low p-3 text-xs text-on-surface">
          {JSON.stringify(approval.payload, null, 2)}
        </pre>
      ) : null}

      {pending && onDecide ? (
        <div className="mt-4 flex justify-end gap-2">
          <Button
            variant="secondary"
            disabled={loading}
            onClick={() => void handle("reject")}
          >
            Reject
          </Button>
          <Button
            disabled={loading}
            icon={<Check className="size-4" />}
            onClick={() => void handle("approve")}
          >
            Approve Change
          </Button>
        </div>
      ) : null}
    </div>
  );
}
