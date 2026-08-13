"""Simple section-aware text chunking."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass(slots=True)
class TextChunk:
    index: int
    content: str
    content_hash: str
    section_title: str | None = None
    token_estimate: int = 0


_HEADING_RE = re.compile(r"^(#{1,3}\s+.+|[A-Z][A-Za-z0-9 /-]{3,80})$", re.MULTILINE)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def chunk_text(
    text: str,
    *,
    max_chars: int = 800,
    overlap: int = 100,
) -> list[TextChunk]:
    """Chunk text by headings then by sliding window."""
    cleaned = text.strip()
    if not cleaned:
        return []

    sections: list[tuple[str | None, str]] = []
    parts = re.split(r"\n(?=#{1,3}\s)", cleaned)
    if len(parts) == 1:
        # Fallback: split on blank lines into paragraphs
        paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
        sections = [(None, "\n\n".join(paragraphs))]
    else:
        for part in parts:
            lines = part.strip().splitlines()
            title = lines[0].lstrip("# ").strip() if lines else None
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else part.strip()
            sections.append((title, body or part.strip()))

    chunks: list[TextChunk] = []
    index = 0
    for title, body in sections:
        if len(body) <= max_chars:
            digest = hashlib.sha256(body.encode()).hexdigest()
            chunks.append(
                TextChunk(
                    index=index,
                    content=body,
                    content_hash=digest,
                    section_title=title,
                    token_estimate=_estimate_tokens(body),
                )
            )
            index += 1
            continue

        start = 0
        while start < len(body):
            end = min(len(body), start + max_chars)
            piece = body[start:end].strip()
            if piece:
                digest = hashlib.sha256(piece.encode()).hexdigest()
                chunks.append(
                    TextChunk(
                        index=index,
                        content=piece,
                        content_hash=digest,
                        section_title=title,
                        token_estimate=_estimate_tokens(piece),
                    )
                )
                index += 1
            if end >= len(body):
                break
            start = max(0, end - overlap)
    return chunks
