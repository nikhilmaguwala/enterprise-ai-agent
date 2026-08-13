"""SSE event stream for conversations."""

from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.services.tenant import get_tenant_row

router = APIRouter(tags=["events"])


@router.get("/conversations/{conversation_id}/events")
async def conversation_events(
    conversation_id: UUID,
    request: Request,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    await get_tenant_row(db, m.Conversation, conversation_id, ctx)

    async def generator():
        last_seq_by_run: dict[str, int] = {}
        # Initial snapshot
        stmt = (
            select(m.AgentEvent)
            .where(
                m.AgentEvent.organization_id == ctx.organization_id,
                m.AgentEvent.conversation_id == conversation_id,
            )
            .order_by(m.AgentEvent.sequence.asc())
            .limit(200)
        )
        rows = (await db.execute(stmt)).scalars().all()
        for row in rows:
            last_seq_by_run[str(row.agent_run_id)] = max(
                last_seq_by_run.get(str(row.agent_run_id), 0), row.sequence
            )
            yield {
                "event": row.event_type,
                "data": json.dumps(
                    {
                        "id": str(row.id),
                        "agent_run_id": str(row.agent_run_id),
                        "sequence": row.sequence,
                        "payload": row.payload,
                    }
                ),
            }

        # Poll for new events (demo-friendly; replace with LISTEN/NOTIFY later)
        while True:
            if await request.is_disconnected():
                break
            await asyncio.sleep(1.0)
            stmt = (
                select(m.AgentEvent)
                .where(
                    m.AgentEvent.organization_id == ctx.organization_id,
                    m.AgentEvent.conversation_id == conversation_id,
                )
                .order_by(m.AgentEvent.created_at.asc())
                .limit(50)
            )
            fresh = (await db.execute(stmt)).scalars().all()
            for row in fresh:
                prev = last_seq_by_run.get(str(row.agent_run_id), 0)
                if row.sequence <= prev:
                    continue
                last_seq_by_run[str(row.agent_run_id)] = row.sequence
                yield {
                    "event": row.event_type,
                    "data": json.dumps(
                        {
                            "id": str(row.id),
                            "agent_run_id": str(row.agent_run_id),
                            "sequence": row.sequence,
                            "payload": row.payload,
                        }
                    ),
                }

    return EventSourceResponse(generator())
