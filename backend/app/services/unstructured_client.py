"""HTTP client for deployed Unstructured general API (partition)."""
from __future__ import annotations

import logging
import mimetypes
import os
from typing import Any, List, Literal

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ParsingStrategy = Literal["fast", "hi_res"]


def _strategy_param(strategy: ParsingStrategy) -> str:
    return "fast" if strategy == "fast" else "hi_res"


def partition_file_local(
    file_path: str,
    *,
    strategy: ParsingStrategy = "fast",
    timeout_s: float = 900.0,
) -> List[dict[str, Any]]:
    """
    Send a local file to the Unstructured general API and return the JSON element list.

    Preserves Unstructured element shape (type, text, metadata) for downstream citation metadata.
    """
    base = settings.UNSTRUCTURED_API_URL.rstrip("/")
    path = settings.UNSTRUCTURED_GENERAL_PATH.lstrip("/")
    url = f"{base}/{path}"
    filename = os.path.basename(file_path)
    mime, _ = mimetypes.guess_type(filename)
    mime = mime or "application/octet-stream"

    params = {"strategy": _strategy_param(strategy)}

    headers: dict[str, str] = {}
    if settings.UNSTRUCTURED_API_KEY:
        headers["unstructured-api-key"] = settings.UNSTRUCTURED_API_KEY

    with open(file_path, "rb") as f:
        files = {"files": (filename, f, mime)}
        with httpx.Client(timeout=timeout_s, follow_redirects=True) as client:
            resp = client.post(url, files=files, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

    if not isinstance(data, list):
        raise ValueError(f"Unstructured API returned non-list JSON: {type(data).__name__}")

    return data
