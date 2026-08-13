"""Integration health probes."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter(prefix="/integrations", tags=["integrations"])


async def _probe(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{url.rstrip('/')}/health")
        return {"ok": response.status_code < 500, "status_code": response.status_code}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


@router.get("/health")
async def integrations_health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "crm": await _probe(settings.crm_base_url),
        "erp": await _probe(settings.erp_base_url),
        "carrier": await _probe(settings.carrier_base_url),
        "ticketing": await _probe(settings.ticketing_base_url),
    }
