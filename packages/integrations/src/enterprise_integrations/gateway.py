"""Tool gateway that wraps clients with classification and timing."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any, Awaitable, Callable

from enterprise_integrations.clients import (
    CarrierClient,
    CRMClient,
    ERPClient,
    TicketingClient,
)
from enterprise_integrations.errors import IntegrationError, IntegrationErrorClass


ToolFn = Callable[..., Awaitable[dict[str, Any]]]


@dataclass
class ToolResult:
    ok: bool
    tool_name: str
    data: dict[str, Any] = field(default_factory=dict)
    error: IntegrationError | None = None
    latency_ms: float = 0.0


class ToolGateway:
    def __init__(
        self,
        *,
        crm: CRMClient,
        erp: ERPClient,
        carrier: CarrierClient,
        ticketing: TicketingClient,
    ) -> None:
        self.crm = crm
        self.erp = erp
        self.carrier = carrier
        self.ticketing = ticketing

    @classmethod
    def from_settings(cls, settings: Any) -> ToolGateway:
        token = str(getattr(settings, "mock_service_token", "") or "")
        urls = settings.service_base_urls() if hasattr(settings, "service_base_urls") else {
            "crm": str(getattr(settings, "crm_base_url", "http://localhost:8101")),
            "erp": str(getattr(settings, "erp_base_url", "http://localhost:8102")),
            "carrier": str(getattr(settings, "carrier_base_url", "http://localhost:8103")),
            "ticketing": str(getattr(settings, "ticketing_base_url", "http://localhost:8104")),
        }
        return cls(
            crm=CRMClient(urls["crm"], token),
            erp=ERPClient(urls["erp"], token),
            carrier=CarrierClient(urls["carrier"], token),
            ticketing=TicketingClient(urls["ticketing"], token),
        )

    async def call(self, tool_name: str, **kwargs: Any) -> ToolResult:
        mapping: dict[str, ToolFn] = {
            "crm.get_customer": self.crm.get_customer,
            "crm.find_customer_by_email": self.crm.find_customer_by_email,
            "erp.get_order": self.erp.get_order,
            "erp.get_order_by_number": self.erp.get_order_by_number,
            "erp.change_address": self.erp.change_address,
            "carrier.get_tracking": self.carrier.get_tracking,
            "ticketing.create_ticket": self.ticketing.create_ticket,
            "ticketing.get_ticket": self.ticketing.get_ticket,
            "ticketing.create_handoff": self.ticketing.create_handoff,
        }
        fn = mapping.get(tool_name)
        if fn is None:
            return ToolResult(
                ok=False,
                tool_name=tool_name,
                error=IntegrationError(
                    message=f"unknown tool: {tool_name}",
                    error_class=IntegrationErrorClass.CLIENT,
                ),
            )
        started = perf_counter()
        try:
            data = await fn(**kwargs)
            return ToolResult(
                ok=True,
                tool_name=tool_name,
                data=data,
                latency_ms=(perf_counter() - started) * 1000,
            )
        except IntegrationError as exc:
            return ToolResult(
                ok=False,
                tool_name=tool_name,
                error=exc,
                latency_ms=(perf_counter() - started) * 1000,
            )
