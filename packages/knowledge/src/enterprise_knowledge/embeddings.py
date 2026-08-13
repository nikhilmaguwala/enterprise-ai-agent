"""Embedding provider protocol and deterministic hash fallback."""

from __future__ import annotations

import hashlib
import math
import struct
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    dim: int

    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class HashEmbeddingProvider:
    """Deterministic local embeddings for demos/tests without an API key."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        seed = digest
        while len(values) < self.dim:
            for i in range(0, len(seed), 4):
                if len(values) >= self.dim:
                    break
                chunk = seed[i : i + 4]
                if len(chunk) < 4:
                    chunk = chunk.ljust(4, b"\0")
                (n,) = struct.unpack("!I", chunk)
                values.append(((n % 10000) / 10000.0) * 2 - 1)
            seed = hashlib.sha256(seed).digest()
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]
