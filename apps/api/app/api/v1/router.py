"""API v1 router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    agent_runs,
    approvals,
    audit,
    auth,
    conversations,
    documents,
    evaluations,
    events,
    health,
    inbox,
    integrations,
    jobs,
    knowledge,
    notifications,
    operations,
    runs,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(conversations.router)
api_router.include_router(events.router)
api_router.include_router(approvals.router)
api_router.include_router(documents.router)
api_router.include_router(knowledge.router)
api_router.include_router(agent_runs.router)
api_router.include_router(runs.router)
api_router.include_router(jobs.router)
api_router.include_router(operations.router)
api_router.include_router(inbox.router)
api_router.include_router(evaluations.router)
api_router.include_router(audit.router)
api_router.include_router(notifications.router)
api_router.include_router(integrations.router)
