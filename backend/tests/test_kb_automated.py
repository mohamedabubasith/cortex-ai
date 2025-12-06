"""
Automated Test Suite for Knowledge Base APIs
Uses pytest for comprehensive testing

Run with: pytest test_kb_automated.py -v
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db, Base
from app.models import models
from app.services.cognee_service import cognee_service
import uuid

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_kb.db"

# Test fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session(test_db_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def client(db_session):
    """Create a test client."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = models.User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        hashed_password="$2b$12$test_hashed_password",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_llm_config(db_session, test_user):
    """Create a test LLM configuration."""
    llm_config = models.LLMConfiguration(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        name="Test LLM",
        provider="openai",
        model="gpt-4",
        api_key="sk-test-key",
        base_url=None
    )
    db_session.add(llm_config)
    await db_session.commit()
    await db_session.refresh(llm_config)
    return llm_config

@pytest.fixture
def test_file():
    """Create a temporary test file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("""
        Test Document for Knowledge Base
        
        This document contains information about:
        - Testing
        - Validation
        - Knowledge Base APIs
        - Automated Testing
        
        The system should be able to index and query this document.
        """)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    # Mock token - in real tests you'd generate a proper JWT
    return {"Authorization": f"Bearer test_token_{test_user.id}"}


# ==================== TESTS ====================

class TestCogneeService:
    """Test Cognee Service methods."""
    
    @pytest.mark.asyncio
    async def test_upload_and_index_success(self, test_llm_config, test_file):
        """Test successful upload and indexing."""
        dataset_name = f"test_dataset_{uuid.uuid4()}"
        
        result = await cognee_service.upload_and_index(
            test_llm_config,
            test_file,
            os.path.basename(test_file),
            dataset_name
        )
        
        assert result["success"] == True
        assert result["status"] in ["indexed", "processing"]
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_upload_nonexistent_file(self, test_llm_config):
        """Test upload with non-existent file."""
        result = await cognee_service.upload_and_index(
            test_llm_config,
            "/nonexistent/file.txt",
            "file.txt",
            "test_dataset"
        )
        
        assert result["success"] == False
        assert result["status"] == "failed"
        assert "not found" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_processing_status(self):
        """Test status retrieval."""
        dataset_name = f"test_dataset_{uuid.uuid4()}"
        
        # Initially should be pending
        status = await cognee_service.get_processing_status(dataset_name)
        assert status == "pending"
        
        # After setting
        cognee_service.processing_status[dataset_name] = "indexed"
        status = await cognee_service.get_processing_status(dataset_name)
        assert status == "indexed"
    
    @pytest.mark.asyncio
    async def test_query_unindexed_dataset(self, test_llm_config):
        """Test querying an unindexed dataset."""
        dataset_name = f"test_dataset_{uuid.uuid4()}"
        
        result = await cognee_service.query(
            test_llm_config,
            "test query",
            dataset_name
        )
        
        assert result["success"] == False
        assert "not ready" in result.get("message", "").lower()
    
    @pytest.mark.asyncio
    async def test_delete_dataset(self, test_llm_config):
        """Test dataset deletion."""
        dataset_name = f"test_dataset_{uuid.uuid4()}"
        cognee_service.processing_status[dataset_name] = "indexed"
        
        result = await cognee_service.delete_dataset(test_llm_config, dataset_name)
        
        # Should not be in status dict anymore
        status = await cognee_service.get_processing_status(dataset_name)
        assert status == "pending"


class TestKnowledgeBaseAPI:
    """Test Knowledge Base API endpoints."""
    
    def test_upload_kb_file_invalid_type(self, client, auth_headers, test_user):
        """Test upload with invalid file type."""
        # Create test file with invalid extension
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        
        try:
            with open(temp_path, 'rb') as file:
                response = client.post(
                    "/api/v1/resources/kb/upload",
                    headers=auth_headers,
                    files={"file": ("test.exe", file, "application/octet-stream")}
                )
            
            assert response.status_code == 400
            assert "Unsupported file type" in response.json()["detail"]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_upload_kb_file_success(self, client, auth_headers, test_file, test_llm_config):
        """Test successful file upload."""
        with open(test_file, 'rb') as file:
            response = client.post(
                "/api/v1/resources/kb/upload",
                headers=auth_headers,
                files={"file": (os.path.basename(test_file), file, "text/plain")},
                params={"llm_config_id": test_llm_config.id}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == os.path.basename(test_file)
        assert data["status"] in ["pending", "processing", "indexed"]
    
    def test_get_kb_files(self, client, auth_headers):
        """Test listing KB files."""
        response = client.get(
            "/api/v1/resources/kb",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_kb_status_not_found(self, client, auth_headers):
        """Test status check for non-existent KB."""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/resources/kb/{fake_id}/status",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_query_kb_not_indexed(self, client, auth_headers, db_session, test_user, test_llm_config, test_file):
        """Test querying a document that's not indexed."""
        # Create KB with pending status
        kb = models.KnowledgeBase(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            name="test.txt",
            filename="test.txt",
            file_path=test_file,
            file_type="text/plain",
            status="pending"
        )
        db_session.add(kb)
        asyncio.run(db_session.commit())
        
        response = client.post(
            f"/api/v1/resources/kb/{kb.id}/query",
            headers=auth_headers,
            json={
                "query": "test query",
                "llm_config_id": test_llm_config.id
            }
        )
        
        assert response.status_code == 400
        assert "not ready" in response.json()["detail"].lower()
    
    def test_delete_kb_success(self, client, auth_headers, db_session, test_user, test_file):
        """Test successful KB deletion."""
        # Create KB
        kb = models.KnowledgeBase(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            name="test.txt",
            filename="test.txt",
            file_path=test_file,
            file_type="text/plain",
            status="indexed"
        )
        db_session.add(kb)
        asyncio.run(db_session.commit())
        
        response = client.delete(
            f"/api/v1/resources/kb/{kb.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_delete_kb_not_found(self, client, auth_headers):
        """Test deletion of non-existent KB."""
        fake_id = str(uuid.uuid4())
        response = client.delete(
            f"/api/v1/resources/kb/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestEndToEndWorkflow:
    """Test complete workflow from upload to delete."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, client, auth_headers, test_file, test_llm_config, db_session):
        """Test complete upload → status → query → delete workflow."""
        kb_id = None
        
        try:
            # 1. Upload
            with open(test_file, 'rb') as file:
                upload_response = client.post(
                    "/api/v1/resources/kb/upload",
                    headers=auth_headers,
                    files={"file": (os.path.basename(test_file), file, "text/plain")},
                    params={"llm_config_id": test_llm_config.id}
                )
            
            assert upload_response.status_code == 200
            kb_id = upload_response.json()["id"]
            
            # 2. Check Status
            status_response = client.get(
                f"/api/v1/resources/kb/{kb_id}/status",
                headers=auth_headers
            )
            
            assert status_response.status_code == 200
            assert "status" in status_response.json()
            
            # 3. List (should include our file)
            list_response = client.get(
                "/api/v1/resources/kb",
                headers=auth_headers
            )
            
            assert list_response.status_code == 200
            files = list_response.json()
            assert any(f["id"] == kb_id for f in files)
            
            # 4. Delete
            delete_response = client.delete(
                f"/api/v1/resources/kb/{kb_id}",
                headers=auth_headers
            )
            
            assert delete_response.status_code == 200
            
            # 5. Verify deletion
            list_response_after = client.get(
                "/api/v1/resources/kb",
                headers=auth_headers
            )
            files_after = list_response_after.json()
            assert not any(f["id"] == kb_id for f in files_after)
            
        except Exception as e:
            # Cleanup on error
            if kb_id:
                client.delete(f"/api/v1/resources/kb/{kb_id}", headers=auth_headers)
            raise e


# Test summary
def test_summary():
    """Print test summary information."""
    print("\n" + "="*60)
    print("📊 Knowledge Base API Test Suite")
    print("="*60)
    print("\nTests included:")
    print("✅ Cognee Service tests (5 tests)")
    print("✅ API endpoint tests (7 tests)")
    print("✅ End-to-end workflow test (1 test)")
    print("\nTotal: 13 comprehensive tests")
    print("="*60)
