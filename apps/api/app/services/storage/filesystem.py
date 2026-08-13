"""Local filesystem object storage."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.services.storage.base import ObjectStorage, StoredObject


class FilesystemObjectStorage:
    backend_name = "filesystem"

    def __init__(self, root: str) -> None:
        self.root = Path(root)

    def _path(self, storage_key: str) -> Path:
        return self.root / storage_key

    async def save_bytes(
        self,
        *,
        storage_key: str,
        data: bytes,
        mime_type: str,
    ) -> StoredObject:
        path = self._path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()
        return StoredObject(
            storage_key=storage_key,
            byte_size=len(data),
            checksum_sha256=checksum,
            mime_type=mime_type,
        )

    async def read_bytes(self, *, storage_key: str) -> bytes:
        return self._path(storage_key).read_bytes()

    async def exists(self, *, storage_key: str) -> bool:
        return self._path(storage_key).is_file()

    async def delete(self, *, storage_key: str) -> None:
        path = self._path(storage_key)
        if path.is_file():
            path.unlink()

    async def signed_download_url(
        self,
        *,
        storage_key: str,
        expires_seconds: int = 3600,
    ) -> str | None:
        _ = expires_seconds
        if not await self.exists(storage_key=storage_key):
            return None
        return str(self._path(storage_key).resolve())

    async def ensure_tenant_folders(self, *, organization_id: str) -> None:
        from app.services.storage.paths import list_root_prefixes
        from uuid import UUID

        org = UUID(organization_id)
        for prefix in list_root_prefixes(org):
            (self.root / prefix).mkdir(parents=True, exist_ok=True)
