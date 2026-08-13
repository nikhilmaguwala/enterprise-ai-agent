"""Immutable audit event writer."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditEvent


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        organization_id: UUID,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            payload=payload or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(event)
        await self.session.flush()
        return event
