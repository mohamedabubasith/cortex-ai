"""Knowledge Base Service (LangChain Implementation)"""
import logging
import os
import asyncio
import datetime
from typing import Dict, Any, List
from app.repositories.kb_repository import KBRepository
from app.services.rag_service import rag_service
from app.services.neo4j_service import neo4j_service
from app.core.config import settings

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
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        tenant_id: str = None,
        enable_graph: bool = False
    ):
        """Create initial KB record"""
        # Note: We don't store enable_graph in DB schema yet to avoid migrations, 
        # but we use it for immediate processing triggering.
        return await self.kb_repo.create(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size, 
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=embedding_model,
            status="pending",
            tenant_id=tenant_id
        )
            
    async def process_kb(self, kb_id: str, file_path: str, user_id: str, tenant_id: str, chunk_size: int, chunk_overlap: int, llm_config, embedding_model: str, user_email: str = None, enable_graph: bool = False):
        """
        Process KB (Load -> Split -> Embed -> Index) via RAGService.
        If enable_graph is True, also extracts and builds Knowledge Graph in Neo4j.
        """
        try:
            print(f"DEBUG: Starting processing for KB {kb_id}")
            await self.kb_repo.update_status(kb_id, "processing")
            
            # Process via LangChain RAG Service
            try:
                async def update_status_callback(status: str):
                    await self.kb_repo.update_status(kb_id, status)

                # 1. Vector Processing
                await rag_service.process_document(
                    file_path=file_path,
                    kb_id=kb_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    llm_config=llm_config,
                    embedding_model=embedding_model,
                    on_progress=update_status_callback
                )
                
                # 2. Graph Processing (Optional)
                if enable_graph and settings.ENABLE_GRAPH:
                    logger.info(f"Graph Integration Enabled for KB {kb_id}")
                    # We need to re-read/chunk here since rag_service doesn't return them currently
                    # Using langchain text splitters directly would be best, but manual works for broad chunks.
                    from langchain.text_splitter import RecursiveCharacterTextSplitter
                    from langchain_community.document_loaders import TextLoader, UnstructuredFileLoader
                    
                    # Quick loading logic (replicating simple part of RAG service for graph)
                    # For complex files, using the same loader instance would be better refactoring for later.
                    try:
                        loader = UnstructuredFileLoader(file_path)
                        documents = await asyncio.to_thread(loader.load)
                        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                        split_docs = text_splitter.split_documents(documents)
                        chunks = [doc.page_content for doc in split_docs]
                        
                        await neo4j_service.process_graph(kb_id, tenant_id, chunks, llm_config)
                    except Exception as graph_err:
                        logger.error(f"Graph processing failed (non-blocking for Vector): {graph_err}")
                        # We don't fail the whole index if graph fails, but logs will show it.

                # Success
                await self.kb_repo.update_status(kb_id, "indexed")
                print(f"DEBUG: Processing complete for KB {kb_id} -> Indexed")
                
            except Exception as e:
                import traceback
                error_msg = f"RAG processing failed: {e}\n{traceback.format_exc()}"
                logger.error(error_msg)
                await self.kb_repo.update_status(kb_id, "failed")
                
        except Exception as e:
            import traceback
            error_msg = f"Background task failed: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            
            await self.kb_repo.update_status(kb_id, "failed")

    async def get_status(self, kb_id: str, user_id: str, tenant_id: str, user_email: str = None) -> Dict[str, Any]:
        """Get status directly from DB (no external sync needed)"""
        # We assume regular user logic here, but status checks should be scoped to tenant too
        # Passing is_admin=False by default for status checks unless we want admins to see status of others' files?
        # Let's assume user checking status knows about the file.
        # Ideally, we should pass is_admin here too, but for now let's use default (Owner/Member)
        # But we MUST pass tenant_id.
        kb = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id=tenant_id)
        if not kb:
            return None
        return {"status": kb.status}
    
    async def get_all(self, user_id: str, tenant_id: str, user_email: str = None, is_admin: bool = False):
        """Get all KB files"""
        return await self.kb_repo.get_all(user_id, tenant_id, is_admin=is_admin)
    
    async def query(self, kb_id: str, user_id: str, tenant_id: str, query_text: str, llm_config, user_email: str = None, is_admin: bool = False):
        """Query single KB"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id, is_admin=is_admin)
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

    async def delete(self, kb_id: str, user_id: str, tenant_id: str, user_email: str = None) -> Dict[str, Any]:
        """Delete KB and vectors"""
        # Delete only possible by Owner (implied by default is_admin=False and user_id check)
        kb = await self.kb_repo.get_by_id(kb_id, user_id, tenant_id=tenant_id)
        
        if not kb:
            return {"success": False, "message": "Not found"}
        
        # 1. Delete Vectors
        await rag_service.delete_kb(kb_id)
        
        # 2. Delete Graph Data (Neo4j)
        if settings.ENABLE_GRAPH:
            await neo4j_service.delete_graph_for_kb(kb_id, tenant_id)
        
        # 3. Delete file
        if os.path.exists(kb.file_path):
            try:
                os.remove(kb.file_path)
            except:
                pass
        
        # 4. Delete from DB
        await self.kb_repo.delete(kb_id, user_id)
        
        return {"success": True, "message": f"Deleted {kb.filename}"}

    async def share_kb(self, kb_id: str, owner_id: str, target_user_id: str, tenant_id: str, role: str = "viewer") -> Dict[str, Any]:
        """Share KB with another user"""
        # 1. Verify Ownership
        # We fetch via repo.get_by_id but we must ensure CURRENT user is OWNER in CURRENT TENANT
        kb = await self.kb_repo.get_by_id(kb_id, owner_id, tenant_id=tenant_id)
        if not kb:
             return {"success": False, "message": "KB not found or access denied"}
        
        if kb.user_id != owner_id:
            return {"success": False, "message": "Only the owner can share the KB"}

        # 2. Add Member
        try:
            await self.kb_repo.add_member(kb_id, target_user_id, role)
            return {"success": True, "message": "KB shared successfully"}
        except Exception as e:
            # Likely unique constraint if already exists or logic error
            return {"success": False, "message": f"Failed to share: {str(e)}"}

    async def unshare_kb(self, kb_id: str, owner_id: str, target_user_id: str, tenant_id: str) -> Dict[str, Any]:
        """Unshare KB"""
        # 1. Verify Ownership
        kb = await self.kb_repo.get_by_id(kb_id, owner_id, tenant_id=tenant_id)
        if not kb:
             return {"success": False, "message": "KB not found or access denied"}
        
        if kb.user_id != owner_id:
            return {"success": False, "message": "Only the owner can manage sharing"}

        # 2. Remove Member
        success = await self.kb_repo.remove_member(kb_id, target_user_id)
        if success:
             return {"success": True, "message": "KB unshared successfully"}
        else:
             return {"success": False, "message": "User was not a member"}

