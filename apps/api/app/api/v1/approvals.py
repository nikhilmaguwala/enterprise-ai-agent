"""Approval approve/reject endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.schemas import ApprovalDecision, ApprovalOut
from app.services.agent_runner import AgentRunner
from app.services.audit import AuditService
from app.services.idempotency import canonical_hash
from app.services.policy import PolicyEngine
from app.services.tenant import get_tenant_row, reject_org_spoof
from enterprise_integrations.gateway import ToolGateway

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/{approval_id}", response_model=ApprovalOut)
async def get_approval(
    approval_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> ApprovalOut:
    row = await get_tenant_row(db, m.Approval, approval_id, ctx)
    return ApprovalOut.model_validate(row)


async def _execute_address_change(
    *,
    settings: Settings,
    approval: m.Approval,
    ctx: ExecutionContext,
) -> dict:
    gateway = ToolGateway.from_settings(settings)
    payload = approval.payload or {}
    order_id = payload.get("order_id")
    address = payload.get("address") or {}
    if not order_id or not address:
        return {"ok": False, "error": "missing_order_or_address"}

    idem = payload.get("idempotency_key") or f"approval-{approval.id}-{canonical_hash(payload)[:12]}"
    result = await gateway.call(
        "erp.change_address",
        order_id=str(order_id),
        address=address,
        idempotency_key=str(idem),
        if_match=str(payload.get("if_match") or "1"),
    )
    verification: dict = {"verified": False}
    if result.ok:
        verify = await gateway.call("erp.get_order", order_id=str(order_id))
        if verify.ok:
            current = verify.data.get("shipping_address") or {}
            verification = {
                "verified": current.get("postal_code") == address.get("postal_code")
                and current.get("line1") == address.get("line1"),
                "order": verify.data,
            }
    return {
        "ok": result.ok,
        "data": result.data,
        "error": str(result.error) if result.error else None,
        "verification": verification,
        "idempotency_key": idem,
    }


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve(
    approval_id: UUID,
    body: ApprovalDecision,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ApprovalOut:
    reject_org_spoof(body.organization_id, ctx)
    ctx.require_permission("approvals:respond")
    approval = await get_tenant_row(db, m.Approval, approval_id, ctx)
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"approval is {approval.status}")

    # Re-validate before marking approved
    payload = approval.payload or {}
    if approval.action_type == "address_change":
        order_id = payload.get("order_id")
        if order_id:
            order = await get_tenant_row(db, m.Order, UUID(str(order_id)), ctx)
            shipment = None
            if order.tracking_number:
                from sqlalchemy import select

                shipment = (
                    await db.execute(
                        select(m.Shipment).where(
                            m.Shipment.organization_id == ctx.organization_id,
                            m.Shipment.order_id == order.id,
                        )
                    )
                ).scalar_one_or_none()
            decision = PolicyEngine().evaluate_address_change(
                order_status=order.status,
                shipment_status=shipment.status if shipment else None,
                current_address=order.shipping_address or {},
                proposed_address=(payload.get("address") or {}),
                order_shipped_at=order.shipped_at,
            )
            if not decision.allowed:
                raise HTTPException(
                    status_code=422,
                    detail={"title": "Policy rejected", "reason_codes": decision.reason_codes},
                )

    approval.status = "approved"
    approval.decided_by_user_id = ctx.actor_id
    approval.decision_reason = body.reason
    approval.decided_at = datetime.now(UTC)
    approval.version += 1

    run = await db.get(m.AgentRun, approval.agent_run_id)
    conversation = await db.get(m.Conversation, approval.conversation_id)
    if run and run.organization_id == ctx.organization_id:
        run.status = "running"
        run.state = {**(run.state or {}), "approval_status": "approved"}
        run.version += 1
        db.add(
            m.AgentEvent(
                organization_id=ctx.organization_id,
                agent_run_id=run.id,
                conversation_id=approval.conversation_id,
                sequence=100,
                event_type="approval_approved",
                payload={"approval_id": str(approval.id)},
            )
        )

    # Prefer AgentRunner resume; fall back to direct ERP mutation + verify
    resumed = False
    if run is not None and conversation is not None:
        user_msg = None
        if run.input_message_id:
            user_msg = await db.get(m.Message, run.input_message_id)
        if user_msg is None:
            user_msg = m.Message(
                organization_id=ctx.organization_id,
                conversation_id=conversation.id,
                role="user",
                content="(resume after approval)",
                actor_user_id=ctx.actor_id,
                metadata_={},
            )
            db.add(user_msg)
            await db.flush()
        try:
            await AgentRunner(db, settings).run_turn(
                ctx=ctx,
                conversation=conversation,
                user_message=user_msg,
                run=run,
                proposed_action=approval.payload,
                resume_approval=approval,
            )
            resumed = True
            if conversation.status == "waiting_approval":
                conversation.status = "resolved"
        except Exception:  # noqa: BLE001
            resumed = False

    if not resumed and approval.action_type == "address_change":
        exec_result = await _execute_address_change(
            settings=settings, approval=approval, ctx=ctx
        )
        if run is not None:
            run.status = "completed" if exec_result.get("ok") else "failed"
            run.completed_at = datetime.now(UTC)
            run.state = {**(run.state or {}), "approval_execution": exec_result}
            db.add(
                m.AgentEvent(
                    organization_id=ctx.organization_id,
                    agent_run_id=run.id,
                    conversation_id=approval.conversation_id,
                    sequence=110,
                    event_type="tool_completed" if exec_result.get("ok") else "failed",
                    payload=exec_result,
                )
            )
            if conversation is not None:
                conversation.status = "resolved" if exec_result.get("ok") else "escalated"
            assistant = m.Message(
                organization_id=ctx.organization_id,
                conversation_id=approval.conversation_id,
                role="assistant",
                content=(
                    "Address change completed and verified."
                    if exec_result.get("ok") and (exec_result.get("verification") or {}).get("verified")
                    else (
                        "Address change submitted."
                        if exec_result.get("ok")
                        else "Address change failed after approval; escalating."
                    )
                ),
                agent_run_id=run.id,
                metadata_={"approval_execution": exec_result},
            )
            db.add(assistant)

    await AuditService(db).record(
        organization_id=ctx.organization_id,
        actor_id=ctx.actor_id,
        action="approval.approved",
        resource_type="approval",
        resource_id=str(approval.id),
    )
    await db.commit()
    await db.refresh(approval)
    return ApprovalOut.model_validate(approval)


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject(
    approval_id: UUID,
    body: ApprovalDecision,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> ApprovalOut:
    reject_org_spoof(body.organization_id, ctx)
    ctx.require_permission("approvals:respond")
    approval = await get_tenant_row(db, m.Approval, approval_id, ctx)
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail=f"approval is {approval.status}")
    approval.status = "rejected"
    approval.decided_by_user_id = ctx.actor_id
    approval.decision_reason = body.reason
    approval.decided_at = datetime.now(UTC)
    approval.version += 1
    await AuditService(db).record(
        organization_id=ctx.organization_id,
        actor_id=ctx.actor_id,
        action="approval.rejected",
        resource_type="approval",
        resource_id=str(approval.id),
    )
    await db.commit()
    await db.refresh(approval)
    return ApprovalOut.model_validate(approval)
