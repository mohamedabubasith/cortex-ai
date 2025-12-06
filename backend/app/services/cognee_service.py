import cognee
import os
import asyncio
from typing import Optional, List, Dict, Any
from app.models import models
import logging

logger = logging.getLogger(__name__)

class CogneeService:
    def __init__(self):
        self.processing_status: Dict[str, str] = {}  # Track processing status by dataset_name
        
    def _configure_llm(self, llm_config: Optional[models.LLMConfiguration]):
        """Configure LLM environment variables for Cognee."""
        if llm_config:
            if llm_config.api_key:
                os.environ["OPENAI_API_KEY"] = llm_config.api_key
            if llm_config.base_url:
                os.environ["OPENAI_API_BASE"] = llm_config.base_url

    async def upload_and_index(
        self, 
        llm_config: Optional[models.LLMConfiguration], 
        file_path: str, 
        filename: str, 
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Uploads file to Cognee and triggers indexing with proper status tracking.
        
        Returns:
            dict: {"success": bool, "message": str, "status": str}
        """
        try:
            logger.info(f"Starting upload and index for {filename} in dataset {dataset_name}")
            
            # Set status to processing
            self.processing_status[dataset_name] = "processing"
            
            # Validate file exists
            if not os.path.exists(file_path):
                self.processing_status[dataset_name] = "failed"
                return {
                    "success": False,
                    "message": f"File not found: {file_path}",
                    "status": "failed"
                }
            
            # Configure LLM
            self._configure_llm(llm_config)
            
            # Add file to Cognee
            logger.info(f"Adding file {file_path} to Cognee dataset {dataset_name}")
            await cognee.add(file_path, dataset_name)
            
            # Trigger cognify (indexing)
            logger.info(f"Starting cognify for dataset {dataset_name}")
            await cognee.cognify(dataset_name)
            
            # Mark as completed
            self.processing_status[dataset_name] = "indexed"
            
            logger.info(f"Successfully indexed {filename} in dataset {dataset_name}")
            return {
                "success": True,
                "message": f"Successfully indexed {filename}",
                "status": "indexed"
            }
            
        except FileNotFoundError as e:
            logger.error(f"File not found error for {filename}: {e}")
            self.processing_status[dataset_name] = "failed"
            return {
                "success": False,
                "message": f"File not found: {str(e)}",
                "status": "failed"
            }
        except Exception as e:
            logger.error(f"Error indexing file {filename}: {e}", exc_info=True)
            self.processing_status[dataset_name] = "failed"
            return {
                "success": False,
                "message": f"Indexing failed: {str(e)}",
                "status": "failed"
            }

    async def get_processing_status(self, dataset_name: str) -> str:
        """
        Get the current processing status for a dataset.
        
        Returns:
            str: "pending" | "processing" | "indexed" | "failed"
        """
        return self.processing_status.get(dataset_name, "pending")

    async def query(
        self, 
        llm_config: Optional[models.LLMConfiguration], 
        query_text: str, 
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Queries the knowledge base for context.
        
        Returns:
            dict: {"success": bool, "context": str, "results": List[Any]}
        """
        try:
            logger.info(f"Querying dataset {dataset_name} with query: {query_text[:50]}...")
            
            # Check if dataset is indexed
            status = await self.get_processing_status(dataset_name)
            if status != "indexed":
                return {
                    "success": False,
                    "context": "",
                    "results": [],
                    "message": f"Dataset not ready. Current status: {status}"
                }
            
            # Configure LLM
            self._configure_llm(llm_config)

            # Search
            results = await cognee.search(query_text, dataset_name)
            
            if results and len(results) > 0:
                # Format results
                context_parts = []
                for r in results:
                    if hasattr(r, 'text'):
                        context_parts.append(r.text)
                    else:
                        context_parts.append(str(r))
                
                context = "\n\n".join(context_parts)
                
                logger.info(f"Found {len(results)} results for query in {dataset_name}")
                return {
                    "success": True,
                    "context": f"Context from Knowledge Base:\n{context}",
                    "results": results,
                    "count": len(results)
                }
            
            logger.info(f"No results found for query in {dataset_name}")
            return {
                "success": True,
                "context": "",
                "results": [],
                "count": 0,
                "message": "No relevant context found"
            }
            
        except Exception as e:
            logger.error(f"Error querying KB {dataset_name}: {e}", exc_info=True)
            return {
                "success": False,
                "context": "",
                "results": [],
                "message": f"Query failed: {str(e)}"
            }

    async def delete_dataset(
        self, 
        llm_config: Optional[models.LLMConfiguration], 
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Deletes the entire dataset from Cognee.
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            logger.info(f"Deleting dataset {dataset_name} from Cognee")
            
            # Configure LLM
            self._configure_llm(llm_config)
            
            # Delete dataset
            await cognee.prune.data(dataset_name)
            
            # Clear status
            if dataset_name in self.processing_status:
                del self.processing_status[dataset_name]
            
            logger.info(f"Successfully deleted dataset {dataset_name}")
            return {
                "success": True,
                "message": f"Successfully deleted dataset {dataset_name}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting dataset {dataset_name}: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Delete failed: {str(e)}"
            }

    async def reset_cognee(self) -> Dict[str, Any]:
        """
        Reset Cognee entirely (for testing/debugging).
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        try:
            logger.warning("Resetting entire Cognee instance")
            await cognee.prune.system()
            self.processing_status.clear()
            
            logger.info("Successfully reset Cognee")
            return {
                "success": True,
                "message": "Successfully reset Cognee"
            }
        except Exception as e:
            logger.error(f"Error resetting Cognee: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Reset failed: {str(e)}"
            }

cognee_service = CogneeService()
