"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path
import asyncio

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.middleware import RequestIdMiddleware
from app.mocks.router import router as mocks_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    settings.validate_runtime()
    setup_logging(json_logs=settings.app_env != "development")
    if settings.run_migrations_on_startup:
        alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

        def _upgrade() -> None:
            command.upgrade(alembic_cfg, "head")

        await asyncio.to_thread(_upgrade)
        logger.info("migrations_applied")
    logger.info(
        "api_starting",
        app_env=settings.app_env,
        git_sha=settings.git_sha,
        graph_version=settings.graph_version,
    )
    yield
    logger.info("api_stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Enterprise AI Support Agent API",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestIdMiddleware)
    register_exception_handlers(application)

    # Root-level health/version (also available under /api/v1/...)
    from app.api.v1 import health as health_routes

    application.include_router(health_routes.router)
    application.include_router(api_router)
    if settings.embedded_mocks_enabled:
        application.include_router(mocks_router)

    @application.get("/")
    async def root() -> dict[str, str]:
        return {"service": "enterprise-ai-api", "docs": "/docs"}

    return application


app = create_app()
