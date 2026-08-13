"""Typed HTTP clients for mock enterprise systems."""

from __future__ import annotations

from typing import Any

import httpx

from enterprise_integrations.errors import IntegrationError, classify_http_error


class _BaseClient:
    def __init__(self, base_url: str, token: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers=self._headers(headers),
            )
        if response.status_code >= 400:
            raise classify_http_error(response.status_code, response.text)
        if response.status_code == 204 or not response.content:
            return {}
        data = response.json()
        if not isinstance(data, dict):
            raise IntegrationError(
                message="expected JSON object",
                error_class=classify_http_error(500).error_class,
                status_code=500,
            )
        return data


class CRMClient(_BaseClient):
    async def get_customer(self, customer_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/customers/{customer_id}")

    async def find_customer_by_email(self, email: str) -> dict[str, Any]:
        return await self._request("GET", "/customers", params={"email": email})


class ERPClient(_BaseClient):
    async def get_order(self, order_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/orders/{order_id}")

    async def get_order_by_number(self, order_number: str) -> dict[str, Any]:
        return await self._request(
            "GET", "/orders", params={"order_number": order_number}
        )

    async def change_address(
        self,
        order_id: str,
        address: dict[str, Any],
        *,
        idempotency_key: str,
        if_match: str | None = None,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {"Idempotency-Key": idempotency_key}
        if if_match:
            headers["If-Match"] = if_match
        return await self._request(
            "POST",
            f"/orders/{order_id}/address-change",
            json={"address": address},
            headers=headers,
        )


class CarrierClient(_BaseClient):
    async def get_tracking(
        self,
        tracking_number: str,
        *,
        fail: str | None = None,
    ) -> dict[str, Any]:
        params = {"fail": fail} if fail else None
        return await self._request(
            "GET",
            f"/tracking/{tracking_number}",
            params=params,
        )


class TicketingClient(_BaseClient):
    async def create_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/tickets", json=payload)

    async def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/tickets/{ticket_id}")

    async def create_handoff(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/handoffs", json=payload)
