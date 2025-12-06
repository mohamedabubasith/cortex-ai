"""Knowledge Base Service"""
import logging
import os
import asyncio
from typing import Dict, Any
from app.repositories.kb_repository import KBRepository
from app.services.cognee_service import cognee_service

logger = logging.getLogger(__name__)

class KBService:
    def __init__(self, kb_repo: KBRepository):
        self.kb_repo = kb_repo
    
    async def upload_and_index(
        self,
        user_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        llm_config = None
    ) -> Dict[str, Any]:
        """Upload file and start background indexing"""
        
        # Create KB record
        kb = await self.kb_repo.create(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            status="pending"
        )
        
        if llm_config:
            dataset_name = f"doc_{kb.id}"
            
            # Upload to Cognee (fast)
            upload_result = await cognee_service.upload_file(file_path, dataset_name)
            
            if upload_result["success"]:
                # Update to processing
                await self.kb_repo.update_status(kb.id, "processing")
                
                # Start background indexing
                async def background_index():
                    try:
                        await cognee_service.index_dataset(llm_config, dataset_name)
                        await self.kb_repo.update_status(kb.id, "indexed")
                    except Exception as e:
                        logger.error(f"Indexing failed: {e}")
                        await self.kb_repo.update_status(kb.id, "failed")
                
                task = asyncio.create_task(background_index())
                cognee_service.processing_tasks[dataset_name] = task
            else:
                await self.kb_repo.update_status(kb.id, "failed")
        
        return kb
    
    async def get_status(self, kb_id: str, user_id: str) -> Dict[str, Any]:
        """Get KB status with Cognee pipeline status"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        
        if not kb:
            return None
        
        dataset_name = f"doc_{kb.id}"
        cognee_status = await cognee_service.get_status(dataset_name)
        
        return {
            "id": kb.id,
            "filename": kb.filename,
            "db_status": kb.status,
            "cognee_status": cognee_status.get("status"),
            "cognee_details": cognee_status.get("details"),
            "created_at": kb.created_at
        }
    
    async def get_all(self, user_id: str):
        """Get all KB files"""
        return await self.kb_repo.get_all(user_id)
    
    async def query(self, kb_id: str, user_id: str, query_text: str, llm_config):
        """Query KB"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        
        if not kb:
            return {"success": False, "message": "KB not found"}
        
        if kb.status != "indexed":
            return {"success": False, "message": f"KB not indexed (status: {kb.status})"}
        
        dataset_name = f"doc_{kb.id}"
        return await cognee_service.query(llm_config, query_text, dataset_name)
    
    async def delete(self, kb_id: str, user_id: str) -> Dict[str, Any]:
        """Delete KB"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        
        if not kb:
            return {"success": False, "message": "Not found"}
        
        # Delete from Cognee
        dataset_name = f"doc_{kb.id}"
        if kb.status == "indexed":
            await cognee_service.delete_dataset(dataset_name)
        
        # Delete file
        if os.path.exists(kb.file_path):
            os.remove(kb.file_path)
        
        # Delete from DB
        await self.kb_repo.delete(kb_id, user_id)
        
        return {"success": True, "message": f"Deleted {kb.filename}"}
