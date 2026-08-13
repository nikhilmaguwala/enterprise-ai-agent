"""Seed Acme Retail + Globex Shop demo data."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.db import models as m
from app.db.session import SessionLocal
from enterprise_domain.seed_ids import SeedIds
from enterprise_knowledge.chunking import chunk_text


POLICY_TEXT = """# Shipping Delay Policy

Orders may be delayed due to carrier hub exceptions, weather, or capacity constraints.
Customers receive updated ETAs when carrier status is delayed.

# Address Change Policy

Address changes require human approval.
Address changes are blocked when shipment status is out_for_delivery or delivered.
Proposed addresses must be valid US addresses and differ from the current address.
Mutations use idempotency keys and are verified with a follow-up read.
"""


ADDRESS_ACME = {
    "line1": "100 Market Street",
    "line2": "Suite 4",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "country": "US",
}

ADDRESS_GLOBEX = {
    "line1": "500 Innovation Way",
    "city": "Austin",
    "state": "TX",
    "postal_code": "78701",
    "country": "US",
}


async def seed() -> None:
    settings = get_settings()
    storage = Path(settings.object_storage_path)
    storage.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)

    async with SessionLocal() as db:
        existing = await db.get(m.Organization, SeedIds.ORG_ACME)
        if existing:
            print("Seed already present — skipping")
            return

        orgs = [
            m.Organization(
                id=SeedIds.ORG_ACME,
                name="Acme Retail",
                slug="acme-retail",
                status="active",
                settings={},
            ),
            m.Organization(
                id=SeedIds.ORG_GLOBEX,
                name="Globex Shop",
                slug="globex-shop",
                status="active",
                settings={},
            ),
        ]
        db.add_all(orgs)
        await db.flush()

        users = [
            m.User(
                id=SeedIds.USER_CUSTOMER_ACME,
                email="customer@acme-demo.test",
                display_name="Acme Customer",
            ),
            m.User(
                id=SeedIds.USER_AGENT_ACME,
                email="agent@acme-demo.test",
                display_name="Acme Agent",
            ),
            m.User(
                id=SeedIds.USER_SUPERVISOR_ACME,
                email="supervisor@acme-demo.test",
                display_name="Acme Supervisor",
            ),
            m.User(
                id=SeedIds.USER_ADMIN_ACME,
                email="admin@acme-demo.test",
                display_name="Acme Admin",
            ),
            m.User(
                id=SeedIds.USER_CUSTOMER_GLOBEX,
                email="customer@globex-demo.test",
                display_name="Globex Customer",
            ),
        ]
        db.add_all(users)
        await db.flush()

        memberships = [
            m.Membership(
                organization_id=SeedIds.ORG_ACME,
                user_id=SeedIds.USER_CUSTOMER_ACME,
                role="customer",
            ),
            m.Membership(
                organization_id=SeedIds.ORG_ACME,
                user_id=SeedIds.USER_AGENT_ACME,
                role="support_agent",
            ),
            m.Membership(
                organization_id=SeedIds.ORG_ACME,
                user_id=SeedIds.USER_SUPERVISOR_ACME,
                role="supervisor",
            ),
            m.Membership(
                organization_id=SeedIds.ORG_ACME,
                user_id=SeedIds.USER_ADMIN_ACME,
                role="admin",
            ),
            m.Membership(
                organization_id=SeedIds.ORG_GLOBEX,
                user_id=SeedIds.USER_CUSTOMER_GLOBEX,
                role="customer",
            ),
        ]
        db.add_all(memberships)
        await db.flush()

        customers = [
            m.Customer(
                id=SeedIds.CUSTOMER_ACME,
                organization_id=SeedIds.ORG_ACME,
                user_id=SeedIds.USER_CUSTOMER_ACME,
                external_id="crm-acme-1",
                email="customer@acme-demo.test",
                full_name="Acme Customer",
                metadata_={},
            ),
            m.Customer(
                id=SeedIds.CUSTOMER_GLOBEX,
                organization_id=SeedIds.ORG_GLOBEX,
                user_id=SeedIds.USER_CUSTOMER_GLOBEX,
                external_id="crm-globex-1",
                email="customer@globex-demo.test",
                full_name="Globex Customer",
                metadata_={},
            ),
        ]
        db.add_all(customers)
        await db.flush()

        orders = [
            m.Order(
                id=SeedIds.ORDER_ACME_DELAYED,
                organization_id=SeedIds.ORG_ACME,
                customer_id=SeedIds.CUSTOMER_ACME,
                order_number=SeedIds.ORDER_NUMBER_ACME_DELAYED,
                status="delayed",
                currency="USD",
                total_amount=Decimal("129.99"),
                shipping_address=ADDRESS_ACME,
                shipped_at=now - timedelta(days=3),
                expected_delivery_at=now + timedelta(days=2),
                tracking_number=SeedIds.TRACKING_ACME_DELAYED,
                metadata_={"scenario": "delayed_shipped"},
                version=1,
            ),
            m.Order(
                id=SeedIds.ORDER_ACME_OK,
                organization_id=SeedIds.ORG_ACME,
                customer_id=SeedIds.CUSTOMER_ACME,
                order_number=SeedIds.ORDER_NUMBER_ACME_OK,
                status="shipped",
                currency="USD",
                total_amount=Decimal("49.00"),
                shipping_address=ADDRESS_ACME,
                shipped_at=now - timedelta(days=1),
                expected_delivery_at=now + timedelta(days=1),
                tracking_number=SeedIds.TRACKING_ACME_OK,
                metadata_={},
                version=1,
            ),
            m.Order(
                id=SeedIds.ORDER_GLOBEX,
                organization_id=SeedIds.ORG_GLOBEX,
                customer_id=SeedIds.CUSTOMER_GLOBEX,
                order_number=SeedIds.ORDER_NUMBER_GLOBEX,
                status="shipped",
                currency="USD",
                total_amount=Decimal("89.50"),
                shipping_address=ADDRESS_GLOBEX,
                shipped_at=now - timedelta(days=1),
                expected_delivery_at=now + timedelta(days=2),
                tracking_number=SeedIds.TRACKING_GLOBEX,
                metadata_={},
                version=1,
            ),
        ]
        db.add_all(orders)
        await db.flush()

        shipments = [
            m.Shipment(
                id=SeedIds.SHIPMENT_ACME_DELAYED,
                organization_id=SeedIds.ORG_ACME,
                order_id=SeedIds.ORDER_ACME_DELAYED,
                carrier="mock-carrier",
                tracking_number=SeedIds.TRACKING_ACME_DELAYED,
                status="delayed",
                status_detail="Hub exception — package held for scan",
                delay_reason="Weather-related hub backlog at OAK",
                estimated_delivery_at=now + timedelta(days=2),
                last_event_at=now - timedelta(hours=6),
                events=[
                    {"code": "IN_TRANSIT", "at": (now - timedelta(days=2)).isoformat()},
                    {"code": "DELAYED", "at": (now - timedelta(hours=6)).isoformat()},
                ],
            ),
            m.Shipment(
                id=SeedIds.SHIPMENT_ACME_OK,
                organization_id=SeedIds.ORG_ACME,
                order_id=SeedIds.ORDER_ACME_OK,
                carrier="mock-carrier",
                tracking_number=SeedIds.TRACKING_ACME_OK,
                status="in_transit",
                status_detail="On time",
                estimated_delivery_at=now + timedelta(days=1),
                last_event_at=now - timedelta(hours=2),
                events=[],
            ),
            m.Shipment(
                id=SeedIds.SHIPMENT_GLOBEX,
                organization_id=SeedIds.ORG_GLOBEX,
                order_id=SeedIds.ORDER_GLOBEX,
                carrier="mock-carrier",
                tracking_number=SeedIds.TRACKING_GLOBEX,
                status="in_transit",
                status_detail="On time",
                estimated_delivery_at=now + timedelta(days=2),
                last_event_at=now - timedelta(hours=3),
                events=[],
            ),
        ]
        db.add_all(shipments)

        # Policy documents per org
        for org_id, title in [
            (SeedIds.ORG_ACME, "Acme Shipping & Address Policy"),
            (SeedIds.ORG_GLOBEX, "Globex Shipping & Address Policy"),
        ]:
            doc = m.Document(
                organization_id=org_id,
                title=title,
                status="active",
                mime_type="text/plain",
                storage_key=f"{org_id}/policies/shipping.txt",
                checksum_sha256=hashlib.sha256(POLICY_TEXT.encode()).hexdigest(),
                byte_size=len(POLICY_TEXT.encode()),
                uploaded_by_user_id=(
                    SeedIds.USER_ADMIN_ACME
                    if org_id == SeedIds.ORG_ACME
                    else SeedIds.USER_CUSTOMER_GLOBEX
                ),
                activated_at=now,
                metadata_={"seed": True},
            )
            db.add(doc)
            await db.flush()
            path = storage / doc.storage_key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(POLICY_TEXT)
            for chunk in chunk_text(POLICY_TEXT):
                db.add(
                    m.DocumentChunk(
                        organization_id=org_id,
                        document_id=doc.id,
                        chunk_index=chunk.index,
                        content=chunk.content,
                        content_hash=chunk.content_hash,
                        section_title=chunk.section_title,
                        token_estimate=chunk.token_estimate,
                        metadata_={},
                    )
                )

        db.add(
            m.EvaluationCase(
                organization_id=SeedIds.ORG_ACME,
                name="delayed_order_explanation",
                dataset="critical_path",
                input={
                    "message": f"Why is order {SeedIds.ORDER_NUMBER_ACME_DELAYED} delayed?",
                    "order_id": str(SeedIds.ORDER_ACME_DELAYED),
                },
                expected={"intent": "delay_explanation", "requires_citation": True},
                tags=["delay", "rag"],
            )
        )
        db.add(
            m.EvaluationCase(
                organization_id=SeedIds.ORG_ACME,
                name="address_change_requires_approval",
                dataset="critical_path",
                input={
                    "message": "Please change my shipping address",
                    "order_id": str(SeedIds.ORDER_ACME_DELAYED),
                    "proposed_action": {
                        "type": "address_change",
                        "order_id": str(SeedIds.ORDER_ACME_DELAYED),
                        "address": {
                            "line1": "200 Mission St",
                            "city": "San Francisco",
                            "state": "CA",
                            "postal_code": "94105",
                            "country": "US",
                        },
                    },
                },
                expected={"requires_approval": True},
                tags=["approval", "mutation"],
            )
        )

        db.add(
            m.PromptVersion(
                organization_id=None,
                name="support_system",
                version="v1",
                content="You are an enterprise support agent. Never invent policy.",
                is_active=True,
                metadata_={},
            )
        )

        await db.commit()
        print("Seed complete: Acme Retail + Globex Shop")


if __name__ == "__main__":
    asyncio.run(seed())
