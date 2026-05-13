"""Haystack + Unstructured + Ollama + Qdrant RAG pipeline."""
from __future__ import annotations

import asyncio
import logging
import os
import threading
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from haystack import Document
from haystack.components.preprocessors import RecursiveDocumentSplitter
from haystack.document_stores.types import DuplicatePolicy
from haystack.utils.auth import Secret
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore

from app.core.config import settings
from app.services.kb_chunk_limits import clamp_chunk_size_overlap
from app.services.ollama_embeddings import embed_texts, get_embedding_dimension
from app.services.unstructured_client import ParsingStrategy, partition_file_local

logger = logging.getLogger(__name__)

_document_store: Optional[QdrantDocumentStore] = None
_store_init_lock = threading.Lock()


def _sanitize_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, datetime):
        return val.astimezone(timezone.utc).isoformat()
    if isinstance(val, (list, tuple)):
        out = [_sanitize_value(v) for v in val]
        return [x for x in out if x is not None][:50]
    if isinstance(val, dict):
        out: Dict[str, Any] = {}
        for k, v in list(val.items())[:40]:
            sk = str(k)[:120]
            sv = _sanitize_value(v)
            if sv is not None:
                out[sk] = sv
        return out
    return str(val)[:500]


def _strip_none(meta: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in meta.items() if v is not None}


def _source_reference(meta: Dict[str, Any]) -> str:
    fn = meta.get("filename") or meta.get("source_filename") or "document"
    parts = [str(fn)]
    if meta.get("page_number") is not None:
        parts.append(f"p.{meta.get('page_number')}")
    if meta.get("section_title"):
        parts.append(str(meta.get("section_title")))
    return " — ".join(parts)


def _get_store() -> QdrantDocumentStore:
    global _document_store
    with _store_init_lock:
        if _document_store is None:
            dim = get_embedding_dimension()
            qdrant_key = (
                Secret.from_token(settings.QDRANT_API_KEY)
                if settings.QDRANT_API_KEY
                else None
            )
            logger.info(
                "[kb-ingest] QdrantDocumentStore init url=%s index=%s api_key_set=%s write_batch_size=%s",
                settings.QDRANT_URL,
                settings.QDRANT_COLLECTION,
                bool(settings.QDRANT_API_KEY),
                settings.RAG_QDRANT_WRITE_BATCH_SIZE,
            )
            _document_store = QdrantDocumentStore(
                url=settings.QDRANT_URL,
                index=settings.QDRANT_COLLECTION,
                api_key=qdrant_key,
                embedding_dim=dim,
                recreate_index=False,
                progress_bar=False,
                return_embedding=False,
                write_batch_size=settings.RAG_QDRANT_WRITE_BATCH_SIZE,
            )
    return _document_store


def _reset_store_cache() -> None:
    """Recreate document store (e.g. after Qdrant collection dimension change)."""
    global _document_store
    _document_store = None


def _elements_to_documents(
    elements: List[dict[str, Any]],
    *,
    filename: str,
    kb_id: str,
    user_id: str,
    tenant_id: Optional[str],
) -> List[Document]:
    docs: List[Document] = []
    for el_idx, el in enumerate(elements):
        text = (el.get("text") or "").strip()
        if not text:
            continue
        raw_meta = el.get("metadata") if isinstance(el.get("metadata"), dict) else {}
        page_number = raw_meta.get("page_number")
        if page_number is None:
            page_number = raw_meta.get("page")
        section_title = (
            raw_meta.get("section")
            or raw_meta.get("title")
            or raw_meta.get("category")
            or raw_meta.get("parent_id")
        )
        layout_meta = _sanitize_value(
            {
                "coordinates": raw_meta.get("coordinates"),
                "detection_class_prob": raw_meta.get("detection_class_prob"),
                "text_as_html": raw_meta.get("text_as_html"),
                "languages": raw_meta.get("languages"),
            }
        )
        unstructured_subset = _sanitize_value(
            {
                k: raw_meta.get(k)
                for k in (
                    "filename",
                    "filetype",
                    "last_modified",
                    "page_number",
                    "page_name",
                    "orig_elements",
                )
                if k in raw_meta
            }
        )
        meta = _strip_none(
            {
                "kb_id": kb_id,
                "user_id": user_id,
                "tenant_id": str(tenant_id) if tenant_id else "",
                "filename": filename,
                "source_filename": raw_meta.get("filename") or filename,
                "page_number": page_number,
                "section_title": section_title,
                "element_index": el_idx,
                "element_type": el.get("type"),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "layout": layout_meta,
                "unstructured_metadata": unstructured_subset,
            }
        )
        docs.append(Document(content=text, meta=meta))
    return docs


def _merge_unstructured_elements_for_splitter(base_docs: List[Document]) -> Document:
    """
    Unstructured yields one Haystack ``Document`` per layout element. RecursiveDocumentSplitter
    works on whole-document text, so we concatenate elements in reading order with newlines.
    This is not a chunking strategy — all splitting is delegated to Haystack.
    """
    if not base_docs:
        raise ValueError("base_docs must not be empty")

    ordered = sorted(
        base_docs,
        key=lambda d: (
            d.meta.get("page_number") is None,
            d.meta.get("page_number") or 0,
            d.meta.get("element_index") is None,
            d.meta.get("element_index") or 0,
        ),
    )
    parts = [(d.content or "").strip() for d in ordered if (d.content or "").strip()]
    if not parts:
        raise ValueError("no textual content in base_docs")

    meta = dict(ordered[0].meta or {})
    for k in ("element_index", "element_type"):
        meta.pop(k, None)

    return Document(content="\n".join(parts), meta=meta)


class RAGService:
    """Ingestion and retrieval using Haystack components, Unstructured, Ollama, and Qdrant."""

    def __init__(self) -> None:
        self._retriever_cache: dict[str, QdrantEmbeddingRetriever] = {}

    def _retriever(self) -> QdrantEmbeddingRetriever:
        key = settings.QDRANT_COLLECTION
        if key not in self._retriever_cache:
            self._retriever_cache[key] = QdrantEmbeddingRetriever(document_store=_get_store(), top_k=8)
        return self._retriever_cache[key]

    async def process_document(
        self,
        file_path: str,
        kb_id: str,
        user_id: str,
        tenant_id: str,
        chunk_size: int,
        chunk_overlap: int,
        llm_config,
        embedding_model: Optional[str] = None,
        on_progress: Optional[Callable] = None,
        parsing_strategy: str = "fast",
    ) -> Dict[str, Any]:
        """
        Parse with Unstructured → Haystack ``RecursiveDocumentSplitter`` (word units so overlap
        does not start mid-word; paragraph / sentence / line / space separators) → Ollama → Qdrant.

        Status callbacks: parsing, chunking, embedding, indexing.

        Note: boilerplate such as "Skip to main content" comes from the source file / Unstructured
        extraction; use ``hi_res`` parsing or a cleaner export if navigation chrome should be excluded.
        """
        chunk_size, chunk_overlap = clamp_chunk_size_overlap(chunk_size, chunk_overlap)
        strategy: ParsingStrategy = "hi_res" if parsing_strategy == "hi_res" else "fast"
        filename = os.path.basename(file_path)
        logger.info(
            "[kb-ingest] rag process_document start kb_id=%s file=%s strategy=%s chunk_size=%s overlap=%s",
            kb_id,
            filename,
            strategy,
            chunk_size,
            chunk_overlap,
        )

        async def _notify(status: str) -> None:
            if on_progress:
                await on_progress(status)

        await _notify("parsing")

        def _parse_sync() -> List[dict[str, Any]]:
            return partition_file_local(file_path, strategy=strategy)

        elements = await asyncio.to_thread(_parse_sync)
        if not elements:
            raise ValueError("Unstructured returned no elements for this file")
        logger.info("[kb-ingest] rag kb_id=%s parsed unstructured elements=%s", kb_id, len(elements))

        base_docs = _elements_to_documents(
            elements, filename=filename, kb_id=kb_id, user_id=user_id, tenant_id=tenant_id
        )
        if not base_docs:
            raise ValueError("No textual content extracted after parsing")
        logger.info("[kb-ingest] rag kb_id=%s base Haystack documents=%s", kb_id, len(base_docs))

        await _notify("chunking")

        def _split_sync() -> List[Document]:
            merged = _merge_unstructured_elements_for_splitter(base_docs)
            # Char overlap on ``split_unit="char"`` prefixes the last N *characters* of the previous
            # chunk, which often begins mid-word ("akes."). Use word units; map char budget ↔ words
            # with a conservative average word length (~5 chars) vs ``kb_max_chunk_chars`` clamp.
            chars_per_word = 5
            split_length_words = max(48, int(chunk_size // chars_per_word))
            overlap_words = max(0, min(int(chunk_overlap // chars_per_word), split_length_words - 1))
            splitter = RecursiveDocumentSplitter(
                split_length=split_length_words,
                split_overlap=overlap_words,
                split_unit="word",
                separators=["\n\n", "sentence", "\n", " "],
            )
            split_docs: List[Document] = splitter.run(documents=[merged])["documents"]
            normalized: List[Document] = []
            for doc in split_docs:
                content = (doc.content or "").strip()
                if not content:
                    continue
                normalized.append(replace(doc, content=content))
            n = len(normalized)
            out: List[Document] = []
            for idx, doc in enumerate(normalized):
                m = dict(doc.meta or {})
                m["chunk_index"] = idx
                m["chunk_count"] = n
                m["source_reference"] = _source_reference(m)
                out.append(replace(doc, meta=m))
            return out

        chunks = await asyncio.to_thread(_split_sync)
        chunk_texts = [c.content or "" for c in chunks if c.content]
        logger.info("[kb-ingest] rag kb_id=%s chunks after splitter=%s", kb_id, len(chunks))

        await _notify("embedding")

        def _embed_and_write() -> int:
            # One Ollama request per batch (`input` array); one Qdrant upsert per batch. Tune via RAG_EMBEDDING_BATCH_SIZE.
            batch_size = max(8, min(256, int(settings.RAG_EMBEDDING_BATCH_SIZE)))
            logger.info(
                "[kb-ingest] rag kb_id=%s embedding+Qdrant batches chunk_batch_size=%s total_chunks=%s collection=%s",
                kb_id,
                batch_size,
                len(chunks),
                settings.QDRANT_COLLECTION,
            )
            store = _get_store()
            texts = [c.content or "" for c in chunks]
            for start in range(0, len(chunks), batch_size):
                batch_docs = chunks[start : start + batch_size]
                batch_texts = texts[start : start + batch_size]
                vectors = embed_texts(batch_texts)
                if len(vectors) != len(batch_docs):
                    raise RuntimeError("Embedding batch size mismatch")
                written_batch = [replace(doc, embedding=vec) for doc, vec in zip(batch_docs, vectors, strict=True)]
                store.write_documents(written_batch, policy=DuplicatePolicy.FAIL)
            return len(chunks)

        await _notify("indexing")

        try:
            written = await asyncio.to_thread(_embed_and_write)
        except Exception as e:
            _reset_store_cache()
            low = str(e).lower()
            if "connection refused" in low or "errno 61" in low:
                raise RuntimeError(
                    f"Qdrant unreachable at {settings.QDRANT_URL!r} (connection refused). "
                    "Set QDRANT_URL to the correct host:port (native Qdrant is usually :6333; "
                    "reverse proxies often use :80 or :443)."
                ) from e
            raise

        logger.info(
            "[kb-ingest] rag kb_id=%s pipeline done chunks_written=%s",
            kb_id,
            written,
        )
        return {"success": True, "chunks": written, "chunk_texts": chunk_texts}

    async def delete_kb(self, kb_id: str) -> bool:
        try:
            store = _get_store()

            filters: Dict[str, Any] = {
                "operator": "AND",
                "conditions": [{"field": "meta.kb_id", "operator": "==", "value": kb_id}],
            }

            def _del() -> None:
                store.delete_by_filter(filters=filters)

            await asyncio.to_thread(_del)
            return True
        except Exception as e:
            logger.error("delete_kb failed for %s: %s", kb_id, e)
            return False

    async def search(
        self,
        query: str,
        config_filter: Dict[str, Any],
        llm_config,
        embedding_model: Optional[str] = None,
        k: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Embed query with Ollama, retrieve from Qdrant via Haystack, return citation-ready dicts.
        config_filter: legacy Chroma-style dict {"kb_id": "..."} or {"kb_id": {"$in": [...]}}
        is translated to Haystack filters on meta.kb_id.
        """
        try:
            vec = (await asyncio.to_thread(embed_texts, [query]))[0]
        except Exception as e:
            logger.error("Query embedding failed: %s", e)
            return []

        haystack_filter = self._legacy_filter_to_haystack(config_filter)
        retriever = self._retriever()
        try:

            def _run() -> List[Document]:
                return retriever.run(query_embedding=vec, filters=haystack_filter, top_k=k)["documents"]

            docs = await asyncio.to_thread(_run)
        except Exception as e:
            logger.error("Qdrant retrieval failed: %s", e)
            return []

        formatted: List[Dict[str, Any]] = []
        for doc in docs:
            meta = dict(doc.meta or {})
            preview = (doc.content or "")[:400]
            meta.setdefault("source_reference", _source_reference(meta))
            meta["chunk_preview"] = preview
            formatted.append(
                {
                    "content": doc.content or "",
                    "metadata": meta,
                    "score": doc.score,
                }
            )
        return formatted

    @staticmethod
    def _legacy_filter_to_haystack(config_filter: Dict[str, Any]) -> Dict[str, Any]:
        kb = config_filter.get("kb_id")
        if isinstance(kb, dict) and "$in" in kb:
            ids = kb["$in"]
            if not isinstance(ids, list) or not ids:
                return {"operator": "AND", "conditions": []}
            return {
                "operator": "OR",
                "conditions": [{"field": "meta.kb_id", "operator": "==", "value": x} for x in ids],
            }
        if isinstance(kb, str) and kb:
            return {"operator": "AND", "conditions": [{"field": "meta.kb_id", "operator": "==", "value": kb}]}
        raise ValueError("config_filter must contain kb_id or kb_id $in list")


rag_service = RAGService()
