"""Mock carrier tracking service with failure simulation."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "data" / "seed"))
sys.path.insert(0, str(ROOT / "packages" / "domain" / "src"))

from ids import tracking  # noqa: E402

app = FastAPI(title="Mock Carrier", version="0.1.0")
TRACKING = tracking()
TOKEN = "mock-service-dev-token"


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mock-carrier"}


@app.get("/tracking/{tracking_number}")
async def get_tracking(
    tracking_number: str,
    fail: str | None = Query(default=None, description="timeout|500|404"),
    _: None = Depends(require_token),
) -> dict:
    if fail == "timeout":
        raise HTTPException(status_code=504, detail="simulated timeout")
    if fail == "500":
        raise HTTPException(status_code=500, detail="simulated carrier failure")
    if fail == "404":
        raise HTTPException(status_code=404, detail="tracking not found")
    row = TRACKING.get(tracking_number)
    if not row:
        raise HTTPException(status_code=404, detail="tracking not found")
    return row
