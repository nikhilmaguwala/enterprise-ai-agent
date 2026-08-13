"""Unit tests for policy engine."""

from __future__ import annotations

from enterprise_domain.policy import evaluate_address_change


CURRENT = {
    "line1": "100 Market Street",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "country": "US",
}

PROPOSED = {
    "line1": "200 Mission St",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94105",
    "country": "US",
}


def test_address_change_requires_approval_when_allowed() -> None:
    decision = evaluate_address_change(
        order_status="delayed",
        shipment_status="delayed",
        current_address=CURRENT,
        proposed_address=PROPOSED,
    )
    assert decision.allowed is True
    assert decision.requires_approval is True


def test_address_change_blocked_when_delivered() -> None:
    decision = evaluate_address_change(
        order_status="delivered",
        shipment_status="delivered",
        current_address=CURRENT,
        proposed_address=PROPOSED,
    )
    assert decision.allowed is False
    assert "order_not_modifiable" in decision.reason_codes


def test_address_change_blocked_when_unchanged() -> None:
    decision = evaluate_address_change(
        order_status="shipped",
        shipment_status="in_transit",
        current_address=CURRENT,
        proposed_address=CURRENT,
    )
    assert decision.allowed is False
    assert "address_unchanged" in decision.reason_codes
