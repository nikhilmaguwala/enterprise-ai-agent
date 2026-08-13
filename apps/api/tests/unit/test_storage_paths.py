"""Storage path layout tests."""

from uuid import UUID

from app.services.storage.paths import (
    build_document_storage_key,
    document_folder,
    list_root_prefixes,
    sanitize_filename,
)

ORG = UUID("11111111-1111-1111-1111-111111111111")
DOC = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaa0001")


def test_document_folder_by_mime() -> None:
    assert document_folder("application/pdf") == "pdfs"
    assert document_folder("image/png") == "images"
    assert document_folder("text/plain") == "other"


def test_build_document_storage_key() -> None:
    key = build_document_storage_key(
        organization_id=ORG,
        document_id=DOC,
        filename="Shipping Policy.pdf",
        mime_type="application/pdf",
    )
    assert key.startswith("resolve-ai/11111111-1111-1111-1111-111111111111/documents/pdfs/")
    assert key.endswith("/Shipping Policy.pdf")


def test_sanitize_filename() -> None:
    assert sanitize_filename("../../evil.pdf") == "evil.pdf"


def test_list_root_prefixes() -> None:
    prefixes = list_root_prefixes(ORG)
    assert any(p.endswith("documents/pdfs/") for p in prefixes)
    assert any(p.endswith("attachments/") for p in prefixes)
