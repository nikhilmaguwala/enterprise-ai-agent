"""Authentication: dev login, registration, login, invites."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import ExecutionContext, get_execution_context, mint_access_token, mint_dev_token
from app.db import models as m
from app.db.session import get_db
from app.schemas import DevLoginRequest, DevTokenRequest, InviteRequest, LoginRequest, RegisterRequest
from app.services.email import EmailRecipient, get_email_service
from app.services.passwords import verify_password
from app.services.registration import invite_team_member, register_workspace

router = APIRouter(prefix="/auth", tags=["auth"])

_ROLE_TO_FRONTEND = {
    "support_agent": "agent",
    "customer": "customer",
    "supervisor": "supervisor",
    "admin": "admin",
}


def _auth_response(
    *,
    user: m.User,
    org: m.Organization,
    membership: m.Membership,
    settings: Settings,
    starter_order_number: str | None = None,
) -> dict:
    db_role = membership.role
    frontend_role = _ROLE_TO_FRONTEND.get(db_role, db_role)
    token = mint_access_token(
        organization_id=org.id,
        actor_id=user.id,
        roles=[db_role],
        email=user.email,
        settings=settings,
    )
    payload = {
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
    if starter_order_number:
        payload["starter_order_number"] = starter_order_number
    return payload


@router.post("/register")
async def register(
    body: RegisterRequest,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not settings.registration_enabled:
        raise HTTPException(status_code=404, detail="registration disabled")
    try:
        user, org, membership, order = await register_workspace(
            db,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            company_name=body.company_name,
        )
        await db.commit()
    except ValueError as exc:
        await db.rollback()
        if str(exc) == "email_already_registered":
            raise HTTPException(status_code=409, detail="email already registered") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _auth_response(
        user=user,
        org=org,
        membership=membership,
        settings=settings,
        starter_order_number=order.order_number,
    )


@router.post("/login")
async def login(
    body: LoginRequest,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not settings.registration_enabled:
        raise HTTPException(status_code=404, detail="login disabled")

    email = body.email.strip().lower()
    user = (
        await db.execute(select(m.User).where(func.lower(m.User.email) == email))
    ).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid email or password")

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

    return _auth_response(user=user, org=org, membership=membership, settings=settings)


@router.post("/invite")
async def invite_user(
    body: InviteRequest,
    ctx: ExecutionContext = Depends(get_execution_context),
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> dict:
    ctx.require_permission("admin:all")
    if not settings.registration_enabled:
        raise HTTPException(status_code=404, detail="invites disabled")

    allowed_roles = {"customer", "support_agent", "supervisor", "admin"}
    role = body.role.strip()
    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail="invalid role")

    temp_password = secrets.token_urlsafe(10)
    try:
        user = await invite_team_member(
            db,
            organization_id=ctx.organization_id,
            email=body.email,
            full_name=body.full_name,
            role=role,
            temp_password=temp_password,
        )
        org = await db.get(m.Organization, ctx.organization_id)
        await db.commit()
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if org is None:
        raise HTTPException(status_code=404, detail="organization not found")

    login_url = f"{settings.app_url.rstrip('/')}/login"
    await get_email_service(settings).send(
        to=[EmailRecipient(email=user.email, name=user.display_name)],
        subject=f"[ResolveAI] You're invited to {org.name}",
        html_content=(
            f"<p>You were invited to <strong>{org.name}</strong> on ResolveAI.</p>"
            f"<p>Email: {user.email}<br/>Temporary password: <code>{temp_password}</code></p>"
            f'<p><a href="{login_url}">Sign in here</a> and change your password later.</p>'
        ),
        text_content=(
            f"Invited to {org.name}. Email: {user.email} Temp password: {temp_password} "
            f"Login: {login_url}"
        ),
    )

    return {
        "ok": True,
        "email": user.email,
        "role": _ROLE_TO_FRONTEND.get(role, role),
        "temporary_password_sent": True,
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

    return _auth_response(user=user, org=org, membership=membership, settings=settings)
