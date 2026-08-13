"""Tenant-aware query helpers."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ExecutionContext
from app.db import models as m


def apply_tenant_filter(stmt: Select, model: type, organization_id: UUID) -> Select:
    if not hasattr(model, "organization_id"):
        raise ValueError(f"{model.__name__} is not tenant-scoped")
    return stmt.where(model.organization_id == organization_id)


async def get_tenant_row(
    session: AsyncSession,
    model: type,
    row_id: UUID,
    ctx: ExecutionContext,
    *,
    not_found_detail: str = "not found",
):
    stmt = select(model).where(model.id == row_id)
    stmt = apply_tenant_filter(stmt, model, ctx.organization_id)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=not_found_detail)
    return row


def reject_org_spoof(body_org_id: UUID | str | None, ctx: ExecutionContext) -> None:
    """Reject requests that attempt to spoof organization_id in the body."""
    if body_org_id is None:
        return
    if UUID(str(body_org_id)) != ctx.organization_id:
        raise HTTPException(
            status_code=403,
            detail="organization_id in body does not match token tenant",
        )
