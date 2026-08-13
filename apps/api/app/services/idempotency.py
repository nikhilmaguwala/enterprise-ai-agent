"""Idempotency key hashing and record management."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemError
from app.db.models import IdempotencyRecord


def hash_request_payload(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def canonical_hash(payload: Any) -> str:
    """Alias used by AgentRunner for approval payload hashes."""
    return hash_request_payload(payload)


class IdempotencyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def begin(
        self,
        *,
        organization_id: UUID,
        idempotency_key: str,
        scope: str,
        request_payload: Any,
        lock_seconds: int = 30,
    ) -> tuple[IdempotencyRecord, bool]:
        """Return (record, is_new). Raises on conflicting replay."""
        request_hash = hash_request_payload(request_payload)
        stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.organization_id == organization_id,
            IdempotencyRecord.idempotency_key == idempotency_key,
            IdempotencyRecord.scope == scope,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            if existing.request_hash != request_hash:
                raise ProblemError(
                    status=409,
                    title="Idempotency Conflict",
                    detail="Idempotency-Key reused with different payload",
                    type="https://enterprise-ai.local/problems/idempotency-conflict",
                )
            return existing, False

        record = IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            scope=scope,
            request_hash=request_hash,
            locked_until=datetime.now(UTC) + timedelta(seconds=lock_seconds),
        )
        self.session.add(record)
        await self.session.flush()
        return record, True

    async def complete(
        self,
        record: IdempotencyRecord,
        *,
        status_code: int,
        body: dict[str, Any],
    ) -> None:
        record.response_status = status_code
        record.response_body = body
        record.locked_until = None
        await self.session.flush()
