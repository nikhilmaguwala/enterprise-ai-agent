"""Document upload/list/get/delete routes."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import ExecutionContext, get_execution_context
from app.db import models as m
from app.db.session import get_db
from app.schemas import (
    DocumentCompleteRequest,
    DocumentOut,
    DocumentPresignRequest,
    DocumentPresignResponse,
    DocumentUploadResponse,
)
from app.services.audit import AuditService
from app.services.jobs import JobQueue
from app.services.storage import build_object_storage, get_object_storage
from app.services.storage.paths import build_document_storage_key
from app.services.tenant import get_tenant_row, reject_org_spoof

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@router.post("/presign", response_model=DocumentPresignResponse)
async def presign(
    body: DocumentPresignRequest,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentPresignResponse:
    reject_org_spoof(body.organization_id, ctx)
    ctx.require_permission("documents:write")
    storage = build_object_storage(settings)
    await storage.ensure_tenant_folders(organization_id=str(ctx.organization_id))

    doc_id = uuid4()
    storage_key = build_document_storage_key(
        organization_id=ctx.organization_id,
        document_id=doc_id,
        filename=body.title,
        mime_type=body.mime_type,
    )
    doc = m.Document(
        id=doc_id,
        organization_id=ctx.organization_id,
        title=body.title,
        status="uploading",
        mime_type=body.mime_type,
        storage_key=storage_key,
        byte_size=body.byte_size,
        uploaded_by_user_id=ctx.actor_id,
    )
    db.add(doc)
    await db.commit()
    upload_url = f"{settings.api_url}/api/v1/documents/{doc_id}/upload"
    return DocumentPresignResponse(
        document_id=doc_id,
        upload_url=upload_url,
        storage_key=storage_key,
    )


@router.put("/{document_id}/upload", response_model=DocumentUploadResponse)
@router.post("/{document_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    document_id: UUID,
    file: UploadFile = File(...),
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentUploadResponse:
    ctx.require_permission("documents:write")
    doc = await get_tenant_row(db, m.Document, document_id, ctx)
    if doc.status not in {"uploading", "pending"}:
        raise HTTPException(status_code=409, detail="document not accepting uploads")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty upload")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="file exceeds 25MB limit")

    mime_type = file.content_type or doc.mime_type or "application/octet-stream"
    doc.mime_type = mime_type

    storage = build_object_storage(settings)
    stored = await storage.save_bytes(
        storage_key=doc.storage_key,
        data=data,
        mime_type=mime_type,
    )
    doc.byte_size = stored.byte_size
    doc.checksum_sha256 = stored.checksum_sha256
    doc.status = "uploading"
    doc.version += 1

    await AuditService(db).record(
        organization_id=ctx.organization_id,
        actor_id=ctx.actor_id,
        action="document.uploaded",
        resource_type="document",
        resource_id=str(doc.id),
        payload={"byte_size": stored.byte_size, "storage_key": doc.storage_key},
    )
    await db.commit()
    await db.refresh(doc)

    return DocumentUploadResponse(
        document_id=doc.id,
        storage_key=doc.storage_key,
        byte_size=stored.byte_size,
        checksum_sha256=stored.checksum_sha256,
        mime_type=mime_type,
    )


@router.post("/{document_id}/complete", response_model=DocumentOut)
async def complete(
    document_id: UUID,
    body: DocumentCompleteRequest,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentOut:
    reject_org_spoof(body.organization_id, ctx)
    ctx.require_permission("documents:write")
    doc = await get_tenant_row(db, m.Document, document_id, ctx)

    storage = build_object_storage(settings)
    if not await storage.exists(storage_key=doc.storage_key):
        raise HTTPException(status_code=400, detail="uploaded file not found in storage")

    if body.checksum_sha256 and doc.checksum_sha256:
        if body.checksum_sha256 != doc.checksum_sha256:
            raise HTTPException(status_code=400, detail="checksum mismatch")

    doc.status = "processing"
    if body.checksum_sha256:
        doc.checksum_sha256 = body.checksum_sha256
    doc.version += 1

    await JobQueue(db).enqueue(
        job_type="document.ingest",
        payload={"document_id": str(doc.id)},
        organization_id=ctx.organization_id,
    )
    await AuditService(db).record(
        organization_id=ctx.organization_id,
        actor_id=ctx.actor_id,
        action="document.complete",
        resource_type="document",
        resource_id=str(doc.id),
    )
    await db.commit()
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.get("/{document_id}/download-url")
async def download_url(
    document_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | None]:
    ctx.require_permission("documents:read")
    doc = await get_tenant_row(db, m.Document, document_id, ctx)
    if doc.status == "deleted":
        raise HTTPException(status_code=404, detail="not found")

    storage = get_object_storage()
    url = await storage.signed_download_url(storage_key=doc.storage_key)
    return {"url": url, "storage_key": doc.storage_key}


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentOut]:
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
    return [DocumentOut.model_validate(r) for r in rows]


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
) -> DocumentOut:
    ctx.require_permission("documents:read")
    doc = await get_tenant_row(db, m.Document, document_id, ctx)
    if doc.status == "deleted":
        raise HTTPException(status_code=404, detail="not found")
    return DocumentOut.model_validate(doc)


@router.delete("/{document_id}", response_model=DocumentOut)
async def delete_document(
    document_id: UUID,
    ctx: ExecutionContext = Depends(get_execution_context),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DocumentOut:
    ctx.require_permission("documents:delete")
    doc = await get_tenant_row(db, m.Document, document_id, ctx)
    storage = build_object_storage(settings)
    await storage.delete(storage_key=doc.storage_key)
    doc.status = "deleted"
    doc.version += 1
    await AuditService(db).record(
        organization_id=ctx.organization_id,
        actor_id=ctx.actor_id,
        action="document.deleted",
        resource_type="document",
        resource_id=str(doc.id),
    )
    await db.commit()
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)
