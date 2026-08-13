"""Postgres durable job queue using FOR UPDATE SKIP LOCKED."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DeadLetterRecord, Job, OutboxEvent


class JobQueue:
    def __init__(self, session: AsyncSession, worker_id: str | None = None) -> None:
        self.session = session
        self.worker_id = worker_id or f"worker-{uuid4().hex[:8]}"

    async def enqueue(
        self,
        *,
        job_type: str,
        payload: dict[str, Any],
        organization_id: UUID | None = None,
        run_after: datetime | None = None,
        max_attempts: int = 5,
    ) -> Job:
        job = Job(
            organization_id=organization_id,
            job_type=job_type,
            status="pending",
            payload=payload,
            max_attempts=max_attempts,
            run_after=run_after or datetime.now(UTC),
        )
        self.session.add(job)
        await self.session.flush()
        self.session.add(
            OutboxEvent(
                organization_id=organization_id,
                aggregate_type="job",
                aggregate_id=job.id,
                event_type="job.enqueued",
                payload={"job_type": job_type, "job_id": str(job.id)},
            )
        )
        await self.session.flush()
        return job

    async def claim(self, *, limit: int = 10) -> list[Job]:
        now = datetime.now(UTC)
        # Dialect-friendly SKIP LOCKED
        result = await self.session.execute(
            text(
                """
                SELECT id FROM jobs
                WHERE status = 'pending' AND run_after <= :now
                ORDER BY run_after ASC
                FOR UPDATE SKIP LOCKED
                LIMIT :limit
                """
            ),
            {"now": now, "limit": limit},
        )
        ids = [row[0] for row in result.fetchall()]
        if not ids:
            return []
        jobs: list[Job] = []
        for job_id in ids:
            job = await self.session.get(Job, job_id)
            if job is None:
                continue
            job.status = "running"
            job.locked_at = now
            job.locked_by = self.worker_id
            job.attempts += 1
            job.version += 1
            jobs.append(job)
        await self.session.flush()
        return jobs

    async def succeed(self, job: Job) -> None:
        job.status = "succeeded"
        job.locked_at = None
        job.locked_by = None
        job.version += 1
        await self.session.flush()

    async def fail(self, job: Job, error: str) -> None:
        job.last_error = error
        if job.attempts >= job.max_attempts:
            job.status = "dead"
            self.session.add(
                DeadLetterRecord(
                    organization_id=job.organization_id,
                    job_id=job.id,
                    job_type=job.job_type,
                    payload=job.payload,
                    error=error,
                    attempts=job.attempts,
                )
            )
        else:
            job.status = "pending"
            job.run_after = datetime.now(UTC) + timedelta(seconds=min(300, 2**job.attempts))
        job.locked_at = None
        job.locked_by = None
        job.version += 1
        await self.session.flush()

    async def replay(self, job_id: UUID) -> Job | None:
        job = await self.session.get(Job, job_id)
        if job is None:
            return None
        job.status = "pending"
        job.run_after = datetime.now(UTC)
        job.locked_at = None
        job.locked_by = None
        job.last_error = None
        job.version += 1
        await self.session.flush()
        return job

    async def drain(self, *, limit: int = 10) -> dict[str, Any]:
        claimed = await self.claim(limit=limit)
        results: list[dict[str, Any]] = []
        for job in claimed:
            try:
                # Stub handlers — real processors register by job_type later
                await self.succeed(job)
                results.append({"job_id": str(job.id), "status": "succeeded"})
            except Exception as exc:  # noqa: BLE001
                await self.fail(job, str(exc))
                results.append({"job_id": str(job.id), "status": "failed", "error": str(exc)})
        return {"processed": len(results), "results": results}
