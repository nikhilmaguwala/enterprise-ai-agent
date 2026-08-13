"""Deterministic policy rules for address changes and related mutations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from enterprise_domain.address import Address, validate_address
from enterprise_domain.enums import OrderStatus, ShipmentStatus


@dataclass(frozen=True, slots=True)
class AddressChangeDecision:
    allowed: bool
    requires_approval: bool
    reason_codes: list[str]
    validated_address: Address | None = None
    policy_citations: list[str] | None = None


def evaluate_address_change(
    *,
    order_status: str,
    shipment_status: str | None,
    current_address: dict[str, Any],
    proposed_address: dict[str, Any],
    order_shipped_at: datetime | None = None,
    now: datetime | None = None,
) -> AddressChangeDecision:
    """Evaluate whether an address change may proceed.

    Rules (deterministic):
    - Order must not be delivered or cancelled
    - Shipment must not be out_for_delivery or delivered
    - Proposed address must pass validation
    - Proposed address must differ from current
    - Always requires human approval when otherwise allowed
    """
    reasons: list[str] = []
    citations = ["policy:address-change-v1"]

    try:
        status = OrderStatus(order_status)
    except ValueError:
        return AddressChangeDecision(
            allowed=False,
            requires_approval=False,
            reason_codes=["invalid_order_status"],
            policy_citations=citations,
        )

    if status in {OrderStatus.DELIVERED, OrderStatus.CANCELLED}:
        reasons.append("order_not_modifiable")
    if status == OrderStatus.PENDING:
        reasons.append("order_not_yet_confirmed")

    ship: ShipmentStatus | None = None
    if shipment_status:
        try:
            ship = ShipmentStatus(shipment_status)
        except ValueError:
            reasons.append("invalid_shipment_status")
        else:
            if ship in {
                ShipmentStatus.OUT_FOR_DELIVERY,
                ShipmentStatus.DELIVERED,
            }:
                reasons.append("shipment_too_far_along")

    address, addr_errors = validate_address(proposed_address)
    if addr_errors:
        reasons.extend(f"address:{e}" for e in addr_errors)

    current, _ = validate_address(current_address)
    if address and current and address.canonical_dict() == current.canonical_dict():
        reasons.append("address_unchanged")

    # Soft window hint (does not block alone)
    clock = now or datetime.now(UTC)
    if order_shipped_at is not None:
        shipped = order_shipped_at
        if shipped.tzinfo is None:
            shipped = shipped.replace(tzinfo=UTC)
        age_hours = (clock - shipped).total_seconds() / 3600
        if age_hours > 72 and ship == ShipmentStatus.IN_TRANSIT:
            citations.append("policy:address-change-late-window")

    if reasons:
        return AddressChangeDecision(
            allowed=False,
            requires_approval=False,
            reason_codes=reasons,
            validated_address=address,
            policy_citations=citations,
        )

    return AddressChangeDecision(
        allowed=True,
        requires_approval=True,
        reason_codes=["requires_human_approval"],
        validated_address=address,
        policy_citations=citations,
    )
