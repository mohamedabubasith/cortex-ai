"""Cognee Service with Background Processing"""
import logging
import os
import asyncio
from typing import Dict, Any
import cognee

logger = logging.getLogger(__name__)

class CogneeService:
    def __init__(self):
        self.processing_tasks = {}  # Track background tasks
    
    def _configure_llm(self, llm_config):
        if llm_config:
            os.environ["LLM_API_KEY"] = llm_config.api_key
            if llm_config.base_url:
                os.environ["LLM_ENDPOINT"] = llm_config.base_url
            if llm_config.model:
                os.environ["LLM_MODEL"] = llm_config.model
    
    async def upload_file(self, file_path: str, dataset_name: str) -> Dict[str, Any]:
        """Upload only (fast)"""
        try:
            await cognee.add(file_path, dataset_name)
            return {"success": True, "message": "File uploaded"}
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return {"success": False, "message": str(e)}
    
    async def index_dataset(self, llm_config, dataset_name: str):
        """Index in background"""
        try:
            self._configure_llm(llm_config)
            await cognee.cognify(datasets=[dataset_name])
            logger.info(f"Indexing complete: {dataset_name}")
        except Exception as e:
            logger.error(f"Indexing error: {e}")
    
    async def get_status(self, dataset_name: str) -> Dict[str, Any]:
        """Get Cognee pipeline status"""
        try:
            # Check if dataset exists
            datasets = await cognee.datasets.get_datasets()
            dataset = next((d for d in datasets if d.name == dataset_name), None)
            
            if not dataset:
                return {"status": "not_found", "exists": False}
            
            # Get processing info
            status_info = await cognee.datasets.get_dataset_status(dataset_name)
            
            return {
                "status": status_info.get("status", "unknown"),
                "exists": True,
                "details": status_info
            }
        except Exception as e:
            logger.error(f"Status error: {e}")
            # Fallback: check if task is running
            if dataset_name in self.processing_tasks:
                task = self.processing_tasks[dataset_name]
                if not task.done():
                    return {"status": "processing", "exists": True}
                elif task.exception():
                    return {"status": "failed", "exists": True, "error": str(task.exception())}
                else:
                    return {"status": "indexed", "exists": True}
            return {"status": "unknown", "exists": False, "message": str(e)}
    
    async def query(self, llm_config, query_text: str, dataset_name: str = None) -> Dict[str, Any]:
        """Search documents"""
        try:
            self._configure_llm(llm_config)
            
            search_params = {"query_text": query_text}
            if dataset_name:
                search_params["datasets"] = [dataset_name]
            
            results = await cognee.search(cognee.SearchType.INSIGHTS, **search_params)
            context = "\n".join([str(r) for r in results]) if results else ""
            
            return {"success": True, "context": context, "count": len(results) if results else 0}
        except Exception as e:
            logger.error(f"Query error: {e}")
            return {"success": False, "message": str(e)}
    
    async def delete_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """Delete dataset"""
        try:
            await cognee.prune.prune_data(dataset_name)
            await cognee.prune.prune_system(dataset_name)
            return {"success": True, "message": f"Deleted {dataset_name}"}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"success": False, "message": str(e)}

cognee_service = CogneeService()
