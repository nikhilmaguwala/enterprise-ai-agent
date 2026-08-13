"""Object storage backends (filesystem, Firebase)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    storage_key: str
    byte_size: int
    checksum_sha256: str
    mime_type: str


class ObjectStorage(Protocol):
    backend_name: str

    async def save_bytes(
        self,
        *,
        storage_key: str,
        data: bytes,
        mime_type: str,
    ) -> StoredObject: ...

    async def read_bytes(self, *, storage_key: str) -> bytes: ...

    async def exists(self, *, storage_key: str) -> bool: ...

    async def delete(self, *, storage_key: str) -> None: ...

    async def signed_download_url(
        self,
        *,
        storage_key: str,
        expires_seconds: int = 3600,
    ) -> str | None: ...

    async def ensure_tenant_folders(self, *, organization_id: str) -> None: ...
