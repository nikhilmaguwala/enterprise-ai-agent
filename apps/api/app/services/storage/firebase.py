"""Firebase Storage (Google Cloud Storage) backend."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from uuid import UUID

import firebase_admin
from firebase_admin import credentials, storage

from app.core.config import Settings
from app.services.storage.base import ObjectStorage, StoredObject
from app.services.storage.paths import list_root_prefixes

_app_initialized = False


def _init_firebase(settings: Settings) -> None:
    global _app_initialized
    if _app_initialized or firebase_admin._apps:
        _app_initialized = True
        return

    if settings.firebase_credentials_json:
        cred_dict = json.loads(settings.firebase_credentials_json)
        cred = credentials.Certificate(cred_dict)
    elif settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
    else:
        raise RuntimeError(
            "Firebase storage selected but FIREBASE_CREDENTIALS_PATH or "
            "FIREBASE_CREDENTIALS_JSON is not configured"
        )

    firebase_admin.initialize_app(
        cred,
        {"storageBucket": settings.firebase_storage_bucket},
    )
    _app_initialized = True


class FirebaseObjectStorage:
    backend_name = "firebase"

    def __init__(self, settings: Settings) -> None:
        _init_firebase(settings)
        self.settings = settings
        self.bucket = storage.bucket()

    async def save_bytes(
        self,
        *,
        storage_key: str,
        data: bytes,
        mime_type: str,
    ) -> StoredObject:
        blob = self.bucket.blob(storage_key)
        blob.upload_from_string(data, content_type=mime_type)
        checksum = hashlib.sha256(data).hexdigest()
        return StoredObject(
            storage_key=storage_key,
            byte_size=len(data),
            checksum_sha256=checksum,
            mime_type=mime_type,
        )

    async def read_bytes(self, *, storage_key: str) -> bytes:
        blob = self.bucket.blob(storage_key)
        return blob.download_as_bytes()

    async def exists(self, *, storage_key: str) -> bool:
        blob = self.bucket.blob(storage_key)
        return blob.exists()

    async def delete(self, *, storage_key: str) -> None:
        blob = self.bucket.blob(storage_key)
        if blob.exists():
            blob.delete()

    async def signed_download_url(
        self,
        *,
        storage_key: str,
        expires_seconds: int = 3600,
    ) -> str | None:
        blob = self.bucket.blob(storage_key)
        if not blob.exists():
            return None
        return blob.generate_signed_url(
            expiration=timedelta(seconds=expires_seconds),
            method="GET",
        )

    async def ensure_tenant_folders(self, *, organization_id: str) -> None:
        """Create placeholder objects so folders appear in Firebase console."""
        org = UUID(organization_id)
        for prefix in list_root_prefixes(org):
            marker_key = f"{prefix}.keep"
            blob = self.bucket.blob(marker_key)
            if not blob.exists():
                blob.upload_from_string(
                    b"ResolveAI storage folder marker\n",
                    content_type="text/plain",
                )
