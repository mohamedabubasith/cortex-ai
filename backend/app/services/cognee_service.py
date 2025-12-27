"""Cognee Service with Background Processing"""
"""
Cognee Service
Handles integration with the Cognee library for knowledge graph and vector search.
"""
import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
from app.core.config import settings

# CRITICAL: Set embedding provider BEFORE importing cognee
# This ensures Cognee reads the correct configuration during module initialization
os.environ["EMBEDDING_PROVIDER"] = settings.EMBEDDING_PROVIDER
os.environ["EMBEDDING_MODEL"] = settings.EMBEDDING_MODEL
os.environ["EMBEDDING_DIMENSIONS"] = str(settings.EMBEDDING_DIMENSIONS)

# Set persistent data path for Cognee (LanceDB)
# This ensures data survives server restarts
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT_DIR, "data")
LANCEDB_PATH = os.path.join(DATA_DIR, "lancedb")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Only set LanceDB paths if we are NOT using pgvector
# User explicitly requested to remove local DBs and use pgvector
if settings.VECTOR_DB_PROVIDER != "pgvector":
    os.environ["COGNEE_VECTOR_DB_PATH"] = LANCEDB_PATH
    os.environ["COGNEE_LANCEDB_URL"] = LANCEDB_PATH
else:
    # Ensure Cognee uses the configured Postgres vector DB
    # Cognee expects this env var for pgvector connection
    os.environ["VECTOR_DB_URL"] = settings.constructed_vector_db_url
    os.environ["DB_PROVIDER"] = settings.DB_PROVIDER
    os.environ["VECTOR_DB_PROVIDER"] = "pgvector"
    
    # Explicitly set DB vars for Cognee (crucial for local execution where env vars might not be set)
    os.environ["DB_HOST"] = settings.DB_HOST
    os.environ["DB_PORT"] = str(settings.DB_PORT)
    os.environ["DB_NAME"] = settings.DB_NAME
    os.environ["DB_USERNAME"] = settings.DB_USERNAME
    os.environ["DB_PASSWORD"] = settings.DB_PASSWORD

# Ensure persistent path for SQLite (if used as fallback for metadata)
COGNEE_DB_PATH = os.path.join(DATA_DIR, "cognee.db")
os.environ["COGNEE_DB_PATH"] = COGNEE_DB_PATH
os.environ["DB_PATH"] = COGNEE_DB_PATH

# Also set a specialized path for Cognee's internal storage if needed
os.environ["COGNEE_ROOT_DIR"] = DATA_DIR

import cognee
from sqlalchemy import text
from cognee.api.v1.search import SearchType
from cognee.api.v1.search import search as cognee_search
from cognee.modules.users.methods import get_default_user, get_user_by_email, create_user
from cognee.infrastructure.databases.relational import get_relational_engine
from cognee.infrastructure.databases.relational.ModelBase import Base as CogneeBase
import tiktoken
from cognee.infrastructure.databases.vector.embeddings.config import get_embedding_config

# CRITICAL MONKEYPATCH: Force pgvector usage
# Cognee caches the vector engine and doesn't always respect runtime env var changes
# This patch intercepts the get_vector_engine function to force pgvector
if settings.VECTOR_DB_PROVIDER == "pgvector":
    try:
        from cognee.infrastructure.databases.vector import get_vector_engine as original_get_vector_engine
        from cognee.infrastructure.databases.vector.pgvector import PGVectorAdapter
        
        _pgvector_instance = None
        
        def patched_get_vector_engine():
            global _pgvector_instance
            if _pgvector_instance is None:
                logger.info(f"Creating PGVectorAdapter with URL: {settings.constructed_vector_db_url}")
                _pgvector_instance = PGVectorAdapter(
                    url=settings.constructed_vector_db_url,
                    db_name=settings.DB_NAME
                )
            return _pgvector_instance
        
        # Replace the function in the module
        import cognee.infrastructure.databases.vector as vector_module
        vector_module.get_vector_engine = patched_get_vector_engine
        
        logger.info("Successfully patched get_vector_engine to force PGVector usage")
    except Exception as e:
        logger.error(f"Failed to patch get_vector_engine: {e}")
        import traceback
        traceback.print_exc()


# Monkeypatch tiktoken to support non-OpenAI models (e.g. fastembed)
# Cognee uses tiktoken for chunking but fails on unknown model names.
original_encoding_for_model = tiktoken.encoding_for_model

def patched_encoding_for_model(model_name):
    try:
        return original_encoding_for_model(model_name)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        return tiktoken.get_encoding("cl100k_base")

tiktoken.encoding_for_model = patched_encoding_for_model

logger = logging.getLogger(__name__)

# MONKEYPATCH: Force MD_JSON mode for Cognee's instructor calls
# This is much more robust for Qwen and other non-OpenAI models
# than the default tool-calling mode, which often fails with 422 errors.
import instructor
original_from_litellm = instructor.from_litellm

def patched_from_litellm(*args, **kwargs):
    # Force MD_JSON mode if no mode is specified (Cognee's default)
    if "mode" not in kwargs or kwargs["mode"] is None:
        kwargs["mode"] = instructor.Mode.MD_JSON
    return original_from_litellm(*args, **kwargs)

instructor.from_litellm = patched_from_litellm

# MONKEYPATCH: Increase retries for Cognee's OpenAI adapter
# This gives the model more chances to follow the complex schema
try:
    from cognee.infrastructure.llm.structured_output_framework.litellm_instructor.llm.openai.adapter import OpenAIAdapter
    OpenAIAdapter.MAX_RETRIES = 10
    logger.info("Monkeypatched OpenAIAdapter.MAX_RETRIES to 10")
except ImportError:
    logger.warning("Could not monkeypatch OpenAIAdapter.MAX_RETRIES")

class CogneeService:
    def __init__(self):
        pass

    async def setup_cognee(self):
        """
        Initialize/setup Cognee (create tables, etc.)
        Cognee version: 0.2.0+
        """
        try:
            # Try importing from new location first, fallback to old if needed
            try:
                from cognee.modules.engine.operations.setup import setup
            except ImportError:
                from cognee.infrastructure.databases.relational.create_db_and_tables import create_db_and_tables as setup
            
            await setup()
            logger.info("Cognee setup completed successfully")
            return {"success": True, "message": "Setup complete"}
        except Exception as e:
            logger.error(f"Failed to setup Cognee: {e}")
            raise e

    def _configure_embeddings(self):
        """Configure embedding settings based on environment"""
        embed_config = get_embedding_config()
        
        current_provider = settings.EMBEDDING_PROVIDER
        
        if current_provider == "fastembed":
            # Configure fastembed
            embed_config.embedding_provider = "fastembed"
            embed_config.embedding_model = settings.EMBEDDING_MODEL
            embed_config.embedding_dimensions = settings.EMBEDDING_DIMENSIONS
            embed_config.embedding_endpoint = None
            embed_config.embedding_api_key = None
            logger.info(f"Configured FastEmbed with model: {embed_config.embedding_model}")

    async def initialize(self):
        """Initialize Cognee (create tables, etc.)"""
        logger.info("Initializing CogneeService...")
        
        # Configure embeddings early
        self._configure_embeddings()
        
        # CRITICAL: Force Cognee to use pgvector instead of LanceDB
        # This must happen BEFORE any Cognee operations
        if settings.VECTOR_DB_PROVIDER == "pgvector":
            try:
                from cognee.infrastructure.databases.vector import get_vector_engine
                # Force reinitialize vector engine with pgvector
                vector_engine = get_vector_engine()
                logger.info(f"Initialized vector engine: {type(vector_engine).__name__}")
                
                # Verify we're using PGVector, not LanceDB
                if "Lance" in type(vector_engine).__name__:
                    logger.error("CRITICAL: Vector engine is LanceDB despite pgvector config!")
                    # Try to force pgvector by clearing the cached engine
                    from cognee.infrastructure.databases.vector import vector_db_config
                    vector_db_config.vector_db_url = settings.constructed_vector_db_url
                    vector_db_config.vector_db_provider = "pgvector"
                    # Re-get engine
                    vector_engine = get_vector_engine()
                    logger.info(f"Re-initialized vector engine: {type(vector_engine).__name__}")
            except Exception as e:
                logger.warning(f"Could not explicitly configure vector engine: {e}")
        
        try:
            # Try setup first
            await self.setup_cognee()
        except Exception as e:
            logger.warning(f"Initial setup failed ({e}). Retrying setup...")
            await self.setup_cognee()

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
                # Fix for litellm: if using custom endpoint (like NVIDIA, Groq, etc.),
                # prefix with openai/ to force OpenAI protocol.
                if llm_config.base_url and not model.startswith("openai/"):
                    model = f"openai/{model}"
                cognee.config.set_llm_model(model)
                
                # Optimization for Qwen and other non-OpenAI models:
                # We use a monkeypatch at the top of this file to force MD_JSON mode
                # and increase retries, which is much more effective than env vars.
                os.environ["STRUCTURED_OUTPUT_FRAMEWORK"] = "instructor"

            # Configure Embeddings
            # Ensure base config is set
            self._configure_embeddings()
            
            embed_config = get_embedding_config()
            # Check configured provider (defaults to fastembed now)
            current_provider = embed_config.embedding_provider
            
            # Only override embedding endpoint if we are NOT using fastembed
            if current_provider != "fastembed" and llm_config.base_url:
                embed_config.embedding_endpoint = llm_config.base_url
                embed_config.embedding_api_key = llm_config.api_key
                
                # Heuristic for NVIDIA
                if "nvidia" in llm_config.base_url.lower():
                    # NVIDIA usually uses nv-embed-v1
                    embed_config.embedding_model = "openai/nvidia/nv-embed-v1"

    async def _get_cognee_user(self, user_email: str):
        """Get or create a Cognee user for multi-tenancy"""
        if not user_email:
            logger.info("No user_email provided, using default Cognee user")
            return await get_default_user()
        
        # Normalize email to ensure consistency across logins
        user_email = user_email.lower().strip()
        
        try:
            user = await get_user_by_email(user_email)
            if not user:
                logger.info(f"Creating new Cognee user for: {user_email}")
                user = await create_user(email = user_email, password = "default_password")
            
            logger.info(f"Cognee user for {user_email}: id={user.id} (type={type(user.id)})")
            return user
        except Exception as e:
            logger.error(f"Error getting/creating Cognee user: {e}")
            return await get_default_user()

    async def _get_dataset_by_name(self, dataset_name: str, user_id) -> Optional[dict]:
        """Check if dataset exists for a specific user"""
        try:
            from cognee.modules.data.methods import get_datasets_by_name
            from uuid import UUID
            
            # Ensure user_id is a UUID object
            uid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
            
            logger.info(f"Checking dataset '{dataset_name}' for user_id={uid}")
            datasets = await get_datasets_by_name(dataset_name, uid)
            
            if datasets and len(datasets) > 0:
                logger.info(f"Found dataset: {datasets[0].id} for name '{dataset_name}'")
                return datasets[0]
            
            logger.warning(f"Dataset '{dataset_name}' NOT FOUND for user_id={uid}")
            return None
        except Exception as e:
            logger.error(f"Error checking dataset for user {user_id}: {e}")
            return None
    
    async def add_document(self, file_path: str, dataset_name: str, llm_config, user_email: str = None) -> Dict[str, Any]:
        """
        Add a document to a specific dataset.
        Passes file path to Cognee.
        """
        self._configure_llm(llm_config)
        try:
            logger.info(f"Adding file {file_path} to dataset {dataset_name} for user {user_email}")
            
            user = await self._get_cognee_user(user_email)
            
            # Add data to Cognee (creates dataset if needed)
            await cognee.add(
                data=file_path,
                dataset_name=dataset_name,
                user = user
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
            logger.info(f"Cognifying dataset {dataset_name} for user {user_email}")
            
            user = await self._get_cognee_user(user_email)
            
            # Cognify
            await cognee.cognify(
                datasets=[dataset_name],
                user = user
            )
            
            return {"success": True, "message": "Dataset cognify started"}
        except Exception as e:
            logger.error(f"Error cognifying dataset: {e}")
            raise e

    async def get_status(self, dataset_name: str, user_email: str = None) -> Dict[str, Any]:
        """
        Get the status of a dataset using Cognee's pipeline status API.
        Handles PipelineRunStatus enum format.
        """
        try:
            user = await self._get_cognee_user(user_email)
            dataset = await self._get_dataset_by_name(dataset_name, user.id)
            if not dataset:
                return {
                    "status": "not_found",
                    "message": f"Dataset '{dataset_name}' not found for user {user_email}"
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
            
            # Ensure datasets is always a list of strings
            search_datasets = datasets if isinstance(datasets, list) else [datasets]
            
            logger.info(f"Calling cognee_search with datasets={search_datasets} for user {user_email}")
            
            user = await self._get_cognee_user(user_email)
            
            # Pass user parameter to Cognee for multi-tenancy
            results = await cognee_search(
                query_type=s_type,
                query_text=query_text,
                datasets=search_datasets,
                user = user
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

    async def delete_dataset(self, dataset_name: str, user_email: str = None) -> Dict[str, Any]:
        """
        Delete a specific dataset.
        """
        try:
            logger.info(f"Deleting dataset {dataset_name} for user {user_email}")
            
            user = await self._get_cognee_user(user_email)
            dataset = await self._get_dataset_by_name(dataset_name, user.id)
            if dataset:
                dataset_id = dataset.id
                # await cognee.prune.prune_data(dataset_name) # Prune might also need user context if it's user-aware
                # delete_dataset takes ID
                await cognee.datasets.delete_dataset(dataset_id)
                return {"success": True, "message": "Dataset deleted"}
            
            return {"success": False, "message": "Dataset not found"}
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return {"success": False, "message": str(e)}

# Singleton instance
cognee_service = CogneeService()
