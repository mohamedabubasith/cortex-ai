"""Ollama embedding client: prefers /api/embed, falls back to /api/embeddings."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _preview_body(r: httpx.Response, limit: int = 600) -> str:
    try:
        t = r.text.replace("\n", " ").replace("\r", "")
    except Exception:
        return "<unreadable>"
    return (t[:limit] + "…") if len(t) > limit else t


def _parse_embeddings_list(body: dict, *, expect: int | None) -> List[List[float]] | None:
    embs = body.get("embeddings")
    if isinstance(embs, list):
        if expect is not None and len(embs) != expect:
            return None
        out: List[List[float]] = []
        for e in embs:
            if not isinstance(e, list):
                return None
            out.append([float(x) for x in e])
        return out
    if expect == 1:
        emb = body.get("embedding")
        if isinstance(emb, list):
            return [[float(x) for x in emb]]
    return None


def _raise_with_body(r: httpx.Response) -> None:
    if r.status_code >= 400:
        logger.error(
            "Ollama embedding HTTP %s for %s body=%s",
            r.status_code,
            str(r.request.url),
            _preview_body(r),
        )
    r.raise_for_status()


@lru_cache(maxsize=1)
def get_embedding_dimension() -> int:
    """Probe vector size once per process using the configured model."""
    vec = embed_texts(["dimension-probe"])[0]
    dim = len(vec)
    if dim < 8:
        raise RuntimeError(f"Unexpected embedding dimension from Ollama: {dim}")
    logger.info("Resolved Ollama embedding dimension: %s", dim)
    return dim


def embed_texts(texts: List[str], *, timeout_s: float | None = None) -> List[List[float]]:
    """
    Embed strings via Ollama. Tries /api/embed (input + optional truncate), then legacy /api/embeddings.
    """
    if not texts:
        return []

    if timeout_s is None:
        timeout_s = min(600.0, 90.0 + 2.5 * len(texts))

    base = settings.OLLAMA_BASE_URL.rstrip("/")
    model = settings.OLLAMA_MODEL
    truncate = bool(settings.OLLAMA_EMBED_TRUNCATE)

    def post(client: httpx.Client, path: str, payload: dict) -> httpx.Response:
        return client.post(f"{base}{path}", json=payload)

    with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:

        def try_batch_embed_path(path: str, use_truncate: bool) -> List[List[float]] | None:
            payload: dict = {"model": model, "input": texts}
            if use_truncate:
                payload["truncate"] = truncate
            r = post(client, path, payload)
            if r.status_code >= 400:
                logger.warning(
                    "Ollama batch %s HTTP %s body=%s",
                    path,
                    r.status_code,
                    _preview_body(r),
                )
                return None
            try:
                body = r.json()
            except Exception as e:
                logger.warning("Ollama batch %s invalid JSON: %s", path, e)
                return None
            parsed = _parse_embeddings_list(body, expect=len(texts))
            return parsed

        def try_batch_legacy_embeddings() -> List[List[float]] | None:
            r = post(client, "/api/embeddings", {"model": model, "input": texts})
            if r.status_code >= 400:
                logger.warning(
                    "Ollama batch /api/embeddings HTTP %s body=%s",
                    r.status_code,
                    _preview_body(r),
                )
                return None
            try:
                body = r.json()
            except Exception as e:
                logger.warning("Ollama batch /api/embeddings invalid JSON: %s", e)
                return None
            return _parse_embeddings_list(body, expect=len(texts))

        # 1) Preferred: /api/embed (matches current Ollama docs; supports truncate)
        if settings.OLLAMA_PREFER_API_EMBED:
            batch = try_batch_embed_path("/api/embed", use_truncate=True)
            if batch is not None:
                return batch

        # 2) Legacy batch without truncate flag (older servers)
        if settings.OLLAMA_PREFER_API_EMBED:
            batch = try_batch_embed_path("/api/embed", use_truncate=False)
            if batch is not None:
                return batch

        # 3) Legacy /api/embeddings batch with `input`
        batch = try_batch_legacy_embeddings()
        if batch is not None:
            return batch

        # 4) Per-text: /api/embed then /api/embeddings prompt
        out: List[List[float]] = []
        for t in texts:
            if settings.OLLAMA_PREFER_API_EMBED:
                r = post(
                    client,
                    "/api/embed",
                    {"model": model, "input": t, "truncate": truncate},
                )
                if r.status_code < 400:
                    try:
                        body = r.json()
                        parsed = _parse_embeddings_list(body, expect=1)
                        if parsed:
                            out.append(parsed[0])
                            continue
                    except Exception as e:
                        logger.warning("Ollama per-text /api/embed parse error: %s", e)

                r = post(client, "/api/embed", {"model": model, "input": t})
                if r.status_code < 400:
                    try:
                        body = r.json()
                        parsed = _parse_embeddings_list(body, expect=1)
                        if parsed:
                            out.append(parsed[0])
                            continue
                    except Exception as e:
                        logger.warning("Ollama per-text /api/embed (no truncate) parse error: %s", e)

            r = post(client, "/api/embeddings", {"model": model, "prompt": t})
            _raise_with_body(r)
            body = r.json()
            emb = body.get("embedding")
            if not isinstance(emb, list):
                raise TypeError("Ollama /api/embeddings response missing 'embedding' list")
            out.append([float(x) for x in emb])

        return out
