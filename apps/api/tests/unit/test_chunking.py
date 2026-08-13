"""Chunking unit tests."""

from __future__ import annotations

from enterprise_knowledge.chunking import chunk_text


def test_chunk_text_splits_by_headings() -> None:
    text = "# One\n\nHello world.\n\n# Two\n\nMore content here."
    chunks = chunk_text(text, max_chars=500)
    assert len(chunks) >= 2
    assert chunks[0].content_hash
    assert all(c.token_estimate > 0 for c in chunks)


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("   ") == []
