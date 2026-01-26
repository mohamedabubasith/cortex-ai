import pytest
import asyncio
import uuid
import httpx
from sqlalchemy import text
from app.main import app # Load dotenv and config
from app.core.database import engine
import pytest_asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(autouse=True)
async def setup_schema():
    """Manually create KnowledgeBaseMember table if it doesn't exist (hack for missing migration)"""
    async with engine.begin() as conn:
        # Check if table exists
        result = await conn.execute(text("SELECT to_regclass('public.knowledge_base_members')"))
        exists = result.scalar()
        if not exists:
            # Manually create table for testing purposes
            await conn.execute(text("""
                CREATE TABLE knowledge_base_members (
                    id VARCHAR PRIMARY KEY,
                    kb_id VARCHAR REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                    user_id VARCHAR REFERENCES users(id),
                    role VARCHAR DEFAULT 'viewer',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
                )
            """))
            print("Created knowledge_base_members table via test fixture.")
        
        # Cleanup
        await conn.execute(text("TRUNCATE tenants, users, projects, knowledge_bases, knowledge_base_members CASCADE"))
    yield

@pytest_asyncio.fixture(scope="session")
async def async_client():
    from app.main import app
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

async def create_test_user_and_tenant(client, prefix):
    unique_id = str(uuid.uuid4())[:8]
    email = f"{prefix}_{unique_id}@example.com"
    token = f"dummy_sso_{email.replace('@', '_at_')}"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Trigger JIT
    resp = await client.get("/api/v1/auth/me", headers=headers)
    user_data = resp.json()
    return user_data, headers, email

@pytest.mark.asyncio
async def test_kb_sharing_flow(async_client):
    """Test KB Sharing Flow"""
    # 1. Setup User A (Owner)
    user_a, headers_a, email_a = await create_test_user_and_tenant(async_client, "user_a")
    
    # 2. Setup User B (Same Tenant - usually auto-created tenants are separate in JIT logic unless they join same, 
    # but the API enforces common tenant.
    # In JIT mock "dummy_sso", typically it creates a NEW tenant for each user.
    # So we need to manually ADD User B to User A's tenant for them to share.
    
    user_b, headers_b, email_b = await create_test_user_and_tenant(async_client, "user_b")
    
    # Add User B to User A's tenant
    tenant_id_a = user_a["tenant_memberships"][0]["tenant_id"]
    
    # We can use the tenant invite/add endpoint if available, or force it via SQL/fixture?
    # Or just use the 'invite' endpoint which was tested in rbac.
    invite_data = {
        "email": f"invited_{uuid.uuid4().hex[:4]}@example.com",
        "role": "member",
        "password": "Password123!"
    }
    # Invite User C (who will be our target) into User A's tenant
    resp = await async_client.post("/api/v1/tenant/users", json=invite_data, headers=headers_a)
    assert resp.status_code == 200
    
    # Get User C's token (the Invited one)
    email_c = invite_data["email"]
    token_c = f"dummy_sso_{email_c.replace('@', '_at_')}"
    headers_c = {"Authorization": f"Bearer {token_c}"}
    
    # Ensure User C is initialized
    resp = await async_client.get("/api/v1/auth/me", headers=headers_c)
    user_c = resp.json()
    
    # 3. User A Creates KB
    files = {'file': ('share_test.txt', b'secret info', 'text/plain')}
    data = {'name': 'Secret-KB', 'chunk_size': 1000}
    # Important: Create KB
    resp = await async_client.post("/api/v1/kb/upload", data=data, files=files, headers=headers_a)
    # Check for success (200 OK)
    if resp.status_code != 200:
        print(f"KB Creation Failed: {resp.text}")
    assert resp.status_code == 200
    kb_id = resp.json()["id"]
    
    # 4. Verify User C cannot see it yet
    resp = await async_client.get("/api/v1/kb", headers=headers_c)
    kbs = resp.json()
    assert not any(k["id"] == kb_id for k in kbs)
    
    # 5. Share KB with User C
    share_req = {"email": email_c, "role": "viewer"}
    resp = await async_client.post(f"/api/v1/kb/{kb_id}/share", json=share_req, headers=headers_a)
    assert resp.status_code == 200
    
    # 6. Verify User C CAN see it now
    resp = await async_client.get("/api/v1/kb", headers=headers_c)
    kbs = resp.json()
    assert any(k["id"] == kb_id for k in kbs)
    
    # 7. Verify User C can get by ID
    resp = await async_client.get(f"/api/v1/kb/{kb_id}/status", headers=headers_c)
    assert resp.status_code == 200
    
    # 8. Unshare
    resp = await async_client.delete(f"/api/v1/kb/{kb_id}/share/{user_c['id']}", headers=headers_a)
    assert resp.status_code == 200
    
    # 9. Verify User C cannot see it again
    resp = await async_client.get("/api/v1/kb", headers=headers_c)
    kbs = resp.json()
    assert not any(k["id"] == kb_id for k in kbs)
