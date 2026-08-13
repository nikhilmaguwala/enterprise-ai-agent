"""Object storage path helpers for ResolveAI assets in Firebase/GCS."""

from __future__ import annotations

import re
from uuid import UUID

STORAGE_ROOT = "resolve-ai"

# Top-level layout under resolve-ai/{org_id}/:
#   documents/pdfs|images|other/{document_id}/{filename}
#   attachments/{attachment_id}/{filename}
#   exports/{export_id}/{filename}
DOCUMENTS_PREFIX = "documents"
ATTACHMENTS_PREFIX = "attachments"
EXPORTS_PREFIX = "exports"


def sanitize_filename(name: str, *, max_length: int = 120) -> str:
    base = name.strip().replace("\\", "/").split("/")[-1] or "file"
    base = re.sub(r"[^\w.\- ()]", "_", base)
    base = re.sub(r"_+", "_", base).strip("._")
    if not base:
        base = "file"
    if len(base) > max_length:
        stem, dot, ext = base.rpartition(".")
        if dot:
            keep = max(1, max_length - len(ext) - 1)
            base = f"{stem[:keep]}.{ext}"
        else:
            base = base[:max_length]
    return base


def document_folder(mime_type: str) -> str:
    lowered = mime_type.lower()
    if lowered == "application/pdf" or lowered.endswith("/pdf"):
        return "pdfs"
    if lowered.startswith("image/"):
        return "images"
    return "other"


def build_document_storage_key(
    *,
    organization_id: UUID,
    document_id: UUID,
    filename: str,
    mime_type: str,
) -> str:
    folder = document_folder(mime_type)
    safe_name = sanitize_filename(filename)
    return (
        f"{STORAGE_ROOT}/{organization_id}/{DOCUMENTS_PREFIX}/"
        f"{folder}/{document_id}/{safe_name}"
    )


def build_attachment_storage_key(
    *,
    organization_id: UUID,
    attachment_id: UUID,
    filename: str,
) -> str:
    safe_name = sanitize_filename(filename)
    return (
        f"{STORAGE_ROOT}/{organization_id}/{ATTACHMENTS_PREFIX}/"
        f"{attachment_id}/{safe_name}"
    )


def build_export_storage_key(
    *,
    organization_id: UUID,
    export_id: UUID,
    filename: str,
) -> str:
    safe_name = sanitize_filename(filename)
    return (
        f"{STORAGE_ROOT}/{organization_id}/{EXPORTS_PREFIX}/"
        f"{export_id}/{safe_name}"
    )


def list_root_prefixes(organization_id: UUID) -> list[str]:
    """Virtual folder prefixes created per tenant."""
    base = f"{STORAGE_ROOT}/{organization_id}"
    return [
        f"{base}/{DOCUMENTS_PREFIX}/pdfs/",
        f"{base}/{DOCUMENTS_PREFIX}/images/",
        f"{base}/{DOCUMENTS_PREFIX}/other/",
        f"{base}/{ATTACHMENTS_PREFIX}/",
        f"{base}/{EXPORTS_PREFIX}/",
    ]
