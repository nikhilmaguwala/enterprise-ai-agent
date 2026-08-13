"""Idempotency hashing tests."""

from __future__ import annotations

from app.services.idempotency import hash_request_payload


def test_hash_is_deterministic_and_key_order_independent() -> None:
    a = hash_request_payload({"b": 2, "a": 1})
    b = hash_request_payload({"a": 1, "b": 2})
    assert a == b


def test_hash_changes_when_payload_changes() -> None:
    a = hash_request_payload({"x": 1})
    b = hash_request_payload({"x": 2})
    assert a != b
