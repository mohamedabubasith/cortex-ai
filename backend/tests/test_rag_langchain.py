import pytest
import os
import tempfile
import uuid
import asyncio
from unittest.mock import MagicMock
from app.services.rag_service import RAGService
from app.core.config import settings

@pytest.fixture
def rag_service():
    """Create a RAGService instance for testing."""
    service = RAGService()
    # Use a separate test collection/path if possible, or just mock embeddings for speed
    service.persist_directory = tempfile.mkdtemp()
    return service

@pytest.fixture
def test_document():
    """Create a temporary test document."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        content = """
        The Martian
        Mark Watney is a botanist and engineer on the Ares 3 mission to Mars.
        During a dust storm, he is left behind and presumed dead.
        He must use his ingenuity to survive and signal Earth.
        Mars is a cold, dry planet with frequent dust storms.
        Botany is key to his survival as he grows potatoes in Martian soil.
        """
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.mark.asyncio
async def test_document_processing_and_search(rag_service, test_document):
    """Test full cycle: Load -> Split -> Embed -> Search."""
    kb_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    tenant_id = "test-tenant"
    
    # Process
    result = await rag_service.process_document(
        file_path=test_document,
        kb_id=kb_id,
        user_id=user_id,
        tenant_id=tenant_id,
        chunk_size=100,
        chunk_overlap=20,
        llm_config=None # Defaults to settings
    )
    
    assert result["success"] is True
    assert result["chunks"] > 0
    
    # Search
    query = "Mark Watney"
    filters = {"kb_id": kb_id}
    
    search_results = await rag_service.search(query, filters, llm_config=None)
    
    assert len(search_results) > 0
    assert "Mark Watney" in search_results[0]["content"]
    assert search_results[0]["metadata"]["kb_id"] == kb_id
    assert search_results[0]["metadata"]["user_id"] == user_id
    assert search_results[0]["metadata"]["tenant_id"] == tenant_id

@pytest.mark.asyncio
async def test_chunk_size_impact(rag_service, test_document):
    """Verify that chunk_size parameter is respected."""
    kb_id_small = str(uuid.uuid4())
    kb_id_large = str(uuid.uuid4())
    user_id = "test-user"
    
    # Small chunks
    res_small = await rag_service.process_document(
        file_path=test_document,
        kb_id=kb_id_small,
        user_id=user_id,
        tenant_id=None,
        chunk_size=50,
        chunk_overlap=0,
        llm_config=None
    )
    
    # Large chunks
    res_large = await rag_service.process_document(
        file_path=test_document,
        kb_id=kb_id_large,
        user_id=user_id,
        tenant_id=None,
        chunk_size=500,
        chunk_overlap=0,
        llm_config=None
    )
    
    # Metadata check: smaller chunk size should result in MORE chunks
    assert res_small["chunks"] > res_large["chunks"]

@pytest.mark.asyncio
async def test_deletion_integrity(rag_service, test_document):
    """Verify that deleting a KB removes its vectors from Chroma."""
    kb_id = str(uuid.uuid4())
    user_id = "test-user"
    
    # 1. Index
    await rag_service.process_document(test_document, kb_id, user_id, None, 100, 20, None)
    
    # 2. Verify it exists
    results = await rag_service.search("Martian", {"kb_id": kb_id}, None)
    assert len(results) > 0
    
    # 3. Delete
    delete_success = await rag_service.delete_kb(kb_id)
    assert delete_success is True
    
    # 4. Verify it's gone
    results_after = await rag_service.search("Martian", {"kb_id": kb_id}, None)
    assert len(results_after) == 0
