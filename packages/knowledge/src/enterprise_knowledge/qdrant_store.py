"""Qdrant-backed vector store with tenant filtering and in-memory fallback."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass
class StoredChunk:
    id: str
    organization_id: str
    document_id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class QdrantStore:
    """Thin store. Uses qdrant-client when configured; else in-memory."""

    def __init__(
        self,
        *,
        url: str | None = None,
        api_key: str | None = None,
        collection: str = "enterprise_ai_chunks",
        dim: int = 64,
    ) -> None:
        self.url = url
        self.api_key = api_key
        self.collection = collection
        self.dim = dim
        self._memory: list[StoredChunk] = []
        self._client: Any = None
        if url and not url.startswith("https://REPLACE"):
            try:
                from qdrant_client import QdrantClient

                self._client = QdrantClient(url=url, api_key=api_key or None)
                self._ensure_collection()
            except Exception:  # noqa: BLE001 — degrade to memory
                self._client = None

    def _ensure_collection(self) -> None:
        if self._client is None:
            return
        from qdrant_client.http import models as qm

        names = {c.name for c in self._client.get_collections().collections}
        if self.collection not in names:
            self._client.create_collection(
                collection_name=self.collection,
                vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE),
            )

    async def upsert(self, chunks: list[StoredChunk]) -> None:
        if not chunks:
            return
        if self._client is None:
            ids = {c.id for c in chunks}
            self._memory = [c for c in self._memory if c.id not in ids] + chunks
            return
        from qdrant_client.http import models as qm

        points = [
            qm.PointStruct(
                id=c.id if _is_uuid(c.id) else str(uuid4()),
                vector=c.embedding,
                payload={
                    "organization_id": c.organization_id,
                    "document_id": c.document_id,
                    "content": c.content,
                    **c.metadata,
                    "chunk_id": c.id,
                },
            )
            for c in chunks
        ]
        self._client.upsert(collection_name=self.collection, points=points)

    async def search(
        self,
        *,
        organization_id: str,
        query_vector: list[float],
        limit: int = 8,
    ) -> list[StoredChunk]:
        if self._client is None:
            scored = []
            for chunk in self._memory:
                if chunk.organization_id != organization_id:
                    continue
                score = _cosine(query_vector, chunk.embedding)
                scored.append((score, chunk))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for _, c in scored[:limit]]

        from qdrant_client.http import models as qm

        try:
            response = self._client.query_points(
                collection_name=self.collection,
                query=query_vector,
                limit=limit,
                query_filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="organization_id",
                            match=qm.MatchValue(value=organization_id),
                        )
                    ]
                ),
            )
            results = response.points
        except Exception:  # noqa: BLE001 — degrade safely
            return []

        out: list[StoredChunk] = []
        for hit in results:
            payload = hit.payload or {}
            out.append(
                StoredChunk(
                    id=str(payload.get("chunk_id") or hit.id),
                    organization_id=str(payload.get("organization_id")),
                    document_id=str(payload.get("document_id")),
                    content=str(payload.get("content", "")),
                    embedding=query_vector,
                    metadata={k: v for k, v in payload.items() if k not in {"content"}},
                )
            )
        return out

    async def delete_document(self, organization_id: str, document_id: str) -> None:
        if self._client is None:
            self._memory = [
                c
                for c in self._memory
                if not (
                    c.organization_id == organization_id and c.document_id == document_id
                )
            ]
            return
        from qdrant_client.http import models as qm

        self._client.delete(
            collection_name=self.collection,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="organization_id",
                            match=qm.MatchValue(value=organization_id),
                        ),
                        qm.FieldCondition(
                            key="document_id",
                            match=qm.MatchValue(value=document_id),
                        ),
                    ]
                )
            ),
        )


def _cosine(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    dot = sum(a[i] * b[i] for i in range(n))
    na = sum(a[i] * a[i] for i in range(n)) ** 0.5
    nb = sum(b[i] * b[i] for i in range(n)) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except ValueError:
        return False
