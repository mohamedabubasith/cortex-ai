"""
Cortex KB — async HTTP client.

Wraps the external Cortex KB service API.

Global config (env):
    CORTEX_KB_URL      e.g. https://knowledge.basivo.in
    CORTEX_KB_API_KEY  admin key (used to provision per-tenant keys + as fallback)

Per-tenant key:
    Each cortex-ai Tenant stores its own kb_api_key (provisioned on registration).
    Pass it as api_key= to all calls for proper tenant isolation in the KB service.
    If not provided, falls back to CORTEX_KB_API_KEY.

is_configured() must be True for any of these functions to be called.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


# ── Config helpers ────────────────────────────────────────────────────────────

def is_configured() -> bool:
    """True when both KB URL and admin API key are set."""
    return bool(settings.CORTEX_KB_URL and settings.CORTEX_KB_API_KEY)


def _headers(api_key: Optional[str] = None) -> Dict[str, str]:
    key = api_key or settings.CORTEX_KB_API_KEY
    return {"X-Api-Key": key}


def _base() -> str:
    return settings.CORTEX_KB_URL.rstrip("/")


# ── Tenant provisioning (admin) ───────────────────────────────────────────────

async def provision_kb_tenant(tenant_name: str) -> Optional[str]:
    """
    Create a new isolated KB tenant + editor API key.
    Called once when a new cortex-ai tenant is registered.

    Uses the global admin key (CORTEX_KB_API_KEY).
    Returns the raw API key string, or None on failure.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            # 1. Create KB tenant
            resp = await client.post(
                f"{_base()}/admin/tenants",
                json={"name": tenant_name},
                headers=_headers(),
            )
            resp.raise_for_status()
            kb_tenant_id = resp.json()["tenant_id"]

            # 2. Create editor API key for that tenant
            resp2 = await client.post(
                f"{_base()}/admin/api-keys",
                json={
                    "label": f"cortex-ai:{tenant_name}",
                    "role": "editor",
                    "tenant_id": kb_tenant_id,
                },
                headers=_headers(),
            )
            resp2.raise_for_status()
            raw_key: str = resp2.json()["raw_key"]
            logger.info("Provisioned KB tenant %s for cortex tenant '%s'", kb_tenant_id, tenant_name)
            return raw_key

    except Exception as exc:
        logger.error("Failed to provision KB tenant for '%s': %s", tenant_name, exc)
        return None


# ── Upload ────────────────────────────────────────────────────────────────────

async def kb_upload(
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    POST /ingest/upload
    Returns KB service response: {document_id, status, message}
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
        resp = await client.post(
            f"{_base()}/ingest/upload",
            files={"file": (filename, file_bytes, mime_type)},
            headers=_headers(api_key),
        )
        resp.raise_for_status()
        return resp.json()


# ── Status ────────────────────────────────────────────────────────────────────

async def kb_get_status(
    document_id: str,
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    GET /status/{document_id}
    Returns {overall_status, stages, progress_pct, ...} or None if 404.
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
        resp = await client.get(
            f"{_base()}/status/{document_id}",
            headers=_headers(api_key),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()


def map_kb_status(overall_status: str, stages: Optional[Dict] = None) -> str:
    """
    Map Cortex KB overall_status to cortex-ai KnowledgeBase.status values.

    Cortex KB sets doc.status directly to the current stage name while
    processing (parsing, embedding) — not just "pending". Map all known
    values explicitly so nothing falls through to "queued".

    KB overall_status  →  cortex-ai status
    pending            →  queued (or stage name if a stage is processing)
    parsing            →  parsing
    embedding          →  embedding
    indexed            →  completed
    error/*_failed     →  failed
    """
    if overall_status == "indexed":
        return "completed"
    if overall_status in ("failed", "error", "parse_failed", "chunk_failed",
                          "embed_failed", "index_failed"):
        return "failed"
    # Direct stage-name statuses set by cortex-kb workers
    if overall_status == "parsing":
        return "parsing"
    if overall_status in ("chunked", "chunking"):
        return "chunking"
    if overall_status == "embedding":
        return "embedding"
    if overall_status == "indexing":
        return "indexing"
    # "pending" — inspect individual stage statuses for finer granularity
    if overall_status == "pending":
        if stages:
            for stage_name, cortex_name in [
                ("parse", "parsing"),
                ("chunk", "chunking"),
                ("embed", "embedding"),
                ("index", "indexing"),
            ]:
                if stages.get(stage_name, {}).get("status") == "processing":
                    return cortex_name
        return "queued"
    return "queued"


# ── Delete ────────────────────────────────────────────────────────────────────

async def kb_delete(
    document_id: str,
    api_key: Optional[str] = None,
) -> bool:
    """DELETE /documents/{document_id}. Returns True on 202/404."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.delete(
                f"{_base()}/documents/{document_id}",
                headers=_headers(api_key),
            )
            return resp.status_code in (202, 404)
    except Exception as exc:
        logger.warning("kb_delete failed for %s: %s", document_id, exc)
        return False


# ── Search ────────────────────────────────────────────────────────────────────

async def kb_search(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = 10,
    mode: str = "hybrid",
    min_score: float = 0.0,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    POST /search — returns list of {text, score, document_id, filename, ...}
    document_id scopes search to one document; omit to search all tenant docs.
    """
    body: Dict[str, Any] = {
        "query": query,
        "top_k": top_k,
        "mode": mode,
        "min_score": min_score,
    }
    if document_id:
        body["document_id"] = document_id

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.post(
                f"{_base()}/search",
                json=body,
                headers=_headers(api_key),
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
    except Exception as exc:
        logger.error("kb_search failed: %s", exc)
        return []


async def kb_search_multi(
    query: str,
    document_ids: List[str],
    top_k: int = 10,
    mode: str = "hybrid",
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search across multiple documents in parallel, merge + sort by score.
    If document_ids is empty, searches all tenant docs (no filter).
    """
    import asyncio

    if not document_ids:
        return await kb_search(query, top_k=top_k, mode=mode, api_key=api_key)

    tasks = [
        kb_search(query, document_id=doc_id, top_k=top_k, mode=mode, api_key=api_key)
        for doc_id in document_ids
    ]
    results_per_doc = await asyncio.gather(*tasks, return_exceptions=True)

    merged: List[Dict[str, Any]] = []
    for r in results_per_doc:
        if isinstance(r, list):
            merged.extend(r)

    merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return merged[:top_k]


# ── List documents ────────────────────────────────────────────────────────────

async def kb_list_documents(
    limit: int = 50,
    offset: int = 0,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """GET /documents — list all documents for this API-key tenant."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            resp = await client.get(
                f"{_base()}/documents",
                params={"limit": limit, "offset": offset},
                headers=_headers(api_key),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("kb_list_documents failed: %s", exc)
        return []
