"""Audit event listing."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.schemas import AuditEventOut

router = APIRouter(prefix="/audit-events", tags=["audit"])


@router.get("", response_model=list[AuditEventOut])
async def list_audit_events(
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> list[AuditEventOut]:
    ctx.require_permission("audit:read")
    stmt = (
        select(m.AuditEvent)
        .where(m.AuditEvent.organization_id == ctx.organization_id)
        .order_by(m.AuditEvent.created_at.desc())
        .limit(200)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [AuditEventOut.model_validate(r) for r in rows]
