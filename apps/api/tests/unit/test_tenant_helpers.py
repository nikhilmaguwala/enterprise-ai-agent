"""Tenant isolation helper tests."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.security import ExecutionContext
from app.services.tenant import reject_org_spoof


def test_reject_org_spoof_blocks_mismatched_body_org() -> None:
    ctx = ExecutionContext(organization_id=uuid4(), actor_id=uuid4(), roles=["customer"])
    with pytest.raises(HTTPException) as exc:
        reject_org_spoof(uuid4(), ctx)
    assert exc.value.status_code == 403


def test_reject_org_spoof_allows_matching_org() -> None:
    org = uuid4()
    ctx = ExecutionContext(organization_id=org, actor_id=uuid4(), roles=["customer"])
    reject_org_spoof(org, ctx)
