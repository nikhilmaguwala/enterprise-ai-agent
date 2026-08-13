"""Enterprise integration clients and tool gateway."""

from enterprise_integrations.errors import (
    IntegrationError,
    IntegrationErrorClass,
    classify_http_error,
)
from enterprise_integrations.gateway import ToolGateway
from enterprise_integrations.clients import (
    CarrierClient,
    CRMClient,
    ERPClient,
    TicketingClient,
)

__all__ = [
    "CRMClient",
    "CarrierClient",
    "ERPClient",
    "IntegrationError",
    "IntegrationErrorClass",
    "TicketingClient",
    "ToolGateway",
    "classify_http_error",
]
