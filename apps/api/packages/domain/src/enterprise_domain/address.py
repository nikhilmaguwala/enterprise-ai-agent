"""Deterministic address validation (never LLM-decided)."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")
_STATE_RE = re.compile(r"^[A-Z]{2}$")


class Address(BaseModel):
    line1: str = Field(min_length=1, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=2, max_length=2)
    postal_code: str = Field(min_length=5, max_length=10)
    country: str = Field(default="US", min_length=2, max_length=2)

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("postal_code")
    @classmethod
    def normalize_postal(cls, value: str) -> str:
        return value.strip()

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "line1": self.line1.strip(),
            "line2": (self.line2 or "").strip() or None,
            "city": self.city.strip(),
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
        }


def validate_address(payload: dict[str, Any]) -> tuple[Address | None, list[str]]:
    """Validate an address payload. Returns (address, errors)."""
    errors: list[str] = []
    try:
        address = Address.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 — collect pydantic errors
        return None, [str(exc)]

    if not _STATE_RE.match(address.state):
        errors.append("state must be a 2-letter US state code")
    if not _ZIP_RE.match(address.postal_code):
        errors.append("postal_code must be ZIP or ZIP+4")
    if address.country != "US":
        errors.append("only US addresses are supported in v1")
    if not address.line1.strip():
        errors.append("line1 is required")

    if errors:
        return None, errors
    return address, []
