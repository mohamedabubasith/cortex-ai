"""Cognee Service with Background Processing"""
"""
Cognee Service
Handles integration with the Cognee library for knowledge graph and vector search.
"""
import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
import cognee
from cognee.api.v1.search import SearchType
from cognee.api.v1.search.search import search as cognee_search
from cognee.modules.users.methods import get_default_user
from cognee.infrastructure.databases.relational import get_relational_engine
from cognee.infrastructure.databases.relational.ModelBase import Base as CogneeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

class CogneeService:
    def __init__(self):
        self._configure_db()

    def _configure_db(self):
        """Configure Cognee to use the main Postgres DB"""
        try:
            # Enable Access Control globally for Cognee
            os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "true"
            
            db_url = settings.DATABASE_URL.replace("+asyncpg", "")
            
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            
            # Reconstruct URL for Cognee DB
            cognee_db_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/cognee_db"
            
            # Configure Relational DB (Postgres)
            cognee.config.set_relational_db_config({
                "db_provider": "postgres",
                "db_name": "cognee_db",
                "db_host": parsed.hostname,
                "db_port": str(parsed.port),
                "db_username": parsed.username,
                "db_password": parsed.password
            })
            
            # Configure Vector DB (PGVector)
            cognee.config.set_vector_db_provider("pgvector")
            cognee.config.set_vector_db_url(cognee_db_url)
            cognee.config.set_vector_db_config({
                "vector_db_provider": "pgvector",
                "vector_db_url": cognee_db_url
            })
            
            logger.info(f"Configured Cognee with PGVector at {cognee_db_url}")
        except Exception as e:
            logger.error(f"Failed to configure Cognee DB: {e}")

    async def initialize(self):
        """Initialize Cognee (create tables, etc.)"""
        try:
            self._configure_db()
            from cognee.modules.engine.operations.setup import setup
            logger.info("Running Cognee setup...")
            await setup()
            logger.info("Cognee setup complete.")
        except Exception as e:
            logger.error(f"Cognee setup failed: {e}")

    def _configure_llm(self, llm_config):
        """Configure LLM settings for Cognee"""
        if llm_config:
            cognee.config.set_llm_api_key(llm_config.api_key)
            # Also set env var for LiteLLM/OpenAI compatibility
            os.environ["OPENAI_API_KEY"] = llm_config.api_key
            
            cognee.config.set_llm_provider("openai") # Default to openai
            
            if llm_config.base_url:
                cognee.config.set_llm_endpoint(llm_config.base_url)
                # Set env vars for LiteLLM to use the custom endpoint for all operations (including embeddings)
                os.environ["OPENAI_API_BASE"] = llm_config.base_url
                os.environ["LITELLM_API_BASE"] = llm_config.base_url
            
            if llm_config.model:
                model = llm_config.model
                # Fix for litellm: if using custom endpoint with non-standard model name,
                # prefix with openai/ to force OpenAI protocol.
                if "/" in model and not model.startswith("openai/"):
                    model = f"openai/{model}"
                cognee.config.set_llm_model(model)

    async def _get_dataset_by_name(self, dataset_name: str) -> Optional[dict]:
        """Check if dataset exists"""
        try:
            datasets = await cognee.datasets.list_datasets()
            for dataset in datasets:
                if dataset.name == dataset_name:
                    return dataset
            return None
        except Exception as e:
            logger.error(f"Error checking dataset: {e}")
            return None
    
    async def add_document(self, file_path: str, dataset_name: str, llm_config, user_email: str = None) -> Dict[str, Any]:
        """
        Add a document to a specific dataset.
        Passes file path to Cognee.
        """
        self._configure_llm(llm_config)
        try:
            logger.info(f"Adding file {file_path} to dataset {dataset_name}")
            
            # Add data to Cognee (creates dataset if needed)
            await cognee.add(
                data=file_path,
                dataset_name=dataset_name,
            )
            
            return {"success": True, "message": "Document added successfully"}
        except Exception as e:
            logger.error(f"Error adding document to Cognee: {e}")
            return {"success": False, "message": str(e)}

    async def cognify_dataset(self, dataset_name: str, llm_config, user_email: str = None) -> Dict[str, Any]:
        """
        Run the cognify process on a specific dataset.
        """
        self._configure_llm(llm_config)
        try:
            logger.info(f"Cognifying dataset {dataset_name}")
            
            # Cognify
            await cognee.cognify(
                datasets=[dataset_name],
            )
            
            return {"success": True, "message": "Dataset cognify started"}
        except Exception as e:
            logger.error(f"Error cognifying dataset: {e}")
            raise e

    async def get_status(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get the status of a dataset using Cognee's pipeline status API.
        Handles PipelineRunStatus enum format.
        """
        try:
            dataset = await self._get_dataset_by_name(dataset_name)
            if not dataset:
                return {
                    "status": "not_found",
                    "message": f"Dataset '{dataset_name}' not found"
                }
            
            dataset_id = dataset.id
            
            # Get status from Cognee - returns dict keyed by dataset_id
            status_response = await cognee.datasets.get_status([dataset_id])
            
            # Extract status for this dataset
            raw_status = (
                status_response.get(dataset_id) or
                status_response.get(str(dataset_id)) or
                (list(status_response.values())[0] if len(status_response) == 1 else None)
            )
            
            if raw_status is None:
                return {
                    "status": "unknown",
                    "message": "Could not retrieve dataset status",
                    "details": status_response
                }
            
            # Extract status string from dict or enum
            if isinstance(raw_status, dict):
                cognee_status = raw_status.get("status", str(raw_status))
            else:
                cognee_status = str(raw_status)
            
            # Clean up enum representation: "PipelineRunStatus.COMPLETED" -> "COMPLETED"
            if "PipelineRunStatus." in cognee_status:
                cognee_status = cognee_status.split("PipelineRunStatus.")[-1]
            elif "." in cognee_status and cognee_status.count(".") == 1:
                # Handle any other enum formats like "Status.VALUE"
                cognee_status = cognee_status.split(".")[-1]
            
            # Normalize to uppercase for consistent mapping
            cognee_status = cognee_status.upper().strip()
            
            # Map Cognee/Pipeline status to user-friendly status
            status_map = {
                # PipelineRunStatus values
                "COMPLETED": "indexed",
                "RUNNING": "processing",
                "PENDING": "initiated",
                "FAILED": "failed",
                "ERRORED": "failed",
                "STARTED": "processing",
                "INITIATED": "initiated",
                
                # Dataset processing status values
                "DATASET_PROCESSING_COMPLETED": "indexed",
                "DATASET_PROCESSING_STARTED": "processing",
                "DATASET_PROCESSING_RUNNING": "processing",
                "DATASET_PROCESSING_INITIATED": "initiated",
                "DATASET_PROCESSING_ERRORED": "failed",
                "DATASET_PROCESSING_FAILED": "failed",
                
                # Additional states
                "QUEUED": "initiated",
                "SUCCESS": "indexed",
                "CANCELLED": "failed",
                "CANCELED": "failed",
            }
            
            # Get user-friendly status
            user_status = status_map.get(cognee_status)
            
            # Fallback: partial matching for robustness
            if not user_status:
                cognee_lower = cognee_status.lower()
                if "complet" in cognee_lower or "success" in cognee_lower:
                    user_status = "indexed"
                elif "run" in cognee_lower or "start" in cognee_lower or "process" in cognee_lower:
                    user_status = "processing"
                elif "init" in cognee_lower or "pend" in cognee_lower or "queue" in cognee_lower:
                    user_status = "initiated"
                elif "fail" in cognee_lower or "error" in cognee_lower or "cancel" in cognee_lower:
                    user_status = "failed"
                else:
                    user_status = cognee_lower
            
            logger.info(
                f"Status for '{dataset_name}': "
                f"raw={cognee_status} -> user={user_status}"
            )
            
            return {
                "status": user_status,
                "cognee_status": cognee_status,
                "is_ready": user_status == "indexed",
                "raw_response": status_response
            }
            
        except Exception as e:
            logger.error(f"Error fetching status for '{dataset_name}': {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }


    async def search(self, query_text: str, datasets: List[str], llm_config, user_email: str = None, search_type: str = "CHUNKS") -> Dict[str, Any]:
        """
        Search within specific datasets.
        """
        self._configure_llm(llm_config)
        try:
            logger.info(f"Searching datasets {datasets} with query: {query_text}")
            
            search_type_map = {
                "CHUNKS": SearchType.CHUNKS,
                "GRAPH_COMPLETION": SearchType.GRAPH_COMPLETION,
            }
            
            s_type = search_type_map.get(search_type, SearchType.CHUNKS)
            
            logger.info(f"Calling cognee_search with datasets={datasets}")
            
            # If only one dataset is provided, pass it as a string as requested
            search_datasets = datasets[0] if datasets and len(datasets) == 1 else datasets
            
            # Pass user parameter to Cognee for multi-tenancy
            results = await cognee_search(
                query_type=s_type,
                query_text=query_text,
                datasets=search_datasets,
            )

            # Log which datasets the results belong to
            if isinstance(results, list) and len(results) > 0:
                belongs_to_sets = set()
                for r in results:
                    if isinstance(r, dict):
                        belongs_to = r.get('belongs_to_set')
                        if belongs_to:
                            belongs_to_sets.add(belongs_to)
                logger.info(f"Search results belong to datasets: {belongs_to_sets}")
            
            return {"success": True, "data": results}
        except Exception as e:
            logger.error(f"Search error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}

    async def delete_dataset(self, dataset_name: str) -> Dict[str, Any]:
        """
        Delete a specific dataset.
        """
        try:
            logger.info(f"Deleting dataset {dataset_name}")
            
            dataset = await self._get_dataset_by_name(dataset_name)
            if dataset:
                dataset_id = dataset.id
                await cognee.prune.prune_data(dataset_name)
                # delete_dataset takes ID
                await cognee.datasets.delete_dataset(dataset_id)
                return {"success": True, "message": "Dataset deleted"}
            
            return {"success": False, "message": "Dataset not found"}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"success": False, "message": str(e)}

# Singleton instance
cognee_service = CogneeService()
