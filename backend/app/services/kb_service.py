"""
Knowledge Base Service.

Routes all KB operations through the external Cortex KB service when
CORTEX_KB_URL + CORTEX_KB_API_KEY are configured.  Falls back to the
local Haystack → Unstructured → Ollama → Qdrant pipeline otherwise.

New records get external_doc_id populated; legacy records without it
continue to work via local RAG.
"""
import asyncio
import logging
import os
import traceback
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from app.repositories.kb_repository import KBRepository
from app.services.rag_service import rag_service
from app.services.neo4j_service import neo4j_service
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models import models
from app.services import cortex_kb_client as kb_client

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_kb_api_key(tenant_id: Optional[str]) -> Optional[str]:
    """
    Return the per-tenant kb_api_key (stored on Tenant row).
    Falls back to None — callers that pass None to kb_client use global key.
    """
    if not tenant_id:
        return None
    try:
        async with AsyncSessionLocal() as session:
            row = (await session.execute(
                select(models.Tenant.kb_api_key).where(models.Tenant.id == tenant_id)
            )).scalar_one_or_none()
            return row
    except Exception:
        return None


# ── Background helpers ────────────────────────────────────────────────────────

async def _sync_kb_status_loop(kb_id: str, external_doc_id: str, tenant_id: Optional[str] = None) -> None:
    """
    Poll the Cortex KB service every 5 s until the document reaches a
    terminal state (completed / failed), then update the local DB record.
    Times out after 10 min (120 × 5 s).
    """
    api_key = await _get_kb_api_key(tenant_id)
    for _ in range(300):
        await asyncio.sleep(2)
        try:
            data = await kb_client.kb_get_status(external_doc_id, api_key=api_key)
            if not data:
                logger.warning("[kb-sync] %s not found in KB service", external_doc_id)
                break

            overall = data.get("overall_status", "")
            stages = data.get("stages", {})
            mapped = kb_client.map_kb_status(overall, stages)

            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(models.KnowledgeBase)
                    .where(models.KnowledgeBase.id == kb_id)
                    .values(status=mapped)
                )
                await session.commit()

            logger.info("[kb-sync] kb_id=%s external=%s overall=%s → local=%s",
                        kb_id, external_doc_id, overall, mapped)

            if mapped in ("completed", "failed"):
                break
        except Exception as exc:
            logger.warning("[kb-sync] kb_id=%s poll error: %s", kb_id, exc)

    logger.info("[kb-sync] polling finished for kb_id=%s", kb_id)


async def run_kb_ingestion_background(
    kb_id: str,
    file_path: str,
    user_id: str,
    tenant_id: str,
    chunk_size: int,
    chunk_overlap: int,
    embedding_model: str,
    user_email: Optional[str],
    enable_graph: bool,
    llm_config_id: Optional[str],
) -> None:
    """
    Entry point for FastAPI BackgroundTasks (local Haystack pipeline path).
    Only called when CORTEX_KB_URL is not configured.
    """
    exists = os.path.isfile(file_path) if file_path else False
    logger.info(
        "[kb-ingest] background task started kb_id=%s file=%s exists=%s chunk=%s/%s model=%s",
        kb_id, file_path, exists, chunk_size, chunk_overlap, embedding_model,
    )
    try:
        async with AsyncSessionLocal() as session:
            llm_config = None
            if llm_config_id:
                res = await session.execute(
                    select(models.LLMConfiguration).where(
                        models.LLMConfiguration.id == llm_config_id,
                        models.LLMConfiguration.tenant_id == tenant_id,
                    )
                )
                llm_config = res.scalars().first()
            else:
                res = await session.execute(
                    select(models.LLMConfiguration).where(
                        models.LLMConfiguration.tenant_id == tenant_id
                    )
                )
                llm_config = res.scalars().first()

            if not llm_config and enable_graph:
                enable_graph = False

            svc = KBService(KBRepository(session))
            await svc.process_kb(
                kb_id, file_path, user_id, tenant_id,
                chunk_size, chunk_overlap, llm_config,
                embedding_model, user_email, enable_graph,
            )
        logger.info("[kb-ingest] background task finished kb_id=%s", kb_id)
    except Exception:
        logger.exception("[kb-ingest] background task crashed kb_id=%s", kb_id)
        raise


# ── KBService ─────────────────────────────────────────────────────────────────

class KBService:
    def __init__(self, kb_repo: KBRepository):
        self.kb_repo = kb_repo

    async def create_kb_record(
        self,
        user_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        embedding_model: str | None = None,
        tenant_id: str | None = None,
        enable_graph: bool = False,
        parsing_strategy: str = "fast",
    ):
        """Create initial KB record (status: queued)."""
        model = embedding_model or settings.OLLAMA_MODEL
        return await self.kb_repo.create(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=model,
            status="queued",
            tenant_id=tenant_id,
            parsing_strategy=parsing_strategy,
        )

    # ── Upload via Cortex KB service ──────────────────────────────────────────

    async def ingest_via_kb_service(
        self,
        kb_id: str,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        tenant_id: Optional[str] = None,
        parsing_strategy: str = "fast",
    ) -> bool:
        """
        Upload file to external Cortex KB service, store document_id in
        knowledge_bases.external_doc_id, then spawn a background polling
        loop to keep kb.status in sync.

        Returns True on success, False on error.
        """
        try:
            api_key = await _get_kb_api_key(tenant_id)
            resp = await kb_client.kb_upload(file_bytes, filename, mime_type, api_key=api_key,
                                              parsing_strategy=parsing_strategy)
            external_doc_id = resp.get("document_id")
            if not external_doc_id:
                logger.error("[kb-ext] upload returned no document_id for kb_id=%s", kb_id)
                await self.kb_repo.update_status(kb_id, "failed")
                return False

            kb_status = resp.get("status", "queued")

            # Already indexed — mark completed immediately, no polling needed.
            if kb_status == "indexed":
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(models.KnowledgeBase)
                        .where(models.KnowledgeBase.id == kb_id)
                        .values(external_doc_id=external_doc_id, status="completed")
                    )
                    await session.commit()
                logger.info("[kb-ext] kb_id=%s already indexed — marked completed", kb_id)
                return True

            # Pending or reprocessing — persist and start polling.
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(models.KnowledgeBase)
                    .where(models.KnowledgeBase.id == kb_id)
                    .values(external_doc_id=external_doc_id, status="queued")
                )
                await session.commit()

            logger.info("[kb-ext] kb_id=%s uploaded → external_doc_id=%s status=%s",
                        kb_id, external_doc_id, kb_status)

            # Fire-and-forget status sync loop
            asyncio.create_task(_sync_kb_status_loop(kb_id, external_doc_id, tenant_id=tenant_id))
            return True

        except Exception as exc:
            logger.error("[kb-ext] ingest_via_kb_service failed kb_id=%s: %s", kb_id, exc)
            await self.kb_repo.update_status(kb_id, "failed")
            return False

    # ── Local Haystack pipeline (fallback) ────────────────────────────────────

    async def process_kb(
        self,
        kb_id: str,
        file_path: str,
        user_id: str,
        tenant_id: str,
        chunk_size: int,
        chunk_overlap: int,
        llm_config,
        embedding_model: str,
        user_email: str | None = None,
        enable_graph: bool = False,
    ):
        """Local pipeline: Unstructured → Haystack → Ollama → Qdrant."""
        try:
            kb_row = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id)
            if not kb_row:
                logger.error("[kb-ingest] process_kb: KB %s not found", kb_id)
                return

            parsing_strategy = kb_row.parsing_strategy or "fast"
            logger.info(
                "[kb-ingest] process_kb begin kb_id=%s filename=%s strategy=%s",
                kb_id, getattr(kb_row, "filename", ""), parsing_strategy,
            )

            async def update_status_callback(status: str) -> None:
                await self.kb_repo.update_status(kb_id, status)

            try:
                result = await rag_service.process_document(
                    file_path=file_path,
                    kb_id=kb_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    llm_config=llm_config,
                    embedding_model=embedding_model,
                    on_progress=update_status_callback,
                    parsing_strategy=parsing_strategy,
                )

                if enable_graph and settings.ENABLE_GRAPH:
                    chunk_texts = result.get("chunk_texts") or []
                    try:
                        await neo4j_service.process_graph(kb_id, tenant_id, chunk_texts, llm_config)
                    except Exception as graph_err:
                        logger.error("Graph processing failed (non-blocking): %s", graph_err)

                await self.kb_repo.update_status(kb_id, "completed")
                logger.info("[kb-ingest] kb_id=%s completed chunks=%s", kb_id, result.get("chunks"))

            except Exception as e:
                logger.error("[kb-ingest] kb_id=%s RAG pipeline failed: %s\n%s",
                             kb_id, e, traceback.format_exc())
                await self.kb_repo.update_status(kb_id, "failed")

        except Exception as e:
            logger.error("[kb-ingest] kb_id=%s outer failure: %s\n%s",
                         kb_id, e, traceback.format_exc())
            try:
                await self.kb_repo.update_status(kb_id, "failed")
            except Exception as inner:
                logger.error("[kb-ingest] kb_id=%s could not set failed: %s", kb_id, inner)

    # ── Reprocess ─────────────────────────────────────────────────────────────

    async def reprocess_kb(self, kb_id: str, tenant_id: str) -> dict:
        """Re-trigger ingestion for a failed or stuck KB document."""
        async with AsyncSessionLocal() as session:
            kb = (await session.execute(
                select(models.KnowledgeBase).where(
                    models.KnowledgeBase.id == kb_id,
                    models.KnowledgeBase.tenant_id == tenant_id,
                )
            )).scalars().first()

            if not kb:
                return {"success": False, "message": "Document not found"}

        # Route through cortex-kb if configured and external_doc_id exists
        if kb_client.is_configured() and kb.external_doc_id:
            api_key = await _get_kb_api_key(tenant_id)
            strategy = kb.parsing_strategy or "fast"
            ok = await kb_client.kb_reprocess(kb.external_doc_id, api_key=api_key,
                                               parsing_strategy=strategy)
            if ok:
                await self.kb_repo.update_status(kb_id, "queued")
                # Restart status polling loop
                asyncio.create_task(_sync_kb_status_loop(kb_id, kb.external_doc_id, tenant_id=tenant_id))
                logger.info("[kb-reprocess] queued kb_id=%s external=%s", kb_id, kb.external_doc_id)
                return {"success": True, "message": "Reprocessing queued"}
            return {"success": False, "message": "Failed to trigger reprocess on KB service"}

        return {"success": False, "message": "No external document ID — re-upload the file"}

    # ── Status ────────────────────────────────────────────────────────────────

    async def get_status(
        self,
        kb_id: str,
        user_id: str,
        tenant_id: str,
        user_email: str | None = None,
    ) -> Dict[str, Any] | None:
        kb = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id=tenant_id)
        if not kb:
            return None

        if kb.external_doc_id and kb_client.is_configured():
            try:
                api_key = await _get_kb_api_key(tenant_id)
                data = await kb_client.kb_get_status(kb.external_doc_id, api_key=api_key)
                if data:
                    overall = data.get("overall_status", "")
                    stages = data.get("stages", {})
                    mapped = kb_client.map_kb_status(overall, stages)
                    # Keep local DB in sync when we check status
                    if mapped != kb.status:
                        await self.kb_repo.update_status(kb_id, mapped)
                    return {
                        "status": mapped,
                        "progress_pct": data.get("progress_pct", 0),
                        "stages": stages,
                        "external_doc_id": kb.external_doc_id,
                    }
            except Exception as exc:
                logger.warning("[kb-status] live check failed for %s: %s", kb.external_doc_id, exc)

        return {"status": kb.status}

    # ── List ──────────────────────────────────────────────────────────────────

    async def get_all(
        self,
        user_id: str,
        tenant_id: str,
        user_email: str | None = None,
        is_admin: bool = False,
    ):
        return await self.kb_repo.get_all(user_id, tenant_id, is_admin=is_admin)

    # ── Query (single KB) ─────────────────────────────────────────────────────

    async def query(
        self,
        kb_id: str,
        user_id: str,
        tenant_id: str,
        query_text: str,
        llm_config,
        user_email: str | None = None,
        is_admin: bool = False,
    ):
        kb = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id, is_admin=is_admin)
        if not kb:
            return {"success": False, "message": "KB not found"}

        if kb.status != "completed":
            return {"success": False, "message": f"KB not ready (status: {kb.status})"}

        # ── External KB service path ──────────────────────────────
        if kb.external_doc_id and kb_client.is_configured():
            api_key = await _get_kb_api_key(tenant_id)
            results = await kb_client.kb_search(
                query=query_text,
                document_id=kb.external_doc_id,
                top_k=10,
                mode="hybrid",
                api_key=api_key,
            )
            # Normalise to cortex-ai result shape
            normalised = [
                {
                    "content": r.get("text", ""),
                    "score": r.get("score", 0.0),
                    "metadata": {
                        "kb_id": kb_id,
                        "source": r.get("filename", kb.filename),
                        "document_id": r.get("document_id", ""),
                        "chunk_index": r.get("chunk_index"),
                    },
                }
                for r in results
            ]
            return {"success": True, "data": normalised}

        # ── Local Haystack path ───────────────────────────────────
        filters = {"kb_id": kb_id}
        results = await rag_service.search(
            query_text, filters, llm_config, embedding_model=kb.embedding_model,
        )
        return {"success": True, "data": results}

    # ── Query (multiple KBs — used by agent chat) ─────────────────────────────

    async def query_multiple(
        self,
        kb_ids: List[str],
        query_text: str,
        llm_config,
        embedding_model: str,
        user_email: str | None = None,
    ):
        if not kb_ids:
            return {"success": True, "data": []}

        # Fetch all KB records to see which have external_doc_id
        async with AsyncSessionLocal() as session:
            rows = (await session.execute(
                select(models.KnowledgeBase).where(
                    models.KnowledgeBase.id.in_(kb_ids)
                )
            )).scalars().all()

        external_ids = [r.external_doc_id for r in rows if r.external_doc_id]
        local_kb_ids = [r.id for r in rows if not r.external_doc_id]

        all_results: List[Dict[str, Any]] = []

        # ── External KB service path ──────────────────────────────
        if external_ids and kb_client.is_configured():
            # Get tenant's KB API key from any KB row (all share same tenant)
            first_tenant_id = next((r.tenant_id for r in rows if r.external_doc_id), None)
            api_key = await _get_kb_api_key(first_tenant_id)
            ext_results = await kb_client.kb_search_multi(
                query=query_text,
                document_ids=external_ids,
                top_k=10,
                mode="hybrid",
                api_key=api_key,
            )
            # Build kb_id lookup by external_doc_id
            ext_id_to_kb_id = {r.external_doc_id: r.id for r in rows if r.external_doc_id}
            for r in ext_results:
                kb_id = ext_id_to_kb_id.get(r.get("document_id", ""), "")
                all_results.append({
                    "content": r.get("text", ""),
                    "score": r.get("score", 0.0),
                    "metadata": {
                        "kb_id": kb_id,
                        "source": r.get("filename", ""),
                        "document_id": r.get("document_id", ""),
                        "chunk_index": r.get("chunk_index"),
                    },
                })

        # ── Local Haystack path (legacy records) ──────────────────
        if local_kb_ids:
            filters = {"kb_id": {"$in": local_kb_ids}}
            local_results = await rag_service.search(
                query_text, filters, llm_config, embedding_model=embedding_model
            )
            all_results.extend(local_results)

        # Sort by score, return top 10
        all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return {"success": True, "data": all_results[:10]}

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete(
        self,
        kb_id: str,
        user_id: str,
        tenant_id: str,
        user_email: str | None = None,
    ) -> Dict[str, Any]:
        kb = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id=tenant_id)
        if not kb:
            return {"success": False, "message": "Not found"}

        # ── External KB service path ──────────────────────────────
        if kb.external_doc_id and kb_client.is_configured():
            api_key = await _get_kb_api_key(tenant_id)
            deleted = await kb_client.kb_delete(kb.external_doc_id, api_key=api_key)
            if not deleted:
                logger.warning(
                    "[kb-delete] KB service delete failed for %s; continuing local cleanup",
                    kb.external_doc_id,
                )
        else:
            # ── Local Haystack path ───────────────────────────────
            vector_deleted = await rag_service.delete_kb(kb_id)
            if kb.status == "completed" and not vector_deleted:
                return {
                    "success": False,
                    "message": (
                        "Could not reach the vector database (Qdrant). "
                        "Fix QDRANT_URL and retry."
                    ),
                }
            if not vector_deleted:
                logger.warning(
                    "delete_kb: Qdrant cleanup failed for kb_id=%s status=%s; proceeding",
                    kb_id, kb.status,
                )

        if settings.ENABLE_GRAPH:
            await neo4j_service.delete_graph_for_kb(kb_id, tenant_id)

        # Clean up local file (may not exist for external-only uploads)
        if kb.file_path and os.path.exists(kb.file_path):
            try:
                os.remove(kb.file_path)
            except OSError:
                pass

        await self.kb_repo.delete(kb_id, user_id)
        return {"success": True, "message": f"Deleted {kb.filename}"}

    # ── Share ─────────────────────────────────────────────────────────────────

    async def share_kb(
        self,
        kb_id: str,
        owner_id: str,
        target_user_id: str,
        tenant_id: str,
        role: str = "viewer",
    ) -> Dict[str, Any]:
        kb = await self.kb_repo.get_by_id(kb_id, owner_id, tenant_id=tenant_id)
        if not kb:
            return {"success": False, "message": "KB not found or access denied"}
        if kb.user_id != owner_id:
            return {"success": False, "message": "Only the owner can share the KB"}
        try:
            await self.kb_repo.add_member(kb_id, target_user_id, role)
            return {"success": True, "message": "KB shared successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to share: {str(e)}"}

    async def unshare_kb(
        self,
        kb_id: str,
        owner_id: str,
        target_user_id: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        kb = await self.kb_repo.get_by_id(kb_id, owner_id, tenant_id=tenant_id)
        if not kb:
            return {"success": False, "message": "KB not found or access denied"}
        if kb.user_id != owner_id:
            return {"success": False, "message": "Only the owner can manage sharing"}
        success = await self.kb_repo.remove_member(kb_id, target_user_id)
        if success:
            return {"success": True, "message": "KB unshared successfully"}
        return {"success": False, "message": "User was not a member"}
