"""
Full ingestion pipeline **without** Postgres or HTTP upload:

  disk file → Unstructured (parse) → RecursiveDocumentSplitter (chunk) → Ollama (embed)
  → Qdrant (index) → search → delete by kb_id

This is the same code path as KB ingestion (`rag_service.process_document`), minus the API
layer and DB rows.

Enable:

  export RUN_RAG_FULL_PIPELINE=1
  export QDRANT_URL='http://your-qdrant:80'          # include :80 if behind HTTP proxy
  export QDRANT_API_KEY='...'                        # when Qdrant requires it
  export QDRANT_COLLECTION='your_haystack_collection'  # must be Haystack-created / empty
  export UNSTRUCTURED_API_KEY='...'                  # if your Unstructured instance requires it
  # OLLAMA_* / UNSTRUCTURED_* default from app config or override via env

  cd backend && uv run pytest tests/test_rag_pipeline_integration.py -v -s
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import uuid

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_full_pipeline_file_parse_chunk_embed_index_search():
    if os.environ.get("RUN_RAG_FULL_PIPELINE") != "1":
        pytest.skip("Set RUN_RAG_FULL_PIPELINE=1 to run live Unstructured → Haystack → Ollama → Qdrant")

    from app.services.rag_service import rag_service

    marker = f"PIPE_{uuid.uuid4().hex[:10]}"
    kb_id = f"kb-pipeline-{uuid.uuid4().hex[:8]}"
    user_id = "pipeline-test-user"
    tenant_id = "pipeline-test-tenant"

    # Long enough for multiple Haystack chunks at split_length=256.
    body = " ".join(
        [
            f"Pipeline integration document. Unique marker: {marker}.",
            "Renewable energy and grid-scale battery storage are complementary.",
        ]
        + ["Additional context sentence for length. "] * 120
    )

    progress: list[str] = []

    async def on_progress(status: str) -> None:
        progress.append(status)

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(body)
            tmp_path = tmp.name

        # 1) Full pipeline (parse → chunk → embed → write)
        result = await rag_service.process_document(
            file_path=tmp_path,
            kb_id=kb_id,
            user_id=user_id,
            tenant_id=tenant_id,
            chunk_size=256,
            chunk_overlap=32,
            llm_config=None,
            parsing_strategy="fast",
            on_progress=on_progress,
        )

        assert result.get("success") is True, result
        written = int(result.get("chunks") or 0)
        assert written >= 1, "indexing should write at least one chunk"
        assert written >= 2, "long fixture should produce multiple chunks (chunking stage)"

        assert progress[:4] == [
            "parsing",
            "chunking",
            "embedding",
            "indexing",
        ], f"unexpected progress order: {progress}"

        chunk_texts = result.get("chunk_texts") or []
        assert any(marker in t for t in chunk_texts), "marker should appear in at least one chunk body"

        # 2) Search (retrieve from Qdrant)
        results = await rag_service.search(
            f"What is the unique marker {marker}?",
            {"kb_id": kb_id},
            llm_config=None,
            k=8,
        )
        assert isinstance(results, list) and len(results) >= 1
        blob = " ".join(str(r.get("content", "")) for r in results)
        assert marker in blob, f"marker not in search hits: {blob[:400]!r}"

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        await rag_service.delete_kb(kb_id)
