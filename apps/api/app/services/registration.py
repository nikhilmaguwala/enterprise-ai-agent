"""Register organizations and users with password auth."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models as m
from app.services.passwords import hash_password


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return (slug or "workspace")[:80]


async def _unique_org_slug(db: AsyncSession, base: str) -> str:
    slug = base
    suffix = 1
    while True:
        exists = (
            await db.execute(select(m.Organization.id).where(m.Organization.slug == slug))
        ).scalar_one_or_none()
        if exists is None:
            return slug
        suffix += 1
        slug = f"{base}-{suffix}"[:80]


async def register_workspace(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    company_name: str,
) -> tuple[m.User, m.Organization, m.Membership, m.Order]:
    normalized_email = email.strip().lower()
    existing = (
        await db.execute(select(m.User.id).where(func.lower(m.User.email) == normalized_email))
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("email_already_registered")

    org = m.Organization(
        id=uuid4(),
        name=company_name.strip() or "My Company",
        slug=await _unique_org_slug(db, _slugify(company_name)),
        status="active",
        settings={},
    )
    user = m.User(
        id=uuid4(),
        email=normalized_email,
        display_name=full_name.strip() or normalized_email.split("@")[0],
        password_hash=hash_password(password),
        status="active",
    )
    membership = m.Membership(
        id=uuid4(),
        organization_id=org.id,
        user_id=user.id,
        role="admin",
        status="active",
    )
    customer = m.Customer(
        id=uuid4(),
        organization_id=org.id,
        user_id=user.id,
        external_id=f"crm-{uuid4().hex[:8]}",
        email=normalized_email,
        full_name=user.display_name,
    )
    order_number = f"ORD-{uuid4().hex[:6].upper()}"
    tracking_number = f"1Z{uuid4().hex[:16].upper()}"
    now = datetime.now(UTC)
    order = m.Order(
        id=uuid4(),
        organization_id=org.id,
        customer_id=customer.id,
        order_number=order_number,
        status="delayed",
        currency="USD",
        total_amount=Decimal("149.99"),
        shipping_address={
            "line1": "100 Market Street",
            "line2": "Suite 4",
            "city": "San Francisco",
            "state": "CA",
            "postal_code": "94105",
            "country": "US",
        },
        tracking_number=tracking_number,
        shipped_at=now - timedelta(days=2),
        expected_delivery_at=now + timedelta(days=3),
    )
    shipment = m.Shipment(
        id=uuid4(),
        organization_id=org.id,
        order_id=order.id,
        carrier="mock-carrier",
        tracking_number=tracking_number,
        status="delayed",
        status_detail="Hub exception — package held for scan",
        delay_reason="Weather-related hub backlog at OAK",
        estimated_delivery_at=now + timedelta(days=4),
        last_event_at=now,
        events=[
            {
                "at": now.isoformat(),
                "location": "OAK",
                "description": "Weather delay at hub",
            }
        ],
    )

    db.add(org)
    db.add(user)
    await db.flush()
    db.add_all([membership, customer, order, shipment])
    await db.flush()
    return user, org, membership, order


async def invite_team_member(
    db: AsyncSession,
    *,
    organization_id: UUID,
    email: str,
    full_name: str,
    role: str,
    temp_password: str,
) -> m.User:
    normalized_email = email.strip().lower()
    existing = (
        await db.execute(select(m.User).where(func.lower(m.User.email) == normalized_email))
    ).scalar_one_or_none()
    if existing is not None:
        membership = (
            await db.execute(
                select(m.Membership).where(
                    m.Membership.user_id == existing.id,
                    m.Membership.organization_id == organization_id,
                )
            )
        ).scalar_one_or_none()
        if membership is not None:
            raise ValueError("user_already_in_org")
        db.add(
            m.Membership(
                id=uuid4(),
                organization_id=organization_id,
                user_id=existing.id,
                role=role,
                status="active",
            )
        )
        await db.flush()
        return existing

    user = m.User(
        id=uuid4(),
        email=normalized_email,
        display_name=full_name.strip() or normalized_email.split("@")[0],
        password_hash=hash_password(temp_password),
        status="active",
    )
    db.add(user)
    db.add(
        m.Membership(
            id=uuid4(),
            organization_id=organization_id,
            user_id=user.id,
            role=role,
            status="active",
        )
    )
    if role == "customer":
        db.add(
            m.Customer(
                id=uuid4(),
                organization_id=organization_id,
                user_id=user.id,
                external_id=f"crm-{uuid4().hex[:8]}",
                email=normalized_email,
                full_name=user.display_name,
            )
        )
    await db.flush()
    return user
