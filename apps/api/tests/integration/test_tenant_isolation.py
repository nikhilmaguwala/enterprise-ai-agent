"""Integration: tenant A cannot read tenant B resources; body org spoof fails."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import mint_dev_token
from app.db.base import Base
from app.db import models as m
from app.db.session import get_db
from app.main import app


@pytest.fixture
async def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEV_AUTH_ENABLED", "true")
    monkeypatch.setenv("DEV_AUTH_SECRET", "test-secret-for-unit-tests-only")
    monkeypatch.setenv("INTERNAL_JOB_HMAC_KEY", "test-hmac-key-32-bytes-minimum!")
    monkeypatch.setenv(
        "DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    )

    # Rebuild settings cache and engine for sqlite
    from app.core.config import get_settings
    from app.db import session as db_session

    get_settings.cache_clear()
    settings = get_settings()
    engine = create_async_engine(settings.database_url, future=True)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    org_a = uuid4()
    org_b = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    async with Session() as session:
        session.add_all(
            [
                m.Organization(id=org_a, name="A", slug="a", status="active", settings={}),
                m.Organization(id=org_b, name="B", slug="b", status="active", settings={}),
                m.User(id=user_a, email="a@test", display_name="A"),
                m.User(id=user_b, email="b@test", display_name="B"),
            ]
        )
        await session.flush()
        convo_b = m.Conversation(
            organization_id=org_b,
            created_by_user_id=user_b,
            status="open",
            channel="web",
            metadata_={},
        )
        session.add(convo_b)
        await session.flush()
        run_b = m.AgentRun(
            organization_id=org_b,
            conversation_id=convo_b.id,
            status="paused",
            graph_version="v1",
            state={},
            started_at=datetime.now(UTC),
        )
        session.add(run_b)
        await session.flush()
        approval_b = m.Approval(
            organization_id=org_b,
            conversation_id=convo_b.id,
            agent_run_id=run_b.id,
            action_type="address_change",
            payload={},
            payload_hash="x",
            status="pending",
            requested_by_user_id=user_b,
        )
        session.add(approval_b)
        await session.commit()
        convo_b_id = convo_b.id
        approval_b_id = approval_b.id

    async def override_db():
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    token_a = mint_dev_token(
        organization_id=org_a,
        actor_id=user_a,
        roles=["customer"],
        settings=settings,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield {
            "client": ac,
            "token_a": token_a,
            "org_a": org_a,
            "org_b": org_b,
            "convo_b_id": convo_b_id,
            "approval_b_id": approval_b_id,
            "settings": settings,
        }

    app.dependency_overrides.clear()
    await engine.dispose()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_tenant_a_cannot_read_tenant_b_conversation(client) -> None:
    ac = client["client"]
    headers = {"Authorization": f"Bearer {client['token_a']}"}
    resp = await ac.get(f"/api/v1/conversations/{client['convo_b_id']}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_tenant_a_cannot_read_tenant_b_approval(client) -> None:
    ac = client["client"]
    headers = {"Authorization": f"Bearer {client['token_a']}"}
    resp = await ac.get(f"/api/v1/approvals/{client['approval_b_id']}", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_body_org_id_spoof_fails(client) -> None:
    ac = client["client"]
    headers = {"Authorization": f"Bearer {client['token_a']}"}
    resp = await ac.post(
        "/api/v1/conversations",
        headers=headers,
        json={"subject": "hack", "organization_id": str(client["org_b"])},
    )
    assert resp.status_code == 403
