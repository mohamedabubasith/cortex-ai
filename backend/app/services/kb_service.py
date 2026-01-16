"""Knowledge Base Service"""
import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
from app.repositories.kb_repository import KBRepository
from app.services.langchain_service import langchain_service
from app.services.access_control_service import AccessControlService
from app.models.models import User

logger = logging.getLogger(__name__)

class KBService:
    def __init__(self, kb_repo: KBRepository, access_service: AccessControlService):
        self.kb_repo = kb_repo
        self.access_service = access_service
    
    async def create_kb_record(
        self,
        user: User,
        tenant_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int
    ):
        """Create initial KB record"""
        return await self.kb_repo.create_kb(
            user_id=user.id,
            tenant_id=tenant_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            status="pending"
        )

    async def process_kb(self, kb_id: str, file_path: str, tenant_id: str):
        """Process KB with clear status progression: processing → indexing → ready"""
        try:
            # Stage 1: Processing (parsing document)
            await self.kb_repo.update_status(kb_id, "processing")
            logger.info(f"KB {kb_id}: Stage 1 - Processing document")
            
            # Run parsing in thread (CPU bound)
            docs = await asyncio.to_thread(langchain_service.parse_file, file_path)
            
            # Stage 2: Indexing (creating embeddings and vector index)
            await self.kb_repo.update_status(kb_id, "indexing")
            logger.info(f"KB {kb_id}: Stage 2 - Indexing (creating embeddings)")
            
            # Run indexing in thread (CPU bound)
            result = await asyncio.to_thread(
                langchain_service.index_documents,
                docs=docs,
                kb_id=kb_id,
                tenant_id=tenant_id,
                file_path=file_path
            )
            
            if result["success"]:
                # Stage 3: Ready (available for queries)
                await self.kb_repo.update_status(kb_id, "ready")
                logger.info(f"KB {kb_id}: Stage 3 - Ready for queries")
            else:
                logger.error(f"KB {kb_id}: Ingestion failed - {result.get('message')}")
                await self.kb_repo.update_status(kb_id, "failed")
                
        except Exception as e:
            logger.error(f"KB {kb_id}: Background processing failed - {e}")
            await self.kb_repo.update_status(kb_id, "failed")

    async def get_status(self, kb_id: str, user: User, tenant_id: str) -> Dict[str, Any]:
        """Get KB status (from DB)"""
        if not await self.access_service.has_access(user, kb_id, "knowledge_base", "viewer", tenant_id):
            return None
            
        kb = await self.kb_repo.get(kb_id, user=user, tenant_id=tenant_id)
        if not kb:
            return None
        return {"status": kb.status}
    
    async def get_all(self, user: User, tenant_id: str):
        """Get all KB files accessible to the user in this tenant"""
        try:
            logger.info(f"Fetching all KBs for user {user.id} in tenant {tenant_id}")
            result = await self.kb_repo.get_all(user=user, tenant_id=tenant_id)
            logger.info(f"Found {len(result)} KBs")
            return result
        except Exception as e:
            logger.error(f"Error fetching KBs: {e}", exc_info=True)
            raise e
    
    async def query(self, kb_id: str, user: User, tenant_id: str, query_text: str, llm_config: Optional[Any] = None):
        """
        Query single KB.
        If llm_config is provided, the query is reformulated using the LLM for better retrieval.
        """
        if not await self.access_service.has_access(user, kb_id, "knowledge_base", "viewer", tenant_id):
            return {"success": False, "message": "Access Denied"}

        kb = await self.kb_repo.get(kb_id, user=user, tenant_id=tenant_id)
        if not kb:
            return {"success": False, "message": "KB not found"}
        
        if kb.status not in ["ready", "indexed"]:
            return {"success": False, "message": f"KB not ready (status: {kb.status})"}
        
        try:
            actual_query = query_text
            reformulated = False
            
            # Smart Query Reformulation
            if llm_config:
                from app.services.llm_service import llm_service
                actual_query = await llm_service.reformulate_query(query_text, llm_config)
                reformulated = actual_query != query_text
            
            results = await langchain_service.query(
                query_text=actual_query,
                tenant_id=tenant_id,
                kb_ids=[kb_id]
            )
            return {
                "success": True, 
                "results": results, 
                "meta": {
                    "original_query": query_text,
                    "actual_query": actual_query,
                    "reformulated": reformulated
                }
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def delete(self, kb_id: str, user: User, tenant_id: str) -> Dict[str, Any]:
        """Delete KB - Requires owner or admin access"""
        if not await self.access_service.has_access(user, kb_id, "knowledge_base", "admin", tenant_id):
            return {"success": False, "message": "Access Denied"}
            
        kb = await self.kb_repo.get(kb_id, user=user, tenant_id=tenant_id)
        if not kb:
            return {"success": False, "message": "Not found"}
        
        # Delete from Vector Store
        await langchain_service.delete_kb(kb_id, tenant_id)
        
        # Delete file
        if os.path.exists(kb.file_path):
            try:
                os.remove(kb.file_path)
            except OSError:
                pass
        
        # Delete from DB
        await self.kb_repo.delete(kb)
        
        return {"success": True, "message": f"Deleted {kb.filename}"}
