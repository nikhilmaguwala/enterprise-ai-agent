"""Conversation and message routes."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.schemas import (
    ConversationCreate,
    ConversationListOut,
    ConversationOut,
    MessageCreate,
    MessageListOut,
    MessageOut,
)
from app.services.agent_runner import AgentRunner
from app.services.audit import AuditService
from app.services.idempotency import IdempotencyService
from app.services.quota import QuotaService
from app.services.tenant import get_tenant_row, reject_org_spoof

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _normalize_citations(raw: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return items
    for idx, c in enumerate(raw):
        if not isinstance(c, dict):
            continue
        items.append(
            {
                "id": str(c.get("id") or c.get("chunk_id") or idx),
                "title": str(c.get("title") or c.get("source") or "Policy"),
                "excerpt": str(c.get("excerpt") or c.get("content") or "")[:500],
                "source_uri": c.get("source_uri"),
                "document_id": str(c["document_id"]) if c.get("document_id") else None,
                "score": c.get("score"),
            }
        )
    return items


def _approval_payload(approval: m.Approval) -> dict[str, Any]:
    return {
        "id": str(approval.id),
        "conversation_id": str(approval.conversation_id),
        "action_type": approval.action_type,
        "summary": f"Approve {approval.action_type.replace('_', ' ')}",
        "payload": approval.payload or {},
        "status": approval.status,
        "created_at": approval.created_at.isoformat(),
        "risk_level": "high" if approval.action_type == "address_change" else "medium",
    }


def serialize_message(
    msg: m.Message,
    *,
    approval: m.Approval | None = None,
) -> MessageOut:
    meta = msg.metadata_ or {}
    citations = _normalize_citations(meta.get("citations"))
    approval_out = None
    if approval is not None:
        approval_out = _approval_payload(approval)
    elif meta.get("approval_id") and meta.get("approval"):
        approval_out = meta.get("approval")  # type: ignore[assignment]
    return MessageOut(
        id=msg.id,
        conversation_id=msg.conversation_id,
        role=msg.role,
        content=msg.content,
        created_at=msg.created_at,
        metadata=meta,
        citations=citations or None,
        approval=approval_out,
        run_id=msg.agent_run_id,
    )


@router.post("", response_model=ConversationOut)
async def create_conversation(
    body: ConversationCreate,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> ConversationOut:
    reject_org_spoof(body.organization_id, ctx)
    convo = m.Conversation(
        organization_id=ctx.organization_id,
        created_by_user_id=ctx.actor_id,
        subject=body.subject,
        status="open",
        metadata_=body.metadata,
    )
    db.add(convo)
    await AuditService(db).record(
        organization_id=ctx.organization_id,
        actor_id=ctx.actor_id,
        action="conversation.created",
        resource_type="conversation",
        resource_id=str(convo.id),
    )
    await db.commit()
    await db.refresh(convo)
    return ConversationOut.model_validate(convo)


@router.get("", response_model=ConversationListOut)
async def list_conversations(
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> ConversationListOut:
    stmt = (
        select(m.Conversation)
        .where(m.Conversation.organization_id == ctx.organization_id)
        .order_by(m.Conversation.created_at.desc())
        .limit(100)
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = [ConversationOut.model_validate(r) for r in rows]
    return ConversationListOut(items=items, total=len(items))


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> ConversationOut:
    convo = await get_tenant_row(db, m.Conversation, conversation_id, ctx)
    return ConversationOut.model_validate(convo)


@router.post("/{conversation_id}/messages", response_model=MessageOut)
async def post_message(
    conversation_id: UUID,
    body: MessageCreate,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> MessageOut:
    reject_org_spoof(body.organization_id, ctx)
    convo = await get_tenant_row(db, m.Conversation, conversation_id, ctx)
    await QuotaService(db, settings).check_and_increment_messages(
        organization_id=ctx.organization_id, authenticated=True
    )

    key = idempotency_key or body.idempotency_key
    idem_record = None
    if key:
        idem = IdempotencyService(db)
        record, is_new = await idem.begin(
            organization_id=ctx.organization_id,
            idempotency_key=key,
            scope=f"message:{conversation_id}",
            request_payload={"content": body.content, "proposed_action": body.proposed_action},
        )
        if not is_new and record.response_body:
            return MessageOut.model_validate(record.response_body)
        idem_record = record

    user_msg = m.Message(
        organization_id=ctx.organization_id,
        conversation_id=convo.id,
        role="user",
        content=body.content,
        actor_user_id=ctx.actor_id,
        metadata_={"proposed_action": body.proposed_action} if body.proposed_action else {},
    )
    db.add(user_msg)
    await db.flush()

    run = m.AgentRun(
        organization_id=ctx.organization_id,
        conversation_id=convo.id,
        status="running",
        graph_version=settings.graph_version,
        input_message_id=user_msg.id,
        started_at=datetime.now(UTC),
        state={"user_message": body.content},
    )
    db.add(run)
    await db.flush()

    result = await AgentRunner(db, settings).run_turn(
        ctx=ctx,
        conversation=convo,
        user_message=user_msg,
        run=run,
        order_id=body.order_id,
        proposed_action=body.proposed_action,
    )
    assistant: m.Message = result["assistant"]
    approval: m.Approval | None = result.get("approval")

    await AuditService(db).record(
        organization_id=ctx.organization_id,
        actor_id=ctx.actor_id,
        action="message.created",
        resource_type="message",
        resource_id=str(user_msg.id),
        payload={"conversation_id": str(convo.id), "assistant_id": str(assistant.id)},
    )
    await db.commit()
    await db.refresh(assistant)
    if approval is not None:
        await db.refresh(approval)

    out = serialize_message(assistant, approval=approval)
    if key and idem_record is not None:
        await IdempotencyService(db).complete(
            idem_record, status_code=200, body=out.model_dump(mode="json")
        )
        await db.commit()
    return out


@router.get("/{conversation_id}/messages", response_model=MessageListOut)
async def list_messages(
    conversation_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> MessageListOut:
    await get_tenant_row(db, m.Conversation, conversation_id, ctx)
    stmt = (
        select(m.Message)
        .where(
            m.Message.organization_id == ctx.organization_id,
            m.Message.conversation_id == conversation_id,
        )
        .order_by(m.Message.created_at.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    approvals = (
        await db.execute(
            select(m.Approval).where(
                m.Approval.organization_id == ctx.organization_id,
                m.Approval.conversation_id == conversation_id,
            )
        )
    ).scalars().all()
    by_run = {a.agent_run_id: a for a in approvals if a.status == "pending"}
    # Prefer latest approval per run
    for a in approvals:
        by_run.setdefault(a.agent_run_id, a)

    items = [
        serialize_message(
            r,
            approval=by_run.get(r.agent_run_id) if r.role == "assistant" else None,
        )
        for r in rows
    ]
    return MessageListOut(items=items)
