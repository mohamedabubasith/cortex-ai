"""Clamp KB chunk / overlap to stay within configured embedding input budget (chars ≈ tokens × factor)."""

from __future__ import annotations

from app.core.config import settings


def clamp_chunk_size_overlap(chunk_size: int, chunk_overlap: int) -> tuple[int, int]:
    """Keep Haystack split_length and overlap within ``settings.kb_max_chunk_chars``."""
    mx = settings.kb_max_chunk_chars
    mn = settings.KB_MIN_CHUNK_CHARS
    cs = max(mn, min(int(chunk_size), mx))
    co_max = max(0, cs - 1)
    co = max(0, min(int(chunk_overlap), co_max))
    return cs, co
