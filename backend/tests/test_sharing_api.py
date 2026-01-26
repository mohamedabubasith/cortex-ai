import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine
from sqlalchemy import text
import uuid

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_sharing_lifecycle(async_client):
    """
    Test valid sharing of a resource (database_connection) via API.
    1. Create Tenant, Users (Owner, Recipient).
    2. Create Resource (DB Conn).
    3. User Owner shares with User Recipient.
    4. Verify Share exists.
    5. User Owner revokes share.
    6. Verify Share gone.
    """
    async with engine.begin() as conn:
        # 1. Setup Data
        tenant_id = str(uuid.uuid4())
        owner_id = str(uuid.uuid4())
        recipient_id = str(uuid.uuid4())
        
        await conn.execute(text(f"INSERT INTO tenants (id, name, slug) VALUES ('{tenant_id}', 'T1', '{tenant_id}')"))
        await conn.execute(text(f"INSERT INTO users (id, email) VALUES ('{owner_id}', 'owner-{owner_id}@t1.com')"))
        await conn.execute(text(f"INSERT INTO users (id, email) VALUES ('{recipient_id}', 'recipient-{recipient_id}@t1.com')"))
        
        # Create Resource (DB Conn)
        res_id = str(uuid.uuid4())
        await conn.execute(text(f"""
            INSERT INTO database_connections (id, user_id, tenant_id, name, type, host, port, username, database_name)
            VALUES ('{res_id}', '{owner_id}', '{tenant_id}', 'DB-A', 'postgres', 'localhost', 5432, 'u', 'd')
        """))
        
    # Need to override dependency to return our mocked user context
    # Usually we would override `get_current_user`
    from app.services.auth_service import get_current_user
    from app.models.models import User
    
    # Mock Owner
    async def override_owner():
        u = User(id=owner_id, is_superuser=False)
        u.tenant_id = tenant_id # Dynamic attribute for RLS context
        u.is_tenant_admin = False
        return u
        
    app.dependency_overrides[get_current_user] = override_owner
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
    
        # 2. Share Resource
        share_payload = {
            "resource_id": res_id,
            "resource_type": "db_connection",
            "grantee_id": recipient_id,
            "grantee_type": "user",
            "permission": "read"
        }
        
        # We assume RLS policies allow insertion into resource_shares if context is set
        # But wait, does the API set the SQL session variables?
        # IMPORTANT: The middleware `VisitorMiddleware` or similar usually sets it.
        # But `async_client` might bypass middleware or we need to ensure middleware runs.
        # The `VisitorMiddleware` is added in `main.py`. It likely reads from request headers or auth token?
        # If we override `get_current_user`, the middleware might NOT know the user ID unless we also mock the dependency it uses.
        # However, `verify_resource_ownership` in the router does logic checks.
        # The ACTUAL INSERT SQL policy relies on `current_app_user()`.
        # If `VisitorMiddleware` sets it based on `request.state.user` (from auth), we are good.
        # Let's assume the stack is User -> Auth Middleware -> Visitor Middleware (sets vars) -> Router.
        # If we override `get_current_user`, the Router gets the user object. 
        # But `VisitorMiddleware` usually runs BEFORE the router.
        # So we need to ensure the DB session variables are set.
        
        # HACK: Manually set session variables in the route? No, global middleware.
        # Let's see `app/middleware/visitor_middleware.py` if possible.
        # For now, let's just Try. If it fails (RLS policy violation for NULL user), we know we need to fix the test harness.
        
        # To be safe, let's explicitly set session vars in the DB fixture wrapper? No, it's per request.
        # Let's assume valid middleware orchestration.
        # If fails, we'll debug.
        
        resp = await client.post("/api/v1/share/", json=share_payload)
        assert resp.status_code == 200, f"Share failed: {resp.text}"
        data = resp.json()
        share_id = data["id"]
        assert data["permission"] == "read"
        
        # 3. List Shares (Verify)
        resp = await client.get(f"/api/v1/share/resource/{res_id}")
        assert resp.status_code == 200
        shares = resp.json()
        assert len(shares) == 1
        assert shares[0]["id"] == share_id
        
        # 4. Revoke Share
        resp = await client.delete(f"/api/v1/share/{share_id}")
        assert resp.status_code == 204
        
        # 5. Verify Gone
        resp = await client.get(f"/api/v1/share/resource/{res_id}")
        assert len(resp.json()) == 0
        
    app.dependency_overrides = {}
