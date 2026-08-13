"""Inbox compatibility routes for the web UI."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db

router = APIRouter(prefix="/inbox", tags=["inbox"])


@router.get("/escalations")
async def list_escalations(
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = (
        select(m.Conversation)
        .where(
            m.Conversation.organization_id == ctx.organization_id,
            m.Conversation.status == "escalated",
        )
        .order_by(m.Conversation.updated_at.desc())
        .limit(100)
    )
    rows = (await db.execute(stmt)).scalars().all()
    items = []
    for convo in rows:
        meta = convo.metadata_ or {}
        items.append(
            {
                "id": str(convo.id),
                "conversation_id": str(convo.id),
                "reason": str(meta.get("escalation_reason") or "Agent escalation"),
                "handoff_summary": str(
                    meta.get("handoff_summary")
                    or convo.subject
                    or "Conversation escalated to a human agent"
                ),
                "status": "open",
                "priority": meta.get("priority") or "medium",
                "created_at": convo.created_at.isoformat(),
                "customer_email": meta.get("customer_email"),
                "assigned_to": meta.get("assigned_to"),
            }
        )
    return {"items": items}
