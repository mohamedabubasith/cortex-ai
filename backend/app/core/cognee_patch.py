
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level state for singletons
_fastembed_instance = None
_pgvector_instance = None

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
    
    # FastEmbed patch RESTORED because it is REQUIRED to fix the 'module not callable' bug
    if settings.EMBEDDING_PROVIDER == "fastembed":
        try:
            # Import the module we want to patch
            import cognee.infrastructure.databases.vector.embeddings as embeddings_module
            
            # Import our adapter
            from app.services.fastembed_adapter import FastEmbedAdapter
            
            # _fastembed_instance = None
            
            def patched_get_embedding_engine():
                global _fastembed_instance
                if _fastembed_instance is None:
                    logger.info(f"Creating FastEmbedAdapter with model: {settings.EMBEDDING_MODEL}")
                    _fastembed_instance = FastEmbedAdapter(model_name=settings.EMBEDDING_MODEL)
                return _fastembed_instance
            
            # Apply patch
            embeddings_module.get_embedding_engine = patched_get_embedding_engine
            logger.info("Successfully patched get_embedding_engine to use FastEmbedAdapter")
            
        except Exception as e:
            logger.error(f"Failed to patch get_embedding_engine: {e}")
            import traceback
            traceback.print_exc()

    # 3. Patch pgvector if needed
    if settings.VECTOR_DB_PROVIDER == "pgvector":
        try:
            import cognee.infrastructure.databases.vector as vector_module
            # Import from the module file directly to get the class
            from cognee.infrastructure.databases.vector.pgvector.PGVectorAdapter import PGVectorAdapter
            
            # _pgvector_instance = None
            
            def patched_get_vector_engine():
                global _pgvector_instance
                if _pgvector_instance is None:
                    # Construct URL manually as constructed_vector_db_url was removed
                    db_url = f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
                    
                    logger.info(f"Creating PGVectorAdapter with URL: {db_url}")
                    
                    # Create embedding engine
                    from app.services.fastembed_adapter import FastEmbedAdapter
                    embedding_engine = FastEmbedAdapter(model_name=settings.EMBEDDING_MODEL)
                    
                    # Instantiate PGVectorAdapter with correct signature
                    _pgvector_instance = PGVectorAdapter(
                        connection_string=db_url,
                        api_key=None,
                        embedding_engine=embedding_engine
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
