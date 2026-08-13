"""Hybrid retrieval with Reciprocal Rank Fusion."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from enterprise_knowledge.embeddings import EmbeddingProvider
from enterprise_knowledge.qdrant_store import QdrantStore, StoredChunk


@dataclass
class RetrievalHit:
    chunk_id: str
    document_id: str
    content: str
    score: float
    organization_id: str
    metadata: dict[str, Any]


def rrf_fuse(
    ranked_lists: list[list[str]],
    *,
    k: int = 60,
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion over lists of document/chunk ids."""
    scores: dict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class HybridRetriever:
    def __init__(
        self,
        store: QdrantStore,
        embeddings: EmbeddingProvider,
    ) -> None:
        self.store = store
        self.embeddings = embeddings

    @classmethod
    def from_settings(cls, settings: Any) -> HybridRetriever:
        from enterprise_knowledge.embeddings import HashEmbeddingProvider

        store = QdrantStore(
            url=getattr(settings, "qdrant_url", None) or None,
            api_key=getattr(settings, "qdrant_api_key", None) or None,
            collection=str(
                getattr(settings, "qdrant_collection", None) or "enterprise_ai_chunks"
            ),
        )
        return cls(store=store, embeddings=HashEmbeddingProvider())

    async def retrieve(
        self,
        *,
        organization_id: str,
        query: str,
        limit: int = 5,
    ) -> list[RetrievalHit]:
        vectors = await self.embeddings.embed([query])
        dense = await self.store.search(
            organization_id=organization_id,
            query_vector=vectors[0],
            limit=limit * 2,
        )
        # Sparse/keyword over in-memory-visible dense results (and store memory)
        sparse = _keyword_rank(query, dense, limit=limit * 2)
        dense_ids = [c.id for c in dense]
        sparse_ids = [c.id for c in sparse]
        fused = rrf_fuse([dense_ids, sparse_ids])
        by_id = {c.id: c for c in dense}
        for c in sparse:
            by_id.setdefault(c.id, c)
        hits: list[RetrievalHit] = []
        for chunk_id, score in fused[:limit]:
            chunk = by_id.get(chunk_id)
            if chunk is None:
                continue
            if chunk.organization_id != organization_id:
                continue
            hits.append(
                RetrievalHit(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    score=score,
                    organization_id=chunk.organization_id,
                    metadata=chunk.metadata,
                )
            )
        return hits


def _keyword_rank(query: str, chunks: list[StoredChunk], limit: int) -> list[StoredChunk]:
    terms = {t.lower() for t in re.findall(r"[a-zA-Z0-9]+", query) if len(t) > 2}
    if not terms:
        return chunks[:limit]
    scored: list[tuple[int, StoredChunk]] = []
    for chunk in chunks:
        text = chunk.content.lower()
        score = sum(1 for t in terms if t in text)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]] or chunks[:limit]
