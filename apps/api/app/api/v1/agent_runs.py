"""Agent run inspection routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.schemas import AgentRunOut
from app.services.tenant import get_tenant_row

router = APIRouter(prefix="/agent-runs", tags=["agent_runs"])


@router.get("", response_model=list[AgentRunOut])
async def list_runs(
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> list[AgentRunOut]:
    ctx.require_permission("agent_runs:read")
    stmt = (
        select(m.AgentRun)
        .where(m.AgentRun.organization_id == ctx.organization_id)
        .order_by(m.AgentRun.created_at.desc())
        .limit(100)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [AgentRunOut.model_validate(r) for r in rows]


@router.get("/{run_id}", response_model=AgentRunOut)
async def get_run(
    run_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> AgentRunOut:
    ctx.require_permission("agent_runs:read")
    run = await get_tenant_row(db, m.AgentRun, run_id, ctx)
    return AgentRunOut.model_validate(run)


@router.get("/{run_id}/events")
async def get_run_events(
    run_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    ctx.require_permission("agent_runs:read")
    await get_tenant_row(db, m.AgentRun, run_id, ctx)
    stmt = (
        select(m.AgentEvent)
        .where(
            m.AgentEvent.organization_id == ctx.organization_id,
            m.AgentEvent.agent_run_id == run_id,
        )
        .order_by(m.AgentEvent.sequence.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": str(r.id),
            "sequence": r.sequence,
            "event_type": r.event_type,
            "payload": r.payload,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
