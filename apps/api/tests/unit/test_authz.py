"""Authz / permission mapping tests."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.security import ExecutionContext, permissions_for_roles


def test_admin_permissions_include_delete() -> None:
    perms = permissions_for_roles(["admin"])
    assert "documents:delete" in perms
    assert "admin:all" in perms


def test_customer_cannot_require_admin_permission() -> None:
    ctx = ExecutionContext(
        organization_id=uuid4(),
        actor_id=uuid4(),
        roles=["customer"],
        permissions=permissions_for_roles(["customer"]),
    )
    with pytest.raises(HTTPException) as exc:
        ctx.require_permission("jobs:replay")
    assert exc.value.status_code == 403
