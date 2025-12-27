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
    
    async def create_kb_record(
        self,
        user_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int
    ):
        """Create initial KB record"""
        return await self.kb_repo.create(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            status="pending"
        )

    async def process_kb(self, kb_id: str, file_path: str, llm_config, user_email: str = None):
        """Process KB in background (add to Cognee and cognify)"""
        try:
            if llm_config:
                dataset_name = f"doc_{kb_id}"
                
                print(f"DEBUG process_kb: Processing KB {kb_id} for user {user_email}")
                
                # Upload to Cognee (fast) - pass user_email for multi-tenancy
                upload_result = await cognee_service.add_document(file_path, dataset_name, llm_config, user_email=user_email)
                
                if upload_result["success"]:
                    # Update to processing
                    await self.kb_repo.update_status(kb_id, "processing")
                    
                    # Trigger Cognify - pass user_email for multi-tenancy
                    try:
                        await cognee_service.cognify_dataset(dataset_name, llm_config, user_email=user_email)
                        # We stay in 'processing' state. 
                        # get_all() will sync status when it completes.
                    except Exception as e:
                        logger.error(f"Cognify trigger failed: {e}")
                        await self.kb_repo.update_status(kb_id, "failed")
                else:
                    await self.kb_repo.update_status(kb_id, "failed")
        except Exception as e:
            logger.error(f"Background processing failed: {e}")
            await self.kb_repo.update_status(kb_id, "failed")

    async def _sync_status(self, kb, user_email: str = None):
        """Sync DB status with Cognee status"""
        if kb.status in ["processing", "pending"]:
            dataset_name = f"doc_{kb.id}"
            status_info = await cognee_service.get_status(dataset_name, user_email = user_email)
            cognee_status = status_info.get("status")
            
            print(f"DEBUG: Syncing status for {kb.id}. Cognee returned: {status_info}")
            print(f"DEBUG: Mapped status: {cognee_status}")
            
            if cognee_status == "indexed":
                print(f"DEBUG: Updating DB status to indexed for {kb.id}")
                await self.kb_repo.update_status(kb.id, "indexed")
                kb.status = "indexed"
            elif cognee_status == "failed":
                print(f"DEBUG: Updating DB status to failed for {kb.id}")
                await self.kb_repo.update_status(kb.id, "failed")
                kb.status = "failed"
            # If still processing/initiated, keep as is

    async def get_status(self, kb_id: str, user_id: str, user_email: str = None) -> Dict[str, Any]:
        """Get KB status with Cognee pipeline status"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        
        if not kb:
            return None
        
        # Sync status
        await self._sync_status(kb, user_email = user_email)
        
        dataset_name = f"doc_{kb.id}"
        cognee_status = await cognee_service.get_status(dataset_name, user_email = user_email)
        
        # Simplified response as requested
        return {
            "status": cognee_status.get("status")
        }
    
    async def get_all(self, user_id: str, user_email: str = None):
        """Get all KB files and sync status"""
        kbs = await self.kb_repo.get_all(user_id)
        
        # Sync status for processing items
        for kb in kbs:
            await self._sync_status(kb, user_email = user_email)
            
        return kbs
    
    async def query(self, kb_id: str, user_id: str, query_text: str, llm_config, user_email: str = None):
        """Query single KB"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        
        if not kb:
            return {"success": False, "message": "KB not found"}
        
        # Sync status before checking
        await self._sync_status(kb)
        
        if kb.status != "indexed":
            return {"success": False, "message": f"KB not indexed (status: {kb.status})"}
        
        dataset_name = f"doc_{kb.id}"
        return await cognee_service.search(query_text, [dataset_name], llm_config, user_email=user_email)

    async def query_datasets(self, dataset_names: list[str], query_text: str, llm_config, user_email: str = None):
        """Query multiple datasets directly"""
        return await cognee_service.search(query_text, dataset_names, llm_config, user_email=user_email)
    
    async def delete(self, kb_id: str, user_id: str, user_email: str = None) -> Dict[str, Any]:
        """Delete KB"""
        kb = await self.kb_repo.get_by_id(kb_id, user_id)
        
        if not kb:
            return {"success": False, "message": "Not found"}
        
        # Delete from Cognee
        dataset_name = f"doc_{kb.id}"
        await cognee_service.delete_dataset(dataset_name, user_email = user_email)
        
        # Delete file
        if os.path.exists(kb.file_path):
            os.remove(kb.file_path)
        
        # Delete from DB
        await self.kb_repo.delete(kb_id, user_id)
        
        return {"success": True, "message": f"Deleted {kb.filename}"}
