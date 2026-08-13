"""Knowledge compatibility aliases for the web UI."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.schemas import DocumentListOut, DocumentOut

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=DocumentListOut)
async def list_knowledge_documents(
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> DocumentListOut:
    ctx.require_permission("documents:read")
    stmt = (
        select(m.Document)
        .where(
            m.Document.organization_id == ctx.organization_id,
            m.Document.status != "deleted",
        )
        .order_by(m.Document.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    items: list[DocumentOut] = []
    for doc in rows:
        chunk_count = (
            await db.execute(
                select(func.count())
                .select_from(m.DocumentChunk)
                .where(
                    m.DocumentChunk.organization_id == ctx.organization_id,
                    m.DocumentChunk.document_id == doc.id,
                )
            )
        ).scalar_one()
        out = DocumentOut.model_validate(doc)
        out.chunk_count = int(chunk_count or 0)
        items.append(out)
    return DocumentListOut(items=items)
