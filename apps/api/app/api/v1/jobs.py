"""Job list/replay and internal HMAC drain."""

from __future__ import annotations

import hashlib
import hmac
import time
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.schemas import JobOut
from app.services.audit import AuditService
from app.services.jobs import JobQueue

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=list[JobOut])
async def list_jobs(
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> list[JobOut]:
    ctx.require_permission("jobs:read")
    stmt = (
        select(m.Job)
        .where(m.Job.organization_id == ctx.organization_id)
        .order_by(m.Job.created_at.desc())
        .limit(100)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [JobOut.model_validate(r) for r in rows]


@router.post("/jobs/{job_id}/replay", response_model=JobOut)
async def replay_job(
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


def _verify_hmac(
    *,
    settings: Settings,
    timestamp: str | None,
    signature: str | None,
    body: bytes = b"",
) -> None:
    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="missing HMAC headers")
    try:
        ts = int(timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid timestamp") from exc
    if abs(int(time.time()) - ts) > 300:
        raise HTTPException(status_code=401, detail="stale timestamp")
    message = f"{timestamp}.".encode() + body
    expected = hmac.new(
        settings.internal_job_hmac_key.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="invalid signature")


@router.post("/internal/jobs/drain")
async def drain_jobs(
    limit: int = Query(default=10, ge=1, le=100),
    x_job_timestamp: str | None = Header(default=None, alias="X-Job-Timestamp"),
    x_job_signature: str | None = Header(default=None, alias="X-Job-Signature"),
    x_job_secret: str | None = Header(default=None, alias="X-Job-Secret"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    # Accept either shared secret (simpler local) or HMAC
    if x_job_secret and hmac.compare_digest(x_job_secret, settings.internal_job_secret):
        pass
    else:
        _verify_hmac(
            settings=settings,
            timestamp=x_job_timestamp,
            signature=x_job_signature,
        )
    result = await JobQueue(db).drain(limit=limit)
    await db.commit()
    return result
