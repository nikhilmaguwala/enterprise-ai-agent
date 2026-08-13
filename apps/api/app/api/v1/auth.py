"""Dev auth helper routes (disabled when DEV_AUTH_ENABLED=false)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import mint_dev_token
from app.db import models as m
from app.db.session import get_db
from app.schemas import DevLoginRequest, DevTokenRequest

router = APIRouter(prefix="/auth", tags=["auth"])

_ROLE_TO_FRONTEND = {
    "support_agent": "agent",
    "customer": "customer",
    "supervisor": "supervisor",
    "admin": "admin",
}


@router.post("/dev-token")
async def create_dev_token(
    body: DevTokenRequest,
    settings: Settings = Depends(get_settings),
) -> dict:
    if not settings.dev_auth_enabled:
        raise HTTPException(status_code=404, detail="not found")
    token = mint_dev_token(
        organization_id=body.organization_id,
        actor_id=body.actor_id,
        roles=body.roles,
        email=body.email,
        settings=settings,
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/dev-login")
async def dev_login(
    body: DevLoginRequest,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not settings.dev_auth_enabled:
        raise HTTPException(status_code=404, detail="not found")

    email = body.email.strip().lower()
    user = (
        await db.execute(select(m.User).where(func.lower(m.User.email) == email))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    membership = (
        await db.execute(
            select(m.Membership)
            .where(
                m.Membership.user_id == user.id,
                m.Membership.status == "active",
            )
            .limit(1)
        )
    ).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=403, detail="no active membership")

    org = await db.get(m.Organization, membership.organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")

    db_role = membership.role
    frontend_role = _ROLE_TO_FRONTEND.get(db_role, db_role)
    token = mint_dev_token(
        organization_id=org.id,
        actor_id=user.id,
        roles=[db_role],
        email=user.email,
        settings=settings,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.display_name,
            "role": frontend_role,
            "organization_id": str(org.id),
            "organization_name": org.name,
        },
    }
