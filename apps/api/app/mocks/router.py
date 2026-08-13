"""Database-backed mock CRM/ERP/carrier/ticketing for cloud deployments."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db import models as m
from app.db.session import get_db

router = APIRouter(tags=["embedded-mocks"])
IDEMPOTENCY: dict[str, dict[str, Any]] = {}
TICKETS: dict[str, dict[str, Any]] = {}


def _require_token(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    expected = f"Bearer {settings.mock_service_token}"
    if not authorization or authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


class AddressChangeBody(BaseModel):
    address: dict[str, Any] = Field(default_factory=dict)


class TicketCreate(BaseModel):
    organization_id: str | None = None
    subject: str
    body: str
    priority: str = "normal"
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.get("/mocks/crm/health")
@router.get("/mocks/erp/health")
@router.get("/mocks/carrier/health")
@router.get("/mocks/ticketing/health")
async def mock_health(service: str = "embedded") -> dict[str, str]:
    return {"status": "ok", "service": service}


@router.get("/mocks/crm/customers/{customer_id}")
async def crm_get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_token),
) -> dict[str, Any]:
    customer = await db.get(m.Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return {
        "id": str(customer.id),
        "organization_id": str(customer.organization_id),
        "email": customer.email,
        "full_name": customer.full_name,
        "external_id": customer.external_id,
    }


@router.get("/mocks/crm/customers")
async def crm_find_customer(
    email: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_token),
) -> dict[str, Any]:
    customer = (
        await db.execute(
            select(m.Customer).where(func.lower(m.Customer.email) == email.strip().lower())
        )
    ).scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="customer not found")
    return {
        "id": str(customer.id),
        "organization_id": str(customer.organization_id),
        "email": customer.email,
        "full_name": customer.full_name,
        "external_id": customer.external_id,
    }


def _order_payload(order: m.Order) -> dict[str, Any]:
    return {
        "id": str(order.id),
        "organization_id": str(order.organization_id),
        "customer_id": str(order.customer_id),
        "order_number": order.order_number,
        "status": order.status,
        "shipping_address": order.shipping_address or {},
        "tracking_number": order.tracking_number,
        "version": order.version,
        "etag": str(order.version),
    }


@router.get("/mocks/erp/orders/{order_id}")
async def erp_get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_token),
) -> dict[str, Any]:
    order = await db.get(m.Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return _order_payload(order)


@router.get("/mocks/erp/orders")
async def erp_find_order(
    order_number: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_token),
) -> dict[str, Any]:
    order = (
        await db.execute(select(m.Order).where(m.Order.order_number == order_number))
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return _order_payload(order)


@router.post("/mocks/erp/orders/{order_id}/address-change")
async def erp_change_address(
    order_id: str,
    body: AddressChangeBody,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_token),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    if_match: str | None = Header(default=None, alias="If-Match"),
) -> dict[str, Any]:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")
    cache_key = f"{order_id}:{idempotency_key}"
    if cache_key in IDEMPOTENCY:
        return IDEMPOTENCY[cache_key]

    order = await db.get(m.Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    if if_match and if_match != str(order.version):
        raise HTTPException(status_code=412, detail="If-Match conflict")

    order.shipping_address = deepcopy(body.address)
    order.version += 1
    await db.flush()
    result = {
        "ok": True,
        "order_id": order_id,
        "shipping_address": order.shipping_address,
        "version": order.version,
        "etag": str(order.version),
    }
    IDEMPOTENCY[cache_key] = result
    return result


@router.get("/mocks/carrier/tracking/{tracking_number}")
async def carrier_tracking(
    tracking_number: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_token),
) -> dict[str, Any]:
    shipment = (
        await db.execute(
            select(m.Shipment).where(m.Shipment.tracking_number == tracking_number)
        )
    ).scalar_one_or_none()
    if shipment is None:
        raise HTTPException(status_code=404, detail="tracking not found")
    return {
        "tracking_number": shipment.tracking_number,
        "status": shipment.status,
        "status_detail": shipment.status_detail,
        "delay_reason": shipment.delay_reason,
        "carrier": shipment.carrier,
    }


@router.post("/mocks/ticketing/tickets")
async def ticketing_create(body: TicketCreate, _: None = Depends(_require_token)) -> dict[str, Any]:
    ticket_id = str(uuid4())
    ticket = {"id": ticket_id, "status": "open", **body.model_dump()}
    TICKETS[ticket_id] = ticket
    return ticket


@router.post("/mocks/ticketing/handoffs")
async def ticketing_handoff(body: dict[str, Any], _: None = Depends(_require_token)) -> dict[str, Any]:
    handoff_id = str(uuid4())
    handoff = {"id": handoff_id, "status": "queued", **body}
    TICKETS[handoff_id] = handoff
    return handoff
