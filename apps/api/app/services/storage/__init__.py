"""Storage backend factory."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import Settings, get_settings
from app.services.storage.base import ObjectStorage
from app.services.storage.filesystem import FilesystemObjectStorage
from app.services.storage.firebase import FirebaseObjectStorage


@lru_cache
def get_object_storage() -> ObjectStorage:
    settings = get_settings()
    return build_object_storage(settings)


def build_object_storage(settings: Settings) -> ObjectStorage:
    if settings.object_storage_backend == "firebase":
        return FirebaseObjectStorage(settings)
    return FilesystemObjectStorage(settings.object_storage_path)
