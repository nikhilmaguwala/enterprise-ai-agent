"""HTTP error classification for tool gateway retries and escalation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IntegrationErrorClass(StrEnum):
    TRANSIENT = "transient"
    CLIENT = "client"
    CONFLICT = "conflict"
    AUTH = "auth"
    NOT_FOUND = "not_found"
    FATAL = "fatal"


@dataclass(slots=True)
class IntegrationError(Exception):
    message: str
    error_class: IntegrationErrorClass
    status_code: int | None = None
    retryable: bool = False
    details: dict | None = None

    def __str__(self) -> str:
        return f"{self.error_class}: {self.message}"


def classify_http_error(status_code: int, body: str | None = None) -> IntegrationError:
    text = body or f"HTTP {status_code}"
    if status_code in {408, 425, 429, 500, 502, 503, 504}:
        return IntegrationError(
            message=text,
            error_class=IntegrationErrorClass.TRANSIENT,
            status_code=status_code,
            retryable=True,
        )
    if status_code in {401, 403}:
        return IntegrationError(
            message=text,
            error_class=IntegrationErrorClass.AUTH,
            status_code=status_code,
            retryable=False,
        )
    if status_code == 404:
        return IntegrationError(
            message=text,
            error_class=IntegrationErrorClass.NOT_FOUND,
            status_code=status_code,
            retryable=False,
        )
    if status_code in {409, 412}:
        return IntegrationError(
            message=text,
            error_class=IntegrationErrorClass.CONFLICT,
            status_code=status_code,
            retryable=False,
        )
    if 400 <= status_code < 500:
        return IntegrationError(
            message=text,
            error_class=IntegrationErrorClass.CLIENT,
            status_code=status_code,
            retryable=False,
        )
    return IntegrationError(
        message=text,
        error_class=IntegrationErrorClass.FATAL,
        status_code=status_code,
        retryable=False,
    )
