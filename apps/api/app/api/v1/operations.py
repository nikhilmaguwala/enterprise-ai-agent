"""Operations dashboard + job replay aliases for the web UI."""

from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.schemas import JobOut
from app.services.audit import AuditService
from app.services.jobs import JobQueue

router = APIRouter(prefix="/operations", tags=["operations"])


async def _probe(name: str, url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{url.rstrip('/')}/health")
        ok = response.status_code < 500
        return {
            "name": name,
            "status": "healthy" if ok else "degraded",
            "latency_ms": None,
            "detail": f"HTTP {response.status_code}",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "name": name,
            "status": "down",
            "latency_ms": None,
            "detail": str(exc),
        }


@router.get("/dashboard")
async def operations_dashboard(
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    ctx.require_permission("jobs:read")

    status_counts = (
        await db.execute(
            select(m.Job.status, func.count())
            .where(m.Job.organization_id == ctx.organization_id)
            .group_by(m.Job.status)
        )
    ).all()
    counts = {str(status): int(count) for status, count in status_counts}
    pending = counts.get("pending", 0) + counts.get("queued", 0)
    processing = counts.get("running", 0) + counts.get("processing", 0)
    failed = counts.get("failed", 0)

    recent = (
        await db.execute(
            select(m.Job)
            .where(
                m.Job.organization_id == ctx.organization_id,
                m.Job.status.in_(["pending", "queued", "completed", "failed", "succeeded"]),
            )
            .order_by(m.Job.created_at.desc())
            .limit(10)
        )
    ).scalars().all()

    integrations = [
        await _probe("CRM", settings.crm_base_url),
        await _probe("ERP", settings.erp_base_url),
        await _probe("Carrier", settings.carrier_base_url),
        await _probe("Ticketing", settings.ticketing_base_url),
        {
            "name": "Qdrant",
            "status": "unknown",
            "latency_ms": None,
            "detail": settings.qdrant_url,
        },
        {"name": "Postgres", "status": "healthy", "latency_ms": None},
    ]

    return {
        "queues": [
            {
                "name": "jobs",
                "depth": pending,
                "oldest_age_seconds": None,
                "processing": processing,
                "failed": failed,
            },
            {
                "name": "ingestion",
                "depth": pending,
                "oldest_age_seconds": None,
                "processing": processing,
                "failed": failed,
            },
        ],
        "integrations": integrations,
        "recent_replays": [
            {
                "id": str(job.id),
                "job_id": str(job.id),
                "status": (
                    "succeeded"
                    if job.status in {"completed", "succeeded"}
                    else "failed"
                    if job.status == "failed"
                    else "queued"
                ),
                "created_at": job.created_at.isoformat(),
            }
            for job in recent
        ],
    }


@router.post("/jobs/{job_id}/replay", response_model=JobOut)
async def replay_job_alias(
    job_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> JobOut:
    ctx.require_permission("jobs:replay")
    job = await db.get(m.Job, job_id)
    if job is None or job.organization_id != ctx.organization_id:
        raise HTTPException(status_code=404, detail="not found")
    replayed = await JobQueue(db).replay(job_id)
    assert replayed is not None
    await AuditService(db).record(
        organization_id=ctx.organization_id,
        actor_id=ctx.actor_id,
        action="job.replayed",
        resource_type="job",
        resource_id=str(job_id),
    )
    await db.commit()
    await db.refresh(replayed)
    return JobOut.model_validate(replayed)
