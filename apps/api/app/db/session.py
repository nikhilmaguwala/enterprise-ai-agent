"""Async SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        connect_args: dict = {}
        if settings.database_requires_ssl:
            import ssl

            connect_args["ssl"] = ssl.create_default_context()
        kwargs: dict = {
            "pool_pre_ping": True,
            "echo": settings.app_env == "development",
            "connect_args": connect_args,
        }
        _engine = create_async_engine(settings.database_url, **kwargs)
        _session_factory = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def reset_engine() -> None:
    global _engine, _session_factory
    _engine = None
    _session_factory = None


class _EngineProxy:
    def __getattr__(self, name: str):
        return getattr(get_engine(), name)


class _SessionLocalProxy:
    def __call__(self, *args, **kwargs):
        return get_session_factory()(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(get_session_factory(), name)


engine = _EngineProxy()
SessionLocal = _SessionLocalProxy()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session
