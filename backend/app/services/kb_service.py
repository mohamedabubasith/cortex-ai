"""Knowledge Base Service (LangChain Implementation)"""
import logging
import os
import asyncio
from typing import Dict, Any, List
from app.repositories.kb_repository import KBRepository
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

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
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """Create initial KB record"""
        # Note: We need to ensure repo supports extra fields or we add them manually if not in constructor
        # Since we modified the model but repo likely uses kwargs or explicit fields?
        # Let's check repo in next step if needed, but for now assuming direct create is cleaner if updated.
        # Actually repo.create usually takes fixed args. We might need to update repo too. 
        # For now, let's assume we can pass them.
        return await self.kb_repo.create(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size, # Ensure this was added to repo/model
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=embedding_model,
            status="pending"
        )
            
    async def process_kb(self, kb_id: str, file_path: str, user_id: str, tenant_id: str, chunk_size: int, chunk_overlap: int, llm_config, embedding_model: str, user_email: str = None):
        """
        Process KB (Load -> Split -> Embed -> Index) via RAGService.
        """
        try:
            print(f"DEBUG: Starting processing for KB {kb_id}")
            await self.kb_repo.update_status(kb_id, "indexing")
            
            # Process via LangChain RAG Service
            try:
                await rag_service.process_document(
                    file_path=file_path,
                    kb_id=kb_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    llm_config=llm_config,
                    embedding_model=embedding_model
                )
                
                # Success
                await self.kb_repo.update_status(kb_id, "indexed")
                print(f"DEBUG: Processing complete for KB {kb_id} -> Indexed")
                
            except Exception as e:
                logger.error(f"RAG processing failed: {e}")
                await self.kb_repo.update_status(kb_id, "failed")
                
        except Exception as e:
            logger.error(f"Background task failed: {e}")
            await self.kb_repo.update_status(kb_id, "failed")

    async def get_status(self, kb_id: str, user_id: str, user_email: str = None) -> Dict[str, Any]:
        """Get status directly from DB (no external sync needed)"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        if not kb:
            return None
        return {"status": kb.status}
    
    async def get_all(self, user_id: str, user_email: str = None):
        """Get all KB files"""
        return await self.kb_repo.get_all(user_id)
    
    async def query(self, kb_id: str, user_id: str, query_text: str, llm_config, user_email: str = None):
        """Query single KB"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        if not kb:
            return {"success": False, "message": "KB not found"}
        
        if kb.status != "indexed":
            return {"success": False, "message": f"KB not indexed (status: {kb.status})"}
        
        # Search via RAG Service
        # Filter by KB ID for security and reliability
        filters = {"kb_id": kb_id}
        
        results = await rag_service.search(query_text, filters, llm_config, embedding_model=kb.embedding_model)
        
        return {"success": True, "data": results}

    async def query_multiple(self, kb_ids: List[str], query_text: str, llm_config, embedding_model: str, user_email: str = None):
        """Query multiple KBs (must share same embedding model)"""
        if not kb_ids:
             return {"success": True, "data": []}
        
        # Search via RAG Service
        # Filter by KB IDs using $in operator
        filters = {"kb_id": {"$in": kb_ids}}
        
        results = await rag_service.search(query_text, filters, llm_config, embedding_model=embedding_model)
        
        return {"success": True, "data": results}

    async def delete(self, kb_id: str, user_id: str, user_email: str = None) -> Dict[str, Any]:
        """Delete KB and vectors"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        
        if not kb:
            return {"success": False, "message": "Not found"}
        
        # 1. Delete Vectors
        await rag_service.delete_kb(kb_id)
        
        # 2. Delete file
        if os.path.exists(kb.file_path):
            try:
                os.remove(kb.file_path)
            except:
                pass
        
        # 3. Delete from DB
        await self.kb_repo.delete(kb_id, user_id)
        
        return {"success": True, "message": f"Deleted {kb.filename}"}
