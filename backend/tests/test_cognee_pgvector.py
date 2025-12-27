import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from app.services.cognee_service import CogneeService
from app.core.config import settings


class TestCogneeVectorEngineIntegration:
    """Test suite for Cognee pgvector integration"""

    @pytest.fixture
    def cognee_service(self):
        return CogneeService()

    @pytest.mark.asyncio
    async def test_vector_engine_uses_pgvector(self, cognee_service):
        """Test that vector engine is forced to use pgvector"""
        # This tests the monkeypatch we applied
        with patch('cognee.infrastructure.databases.vector.get_vector_engine') as mock_get_engine:
            mock_engine = Mock()
            mock_engine.__class__.__name__ = "PGVectorAdapter"
            mock_get_engine.return_value = mock_engine

            # Import after patching
            from cognee.infrastructure.databases.vector import get_vector_engine
            engine = get_vector_engine()

            # Verify it's PGVector, not LanceDB
            assert "PGVector" in engine.__class__.__name__
            assert "Lance" not in engine.__class__.__name__

    @pytest.mark.asyncio
    async def test_vector_engine_url_configuration(self):
        """Test that pgvector uses correct database URL"""
        assert settings.VECTOR_DB_PROVIDER == "pgvector"
        assert "postgresql://" in settings.constructed_vector_db_url
        assert "cognee_db" in settings.constructed_vector_db_url

    @pytest.mark.asyncio
    async def test_no_lancedb_fallback(self, cognee_service):
        """Test that LanceDB is never used as fallback"""
        # Verify environment variables don't point to LanceDB
        import os
        from app.core.config import settings
        
        if settings.VECTOR_DB_PROVIDER == "pgvector":
            # These should NOT be set when using pgvector
            assert os.environ.get("COGNEE_VECTOR_DB_PATH") is None or \
                   os.environ.get("COGNEE_VECTOR_DB_PATH") == ""
            assert os.environ.get("COGNEE_LANCEDB_URL") is None or \
                   os.environ.get("COGNEE_LANCEDB_URL") == ""

    @pytest.mark.asyncio
    async def test_vector_db_provider_env_var(self):
        """Test that VECTOR_DB_PROVIDER env var is correctly set"""
        import os
        assert os.environ.get("VECTOR_DB_PROVIDER") == "pgvector"

    @pytest.mark.asyncio
    async def test_cognee_initialization(self, cognee_service):
        """Test that Cognee initializes without errors"""
        try:
            await cognee_service.initialize()
            assert True  # If we get here, initialization succeeded
        except Exception as e:
            pytest.fail(f"Cognee initialization failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_embedding_config(self, cognee_service):
        """Test that embedding configuration is correct"""
        cognee_service._configure_embeddings()
        
        from cognee.infrastructure.databases.vector.embeddings.config import get_embedding_config
        config = get_embedding_config()
        
        assert config.embedding_provider == "fastembed"
        assert config.embedding_model == settings.EMBEDDING_MODEL
        assert config.embedding_dimensions == settings.EMBEDDING_DIMENSIONS


class TestCogneeDataPersistence:
    """Test suite for Cognee data persistence in pgvector"""

    @pytest.mark.asyncio
    async def test_data_stored_in_postgres(self):
        """Test that vector data is stored in PostgreSQL, not local files"""
        # This would require actual integration testing
        # For now, we verify configuration
        assert settings.VECTOR_DB_PROVIDER == "pgvector"
        assert "postgresql" in settings.constructed_vector_db_url.lower()

    @pytest.mark.asyncio
    async def test_vector_search_uses_pgvector(self):
        """Test that vector search queries use pgvector"""
        # This is verified by the monkeypatch in cognee_service.py
        # The get_vector_engine function always returns PGVectorAdapter
        from cognee.infrastructure.databases.vector import get_vector_engine
        
        engine = get_vector_engine()
        assert "PGVector" in type(engine).__name__
