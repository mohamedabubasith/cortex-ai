"""Knowledge Base Service (Haystack + Unstructured + Ollama + Qdrant)."""
import logging
import os
import traceback
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from app.repositories.kb_repository import KBRepository
from app.services.rag_service import rag_service
from app.services.neo4j_service import neo4j_service
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models import models

logger = logging.getLogger(__name__)


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
    Entry point for FastAPI ``BackgroundTasks``.

    Opens a **new** async SQLAlchemy session. The request-scoped session used during
    ``/upload`` is closed after the response; ingestion runs later and must not use it.
    """
    exists = os.path.isfile(file_path) if file_path else False
    logger.info(
        "[kb-ingest] background task started kb_id=%s file=%s exists=%s chunk=%s/%s model=%s",
        kb_id,
        file_path,
        exists,
        chunk_size,
        chunk_overlap,
        embedding_model,
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

            logger.info(
                "[kb-ingest] DB session ready kb_id=%s llm_config_id=%s",
                kb_id,
                llm_config_id or "(tenant default or none)",
            )

            svc = KBService(KBRepository(session))
            await svc.process_kb(
                kb_id,
                file_path,
                user_id,
                tenant_id,
                chunk_size,
                chunk_overlap,
                llm_config,
                embedding_model,
                user_email,
                enable_graph,
            )
        logger.info("[kb-ingest] background task finished kb_id=%s", kb_id)
    except Exception:
        logger.exception("[kb-ingest] background task crashed kb_id=%s", kb_id)
        raise


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
        """Create initial KB record (queued for background ingestion)."""
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
        """Background: Unstructured → Haystack chunking → Ollama → Qdrant; optional Neo4j graph."""
        try:
            kb_row = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id)
            if not kb_row:
                logger.error("[kb-ingest] process_kb: KB %s not found for user", kb_id)
                return

            parsing_strategy = kb_row.parsing_strategy or "fast"
            on_disk = os.path.isfile(file_path) if file_path else False
            logger.info(
                "[kb-ingest] process_kb begin kb_id=%s filename=%s path=%s on_disk=%s strategy=%s",
                kb_id,
                getattr(kb_row, "filename", ""),
                file_path,
                on_disk,
                parsing_strategy,
            )

            async def update_status_callback(status: str) -> None:
                logger.info("[kb-ingest] kb_id=%s DB status -> %s", kb_id, status)
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

                chunk_texts = result.get("chunk_texts") or []

                if enable_graph and settings.ENABLE_GRAPH:
                    logger.info("Graph integration enabled for KB %s", kb_id)
                    try:
                        await neo4j_service.process_graph(kb_id, tenant_id, chunk_texts, llm_config)
                    except Exception as graph_err:
                        logger.error("Graph processing failed (non-blocking): %s", graph_err)

                await self.kb_repo.update_status(kb_id, "completed")
                logger.info(
                    "[kb-ingest] kb_id=%s ingestion completed chunks=%s",
                    kb_id,
                    result.get("chunks"),
                )

            except Exception as e:
                logger.error(
                    "[kb-ingest] kb_id=%s RAG pipeline failed: %s\n%s",
                    kb_id,
                    e,
                    traceback.format_exc(),
                )
                await self.kb_repo.update_status(kb_id, "failed")

        except Exception as e:
            logger.error(
                "[kb-ingest] kb_id=%s process_kb outer failure: %s\n%s",
                kb_id,
                e,
                traceback.format_exc(),
            )
            try:
                await self.kb_repo.update_status(kb_id, "failed")
            except Exception as inner:
                logger.error("[kb-ingest] kb_id=%s could not set failed status: %s", kb_id, inner)

    async def get_status(self, kb_id: str, user_id: str, tenant_id: str, user_email: str | None = None) -> Dict[str, Any] | None:
        kb = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id=tenant_id)
        if not kb:
            return None
        return {"status": kb.status}

    async def get_all(self, user_id: str, tenant_id: str, user_email: str | None = None, is_admin: bool = False):
        return await self.kb_repo.get_all(user_id, tenant_id, is_admin=is_admin)

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

        filters = {"kb_id": kb_id}
        results = await rag_service.search(
            query_text,
            filters,
            llm_config,
            embedding_model=kb.embedding_model,
        )
        return {"success": True, "data": results}

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

        filters = {"kb_id": {"$in": kb_ids}}
        results = await rag_service.search(query_text, filters, llm_config, embedding_model=embedding_model)
        return {"success": True, "data": results}

    async def delete(self, kb_id: str, user_id: str, tenant_id: str, user_email: str | None = None) -> Dict[str, Any]:
        kb = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id=tenant_id)

        if not kb:
            return {"success": False, "message": "Not found"}

        # Completed KBs have vectors in Qdrant; do not remove the DB row if Qdrant is unreachable
        # (avoids false "deleted" while points remain). Non-completed: best-effort vector cleanup.
        vector_deleted = await rag_service.delete_kb(kb_id)
        if kb.status == "completed" and not vector_deleted:
            return {
                "success": False,
                "message": (
                    "Could not reach the vector database (Qdrant), so vectors were not removed. "
                    "Fix QDRANT_URL (e.g. add :6333 for native Qdrant or :80 if behind HTTP), ensure "
                    "the service is running, then try again."
                ),
            }
        if not vector_deleted:
            logger.warning(
                "delete_kb: Qdrant cleanup failed for non-completed kb_id=%s status=%s; continuing with file/DB delete",
                kb_id,
                kb.status,
            )

        if settings.ENABLE_GRAPH:
            await neo4j_service.delete_graph_for_kb(kb_id, tenant_id)

        if os.path.exists(kb.file_path):
            try:
                os.remove(kb.file_path)
            except OSError:
                pass

        await self.kb_repo.delete(kb_id, user_id)

        return {"success": True, "message": f"Deleted {kb.filename}"}

    async def share_kb(self, kb_id: str, owner_id: str, target_user_id: str, tenant_id: str, role: str = "viewer") -> Dict[str, Any]:
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

    async def unshare_kb(self, kb_id: str, owner_id: str, target_user_id: str, tenant_id: str) -> Dict[str, Any]:
        kb = await self.kb_repo.get_by_id(kb_id, owner_id, tenant_id=tenant_id)
        if not kb:
            return {"success": False, "message": "KB not found or access denied"}

        if kb.user_id != owner_id:
            return {"success": False, "message": "Only the owner can manage sharing"}

        success = await self.kb_repo.remove_member(kb_id, target_user_id)
        if success:
            return {"success": True, "message": "KB unshared successfully"}
        return {"success": False, "message": "User was not a member"}
