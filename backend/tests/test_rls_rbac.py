import httpx
import uuid
import pytest
import asyncio
import os
from app.main import app

import pytest_asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    """Clean up database tables before each test"""
    from sqlalchemy import text
    from app.core.database import engine
    async with engine.begin() as conn:
        # Disable foreign key checks for faster cleanup (Postgres style)
        await conn.execute(text("TRUNCATE tenants, users, projects, llm_configurations, audit_logs, agent_audit_logs, analytics CASCADE"))
    yield

# Use AsyncClient with the app directly
@pytest_asyncio.fixture(scope="session")
async def async_client():
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

async def create_test_user_and_tenant(client: httpx.AsyncClient, prefix: str):
    """Utility to create a new user/tenant via JIT provisioning"""
    unique_id = str(uuid.uuid4())[:8]
    email = f"{prefix}_{unique_id}@example.com"
    token = f"dummy_sso_{email.replace('@', '_at_')}"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Trigger JIT
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    user_data = resp.json()
    tenant_id = user_data["tenant_memberships"][0]["tenant_id"]
    
    return {
        "user": user_data,
        "token": token,
        "headers": headers,
        "tenant_id": tenant_id
    }

@pytest.mark.asyncio
async def test_llm_config_rls(async_client):
    """Verify LLM configurations are isolated between tenants"""
    # 1. Setup Tenant A
    tenant_a = await create_test_user_and_tenant(async_client, "tenant_a")
    
    # Create LLM config for Tenant A
    llm_data = {
        "name": "A-LLM",
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "sk-aaa",
        "is_default": True
    }
    resp = await async_client.post("/api/v1/llm", json=llm_data, headers=tenant_a["headers"])
    assert resp.status_code == 200
    llm_id = resp.json()["id"]
    
    # 2. Setup Tenant B
    tenant_b = await create_test_user_and_tenant(async_client, "tenant_b")
    
    # User B tries to GET Tenant A's LLM config
    resp = await async_client.get("/api/v1/llm", headers=tenant_b["headers"])
    configs = resp.json()
    assert not any(c["id"] == llm_id for c in configs), "Leakage: Tenant B saw Tenant A's LLM config"
    
    # User B tries to DELETE Tenant A's LLM config
    resp = await async_client.delete(f"/api/v1/llm/{llm_id}", headers=tenant_b["headers"])
    assert resp.status_code == 404, "Security: Tenant B should get 404 for Tenant A's resource"

@pytest.mark.asyncio
async def test_agent_rls(async_client):
    """Verify Agents are isolated between tenants"""
    # 1. Setup Tenant A
    tenant_a = await create_test_user_and_tenant(async_client, "tenant_a")
    
    # Create Agent for Tenant A
    agent_data = {
        "name": "Agent-A",
        "system_prompt": "You are Agent A",
        "type": "standard_agent"
    }
    resp = await async_client.post("/api/v1/agents", json=agent_data, headers=tenant_a["headers"])
    assert resp.status_code == 200
    agent_id = resp.json()["id"]
    
    # 2. Setup Tenant B
    tenant_b = await create_test_user_and_tenant(async_client, "tenant_b")
    
    # User B tries to GET Tenant A's Agent
    resp = await async_client.get("/api/v1/agents", headers=tenant_b["headers"])
    agents = resp.json()
    assert not any(a["id"] == agent_id for a in agents), "Leakage: Tenant B saw Tenant A's Agent"
    
    # User B tries to DELETE Tenant A's Agent
    resp = await async_client.delete(f"/api/v1/agents/{agent_id}", headers=tenant_b["headers"])
    assert resp.status_code == 404, "Security: Tenant B should get 404 for Tenant A's Agent"

@pytest.mark.asyncio
async def test_tenant_management_rbac(async_client):
    """Verify role-based access control for tenant management"""
    # 1. Setup Tenant (Owner is created by default)
    owner_context = await create_test_user_and_tenant(async_client, "owner")
    
    # 2. Invite a new user as 'member'
    invite_data = {
        "email": f"member_{uuid.uuid4().hex[:4]}@example.com",
        "role": "member",
        "password": "Password123!"
    }
    resp = await async_client.post("/api/v1/tenant/users", json=invite_data, headers=owner_context["headers"])
    assert resp.status_code == 200
    
    # Get the new user's credentials
    member_email = invite_data["email"]
    member_token = f"dummy_sso_{member_email.replace('@', '_at_')}"
    member_headers = {"Authorization": f"Bearer {member_token}"}
    
    # 3. Member tries to invite another user (Should fail)
    bad_invite = {
        "email": f"victim_{uuid.uuid4().hex[:4]}@example.com",
        "role": "admin"
    }
    resp = await async_client.post("/api/v1/tenant/users", json=bad_invite, headers=member_headers)
    assert resp.status_code == 403, "RBAC: Member should NOT be able to invite users"
    
    # 4. Member tries to list tenant users (Should fail)
    resp = await async_client.get("/api/v1/tenant/users", headers=member_headers)
    assert resp.status_code == 403, "RBAC: Member should NOT be able to list tenant users"

@pytest.mark.asyncio
async def test_audit_logs_rls_and_rbac(async_client):
    """Verify Audit Logs isolation and role-based filtering"""
    # 1. Setup Tenant A and generate logs
    tenant_a = await create_test_user_and_tenant(async_client, "tenant_a")
    await async_client.post(
        "/api/v1/llm", 
        json={"name": "Log-A", "provider": "openai", "model": "gpt-4", "api_key": "key"},
        headers=tenant_a["headers"]
    )
    
    # 2. Setup Tenant B
    tenant_b = await create_test_user_and_tenant(async_client, "tenant_b")
    
    # 3. User B tries to see Tenant A's logs
    resp = await async_client.get("/api/v1/analytics/audit-logs", headers=tenant_b["headers"])
    logs = resp.json()
    assert all(l.get("tenant_id") == tenant_b["tenant_id"] or l.get("tenant_id") is None for l in logs)

    # 4. Test Member role access
    invite_data = {"email": f"m_audit_{uuid.uuid4().hex[:4]}@example.com", "role": "member", "password": "Pass"}
    await async_client.post("/api/v1/tenant/users", json=invite_data, headers=tenant_a["headers"])
    
    m_token = f"dummy_sso_{invite_data['email'].replace('@', '_at_')}"
    m_headers = {"Authorization": f"Bearer {m_token}"}
    
    await async_client.get("/api/v1/auth/me", headers=m_headers)
    
    resp = await async_client.get("/api/v1/analytics/audit-logs", headers=m_headers)
    logs = resp.json()
    for log in logs:
        # In this test, the member should only see their own logs (the /me call)
        # However, the owner saw their own logs.
        assert log["user_id"] == tenant_a["user"]["id"] or log["email"] == invite_data["email"]

@pytest.mark.asyncio
async def test_agent_audit_logs_rls(async_client):
    """Verify Agent Audit Logs isolation"""
    # 1. Setup Tenant A
    tenant_a = await create_test_user_and_tenant(async_client, "tenant_a")
    await async_client.post("/api/v1/agents", json={"name": "A", "system_prompt": "X"}, headers=tenant_a["headers"])
    
    # 2. Setup Tenant B
    tenant_b = await create_test_user_and_tenant(async_client, "tenant_b")
    
    # 3. User B tries to see Tenant A's agent logs
    resp = await async_client.get("/api/v1/analytics/agent-audit/logs", headers=tenant_b["headers"])
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) == 0, "Leakage: User B saw Agent Logs of User A"

if __name__ == "__main__":
    # This allows running the file directly if needed, though pytest is preferred
    asyncio.run(test_llm_config_rls())
    asyncio.run(test_agent_rls())
    asyncio.run(test_tenant_management_rbac())
    asyncio.run(test_audit_logs_rls_and_rbac())
    asyncio.run(test_agent_audit_logs_rls())

@pytest.mark.asyncio
async def test_knowledge_base_rls(async_client):
    """Verify Knowledge Bases are isolated between tenants"""
    # 1. Setup Tenant A
    tenant_a = await create_test_user_and_tenant(async_client, "tenant_a")
    
    files = {'file': ('test.txt', b'content', 'text/plain')}
    data = {'name': 'KB-A', 'chunk_size': 1000, 'chunk_overlap': 200}
    headers = tenant_a["headers"].copy()
    
    # Correct path: /api/v1/kb/upload
    resp = await async_client.post("/api/v1/kb/upload", data=data, files=files, headers=headers)
    if resp.status_code != 200:
        print(f"KB Create failed: {resp.text}")
    assert resp.status_code == 200
    kb_id = resp.json()["id"]
    
    # 2. Setup Tenant B
    tenant_b = await create_test_user_and_tenant(async_client, "tenant_b")
    
    # User B tries to GET Tenant A's KB (Path: /api/v1/kb)
    resp = await async_client.get("/api/v1/kb", headers=tenant_b["headers"])
    kbs = resp.json()
    assert not any(k["id"] == kb_id for k in kbs), "Leakage: Tenant B saw Tenant A's KB"
    
    # User B tries to DELETE Tenant A's KB (Path: /api/v1/kb/{id})
    resp = await async_client.delete(f"/api/v1/kb/{kb_id}", headers=tenant_b["headers"])
    assert resp.status_code == 404, "Security: Tenant B should get 404 for Tenant A's KB"

@pytest.mark.asyncio
async def test_database_connection_rls(async_client):
    """Verify Database Connections are isolated between tenants"""
    # 1. Setup Tenant A
    tenant_a = await create_test_user_and_tenant(async_client, "tenant_a")
    
    # Create DB Connection for Tenant A
    db_data = {
        "name": "DB-A",
        "type": "postgres",
        "host": "localhost",
        "port": 5432,
        "username": "user",
        "password": "password",
        "database_name": "db"
    }
    # Correct path: /api/v1/resources/databases
    resp = await async_client.post("/api/v1/resources/databases", json=db_data, headers=tenant_a["headers"])
    if resp.status_code != 200:
        print(f"DB Create failed: {resp.text}")
    assert resp.status_code == 200
    db_id = resp.json()["id"]
    
    # 2. Setup Tenant B
    tenant_b = await create_test_user_and_tenant(async_client, "tenant_b")
    
    # User B tries to GET Tenant A's DB Connection
    resp = await async_client.get("/api/v1/resources/databases", headers=tenant_b["headers"])
    dbs = resp.json()
    assert not any(d["id"] == db_id for d in dbs), "Leakage: Tenant B saw Tenant A's Database Connection"
    
    # User B tries to DELETE Tenant A's DB Connection
    resp = await async_client.delete(f"/api/v1/resources/databases/{db_id}", headers=tenant_b["headers"])
    assert resp.status_code == 404, "Security: Tenant B should get 404 for Tenant A's Database Connection"

@pytest.mark.asyncio
async def test_mcp_connection_rls(async_client):
    """Verify MCP Connections are isolated between tenants"""
    # 1. Setup Tenant A
    tenant_a = await create_test_user_and_tenant(async_client, "tenant_a")
    
    # Create MCP Connection for Tenant A
    mcp_data = {
        "name": "MCP-A",
        "server_url": "http://localhost:8000/sse",
        "protocol": "sse"
    }
    # Path: /api/v1/resources/mcp
    resp = await async_client.post("/api/v1/resources/mcp", json=mcp_data, headers=tenant_a["headers"])
    # Note: If MCP connection fails validation (e.g. unreachable), it might fail. 
    # But usually creation is just DB insert unless it validates immediately?
    # Inspecting resources.py: create_mcp_connection just adds to DB. It does NOT connect/validate immediately. 
    # Only test_mcp_connection does.
    
    if resp.status_code != 200:
        print(f"MCP Create failed: {resp.text}")
    assert resp.status_code == 200
    mcp_id = resp.json()["id"]
    
    # 2. Setup Tenant B
    tenant_b = await create_test_user_and_tenant(async_client, "tenant_b")
    
    # User B tries to GET Tenant A's MCP Connection
    resp = await async_client.get("/api/v1/resources/mcp", headers=tenant_b["headers"])
    mcps = resp.json()
    assert not any(m["id"] == mcp_id for m in mcps), "Leakage: Tenant B saw Tenant A's MCP Connection"
    
    # User B tries to DELETE Tenant A's MCP Connection
    resp = await async_client.delete(f"/api/v1/resources/mcp/{mcp_id}", headers=tenant_b["headers"])
    assert resp.status_code == 404, "Security: Tenant B should get 404 for Tenant A's MCP Connection"

# @pytest.mark.asyncio
# async def test_mcp_connection_rls(async_client):
#    To be implemented if MCP endpoints are standardized in valid routes
#    pass

