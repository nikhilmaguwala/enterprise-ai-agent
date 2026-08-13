"""Daily quota / usage counters."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.models import UsageCounter


def _day_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    clock = now or datetime.now(UTC)
    start = datetime(clock.year, clock.month, clock.day, tzinfo=UTC)
    return start, start + timedelta(days=1)


class QuotaService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def _bump(
        self,
        *,
        organization_id: UUID | None,
        counter_key: str,
        amount: int = 1,
    ) -> UsageCounter:
        start, end = _day_window()
        stmt = select(UsageCounter).where(
            UsageCounter.organization_id == organization_id,
            UsageCounter.counter_key == counter_key,
            UsageCounter.period_start == start,
        )
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = UsageCounter(
                organization_id=organization_id,
                counter_key=counter_key,
                period_start=start,
                period_end=end,
                count=0,
            )
            self.session.add(row)
            await self.session.flush()
        row.count = int(row.count) + amount
        row.version += 1
        await self.session.flush()
        return row

    async def check_and_increment_messages(
        self,
        *,
        organization_id: UUID,
        authenticated: bool,
    ) -> None:
        key = "messages_authenticated" if authenticated else "messages_anonymous"
        limit = (
            self.settings.max_authenticated_messages_per_day
            if authenticated
            else self.settings.max_anonymous_messages_per_day
        )
        row = await self._bump(organization_id=organization_id, counter_key=key)
        if row.count > limit:
            raise HTTPException(status_code=429, detail="daily message quota exceeded")

    async def check_and_increment_model_calls(
        self,
        *,
        organization_id: UUID | None,
        amount: int = 1,
    ) -> None:
        org_row = await self._bump(
            organization_id=organization_id,
            counter_key="model_calls",
            amount=amount,
        )
        if org_row.count > self.settings.max_model_calls_per_turn * 1000:
            # soft org ceiling; global checked separately
            pass
        global_row = await self._bump(
            organization_id=None,
            counter_key="model_calls_global",
            amount=amount,
        )
        if global_row.count > self.settings.max_global_model_calls_per_day:
            raise HTTPException(status_code=429, detail="global model quota exceeded")
