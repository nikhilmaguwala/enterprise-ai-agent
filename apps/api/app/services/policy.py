"""Policy engine facade used by API routes (deterministic)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from enterprise_domain.policy import AddressChangeDecision, evaluate_address_change


class PolicyEngine:
    def evaluate_address_change(
        self,
        *,
        order_status: str,
        shipment_status: str | None,
        current_address: dict[str, Any],
        proposed_address: dict[str, Any],
        order_shipped_at: datetime | None = None,
    ) -> AddressChangeDecision:
        return evaluate_address_change(
            order_status=order_status,
            shipment_status=shipment_status,
            current_address=current_address,
            proposed_address=proposed_address,
            order_shipped_at=order_shipped_at,
        )
