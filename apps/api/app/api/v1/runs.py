"""Thin /runs alias for agent-runs (web UI contract)."""

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

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}", response_model=AgentRunOut)
async def get_run_alias(
    run_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> AgentRunOut:
    ctx.require_permission("agent_runs:read")
    run = await get_tenant_row(db, m.AgentRun, run_id, ctx)
    out = AgentRunOut.model_validate(run)
    events = (
        await db.execute(
            select(m.AgentEvent)
            .where(
                m.AgentEvent.organization_id == ctx.organization_id,
                m.AgentEvent.agent_run_id == run_id,
            )
            .order_by(m.AgentEvent.sequence.asc())
        )
    ).scalars().all()
    steps = []
    for ev in events:
        status = "succeeded"
        if "fail" in ev.event_type:
            status = "failed"
        elif ev.event_type in {"approval_required", "running", "tool_executing"}:
            status = "running"
        steps.append(
            {
                "id": str(ev.id),
                "name": ev.event_type,
                "status": status,
                "started_at": ev.created_at.isoformat(),
                "finished_at": ev.created_at.isoformat(),
                "detail": None,
                "output": ev.payload,
            }
        )
    out.steps = steps
    return out
