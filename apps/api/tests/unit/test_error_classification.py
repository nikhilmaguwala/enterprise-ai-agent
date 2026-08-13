"""Integration error classification tests."""

from __future__ import annotations

from enterprise_integrations.errors import IntegrationErrorClass, classify_http_error


def test_classify_transient() -> None:
    err = classify_http_error(503, "unavailable")
    assert err.error_class == IntegrationErrorClass.TRANSIENT
    assert err.retryable is True


def test_classify_conflict() -> None:
    err = classify_http_error(412, "precondition")
    assert err.error_class == IntegrationErrorClass.CONFLICT


def test_classify_not_found() -> None:
    err = classify_http_error(404, "missing")
    assert err.error_class == IntegrationErrorClass.NOT_FOUND
