"""Mock ERP service with idempotent address change."""

from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "data" / "seed"))
sys.path.insert(0, str(ROOT / "packages" / "domain" / "src"))

from ids import orders  # noqa: E402

app = FastAPI(title="Mock ERP", version="0.1.0")
ORDERS: dict[str, dict[str, Any]] = orders()
IDEMPOTENCY: dict[str, dict[str, Any]] = {}
TOKEN = "mock-service-dev-token"


class AddressChangeBody(BaseModel):
    address: dict[str, Any] = Field(default_factory=dict)


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mock-erp"}


@app.get("/orders/{order_id}")
async def get_order(order_id: str, _: None = Depends(require_token)) -> dict:
    row = ORDERS.get(order_id)
    if not row:
        raise HTTPException(status_code=404, detail="order not found")
    return row


@app.get("/orders")
async def find_order(
    order_number: str = Query(...),
    _: None = Depends(require_token),
) -> dict:
    for row in ORDERS.values():
        if row["order_number"] == order_number:
            return row
    raise HTTPException(status_code=404, detail="order not found")


@app.post("/orders/{order_id}/address-change")
async def change_address(
    order_id: str,
    body: AddressChangeBody,
    request: Request,
    _: None = Depends(require_token),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    if_match: str | None = Header(default=None, alias="If-Match"),
) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")

    cache_key = f"{order_id}:{idempotency_key}"
    if cache_key in IDEMPOTENCY:
        return IDEMPOTENCY[cache_key]

    if if_match and if_match != str(order.get("etag") or order.get("version")):
        raise HTTPException(status_code=412, detail="If-Match conflict")

    order["shipping_address"] = deepcopy(body.address)
    order["version"] = int(order.get("version") or 1) + 1
    order["etag"] = str(order["version"])
    result = {
        "ok": True,
        "order_id": order_id,
        "shipping_address": order["shipping_address"],
        "version": order["version"],
        "etag": order["etag"],
    }
    IDEMPOTENCY[cache_key] = result
    return result
