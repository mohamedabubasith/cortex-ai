
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

def apply_cognee_patches():
    """
    Apply critical monkeypatches for Cognee integration.
    Must be called BEFORE any other Cognee imports.
    """
    logger.info("Applying Cognee patches...")
    
    # 1. Set environment variables
    os.environ["EMBEDDING_PROVIDER"] = settings.EMBEDDING_PROVIDER
    os.environ["EMBEDDING_MODEL"] = settings.EMBEDDING_MODEL
    os.environ["EMBEDDING_DIMENSIONS"] = str(settings.EMBEDDING_DIMENSIONS)
    # os.environ["LLM_PROVIDER"] = "litellm" # Removed as per user request
    
    # FastEmbed patch REMOVED as per user request
    pass

    # 3. Patch pgvector if needed
    if settings.VECTOR_DB_PROVIDER == "pgvector":
        try:
            import cognee.infrastructure.databases.vector as vector_module
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
            
            vector_module.get_vector_engine = patched_get_vector_engine
            logger.info("Successfully patched get_vector_engine to force PGVector usage")
        except Exception as e:
            logger.error(f"Failed to patch get_vector_engine: {e}")

    # 4. Patch tiktoken
    try:
        import tiktoken
        original_encoding_for_model = tiktoken.encoding_for_model
        
        def patched_encoding_for_model(model_name):
            try:
                return original_encoding_for_model(model_name)
            except KeyError:
                return original_encoding_for_model("cl100k_base")
                
        tiktoken.encoding_for_model = patched_encoding_for_model
        logger.info("Successfully patched tiktoken")
    except Exception as e:
        logger.error(f"Failed to patch tiktoken: {e}")
