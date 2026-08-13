"""Mock CRM service."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "data" / "seed"))
sys.path.insert(0, str(ROOT / "packages" / "domain" / "src"))

from ids import customers  # noqa: E402

app = FastAPI(title="Mock CRM", version="0.1.0")
CUSTOMERS = customers()
TOKEN = "mock-service-dev-token"


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mock-crm"}


@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str, _: None = Depends(require_token)) -> dict:
    row = CUSTOMERS.get(customer_id)
    if not row:
        raise HTTPException(status_code=404, detail="customer not found")
    return row


@app.get("/customers")
async def find_customer(
    email: str = Query(...),
    _: None = Depends(require_token),
) -> dict:
    for row in CUSTOMERS.values():
        if row["email"].lower() == email.lower():
            return row
    raise HTTPException(status_code=404, detail="customer not found")
