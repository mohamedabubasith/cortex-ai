import httpx
import uuid
import asyncio
import os
import json
from pathlib import Path

# Base URL for the running API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

async def get_user_headers(email: str):
    """Helper to get headers for a user (simulating JIT auth)"""
    token = f"dummy_sso_{email.replace('@', '_at_')}"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Trigger JIT
        resp = await client.get(f"{API_BASE_URL}/auth/me", headers=headers)
        if resp.status_code != 200:
            print(f"[Error] JIT Auth failed for {email}: {resp.status_code} - {resp.text}")
            return None, None
        return headers, resp.json()

async def test_organization_e2e():
    print("\n" + "="*80)
    print("ORGANIZATION END-TO-END TEST SUITE")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # ==========================================
        # SCENARIO 1: TENANT MANAGEMENT
        # ==========================================
        print("\n--- SCENARIO 1: TENANT MANAGEMENT ---")
        
        # 1. Create Owner (creates their own tenant)
        email_owner = f"org_owner_{uuid.uuid4().hex[:4]}@example.com"
        headers_owner, user_owner = await get_user_headers(email_owner)
        tenant_id = user_owner["tenant_memberships"][0]["tenant_id"]
        print(f"✓ Owner created: {email_owner} (Tenant: {tenant_id})")
        
        # 2. Create Member (initially in their own separate tenant)
        email_member = f"org_member_{uuid.uuid4().hex[:4]}@example.com"
        headers_member, user_member = await get_user_headers(email_member)
        print(f"✓ Member created: {email_member}")
        
        # 3. Owner adds Member to their tenant as 'viewer' (default role assumption or explicit)
        print("[Step] Adding Member to Owner's tenant as 'viewer'...")
        resp = await client.post(
            f"{API_BASE_URL}/tenants/{tenant_id}/members",
            json={"user_id": user_member["id"], "role": "member"}, # 'member' role usually implied viewer/basic access
            headers=headers_owner
        )
        assert resp.status_code == 200, f"Add member failed: {resp.text}"
        print("✓ Member added to tenant")

        # ==========================================
        # SCENARIO 2: RESOURCE CREATION
        # ==========================================
        print("\n--- SCENARIO 2: RESOURCE CREATION ---")

        # 1. Owner creates a Knowledge Base (Upload file)
        print("[Step] Owner uploading Knowledge Base...")
        dummy_file_content = b"This is a test document for organization E2E testing."
        files = {'file': ('test_doc.txt', dummy_file_content, 'text/plain')}
        
        resp = await client.post(
            f"{API_BASE_URL}/kb/upload",
            files=files,
            headers={"Authorization": headers_owner["Authorization"]} # No Content-Type for multipart
        )
        if resp.status_code != 200:
             print(f"[FAIL] KB Upload failed: {resp.status_code} - {resp.text}")
             return
        kb_data = resp.json()
        kb_id = kb_data["id"]
        print(f"✓ KB Created: {kb_id}")

        # 2. Owner creates an MCP Connection
        print("[Step] Owner creating MCP Connection...")
        mcp_payload = {
            "name": "Test MCP",
            "server_url": "http://localhost:8000/mcp/test",
            "protocol": "sse"
        }
        resp = await client.post(
            f"{API_BASE_URL}/resources/mcp",
            json=mcp_payload,
            headers=headers_owner
        )
        assert resp.status_code == 200, f"MCP create failed: {resp.text}"
        mcp_data = resp.json()
        mcp_id = mcp_data["id"]
        print(f"✓ MCP Created: {mcp_id}")

        # ==========================================
        # SCENARIO 3: USER-BASED SHARING (Explicit Share)
        # ==========================================
        print("\n--- SCENARIO 3: USER-BASED SHARING ---")

        # 1. Verify Member CANNOT access resources initially
        print("[Step] Verifying Member has NO access initially...")
        # Try to get KB status
        resp = await client.get(f"{API_BASE_URL}/kb/{kb_id}/status", headers=headers_member)
        assert resp.status_code in [403, 404], f"Member should not access KB yet. Got {resp.status_code}"
        
        # Try to get MCP connection (mock checking list or specific item if endpoint exists)
        # Accessing specific MCP requires ID. If list is used, it might just be empty.
        # Check specific items usually 403/404.
        
        print("✓ Initial access denied (correct)")

        # 2. Share KB with Member (USER scope)
        print("[Step] Sharing KB with Member (User Scope)...")
        share_payload = {
            "user_id": user_member["id"],
            "access_level": "viewer"
        }
        resp = await client.post(
            f"{API_BASE_URL}/access/knowledge_base/{kb_id}/share",
            json=share_payload,
            headers=headers_owner
        )
        assert resp.status_code == 200, f"Share KB failed: {resp.text}"
        print("✓ KB Shared")

        # 3. Verify Member CAN access KB
        print("[Step] Verifying Member CAN access KB...")
        # Member needs to switch to Owner's Tenant Context
        headers_member_context = headers_member.copy()
        headers_member_context["X-Tenant-ID"] = tenant_id

        resp = await client.get(f"{API_BASE_URL}/kb/{kb_id}/status", headers=headers_member_context)
        assert resp.status_code == 200, f"Member cannot access KB after sharing: {resp.text}"
        print("✓ Member accessed KB successfully")

        # 4. Share MCP with Member (USER scope)
        print("[Step] Sharing MCP with Member (User Scope)...")
        resp = await client.post(
            f"{API_BASE_URL}/access/mcp_connection/{mcp_id}/share",
            json=share_payload, # reusing payload with user_id
            headers=headers_owner
        )
        assert resp.status_code == 200, f"Share MCP failed: {resp.text}"
        print("✓ MCP Shared")
        
        # 5. Verify Member CAN access MCP (using sync endpoint as proxy for 'use' access or update if allowed)
        # Viewer mostly can just 'see' it in list or use it. Let's try to list and find it.
        print("[Step] Verifying Member can see MCP in list...")
        # Member lists resources IN THE SHARED TENANT context
        resp = await client.get(f"{API_BASE_URL}/resources/mcp", headers=headers_member_context)
        assert resp.status_code == 200
        mcp_list = resp.json()
        found = any(m["id"] == mcp_id for m in mcp_list)
        assert found, "Shared MCP not found in member's list"
        print("✓ Member sees MCP in list")


        # ==========================================
        # SCENARIO 4: ROLE-BASED SHARING
        # ==========================================
        print("\n--- SCENARIO 4: ROLE-BASED SHARING ---")

        # 1. Create Secondary Resources
        print("[Step] Creating secondary locked resources...")
        # Upload KB 2
        files2 = {'file': ('secret_plans.txt', b"Top secret content", 'text/plain')}
        resp = await client.post(f"{API_BASE_URL}/kb/upload", files=files2, headers={"Authorization": headers_owner["Authorization"]})
        kb2_id = resp.json()["id"]
        
        # Create MCP 2
        resp = await client.post(f"{API_BASE_URL}/resources/mcp", json={"name": "Admin Only MCP", "server_url": "http://x", "protocol": "sse"}, headers=headers_owner)
        mcp2_id = resp.json()["id"]
        print(f"✓ Created Locked Resources: KB2({kb2_id}), MCP2({mcp2_id})")

        # 2. Share KB2 with 'member' role (Member has this role)
        print("[Step] Sharing KB2 with tenant role 'member'...")
        role_share_payload = {
            "tenant_role": "member",
            "access_level": "viewer"
        }
        resp = await client.post(
            f"{API_BASE_URL}/access/knowledge_base/{kb2_id}/share",
            json=role_share_payload,
            headers=headers_owner
        )
        assert resp.status_code == 200, f"Role share failed: {resp.text}"
        
        # Verify access
        resp = await client.get(f"{API_BASE_URL}/kb/{kb2_id}/status", headers=headers_member_context)
        assert resp.status_code == 200, "Member should access KB2 via role"
        print("✓ Member accessed KB2 via 'member' role")

        # 3. Share MCP2 with 'admin' role (Member does NOT have this role)
        print("[Step] Sharing MCP2 with tenant role 'admin'...")
        admin_share_payload = {
            "tenant_role": "admin",
            "access_level": "editor"
        }
        resp = await client.post(
            f"{API_BASE_URL}/access/mcp_connection/{mcp2_id}/share",
            json=admin_share_payload,
            headers=headers_owner
        )
        assert resp.status_code == 200
        
        # Verify NO access
        print("[Step] Verifying Member has NO access to MCP2...")
        resp = await client.get(f"{API_BASE_URL}/resources/mcp", headers=headers_member_context)
        mcp_list = resp.json()
        found = any(m["id"] == mcp2_id for m in mcp_list)
        assert not found, "Member should NOT see MCP2 yet"
        print("✓ Access denied correctly (Member is not Admin)")

        # 4. Upgrade Member to Admin
        print("[Step] Upgrading Member to 'admin'...")
        resp = await client.put(
            f"{API_BASE_URL}/tenants/{tenant_id}/members/{user_member['id']}",
            json={"role": "admin"},
            headers=headers_owner
        )
        assert resp.status_code == 200
        print("✓ Member promoted to Admin")

        # 5. Verify Access Granted
        print("[Step] Verifying Admin Member now has access to MCP2...")
        # Need to refresh token implies usually no, but here headers are just dummy sso.
        # But RBAC check hits DB, so it should be immediate.
        resp = await client.get(f"{API_BASE_URL}/resources/mcp", headers=headers_member_context)
        mcp_list = resp.json()
        found = any(m["id"] == mcp2_id for m in mcp_list)
        assert found, "New Admin should see MCP2 now"
        print("✓ Access granted via role upgrade")

        print("\n" + "="*80)
        print("🎉 ALL ORGANIZATION E2E TESTS PASSED!")
        print("="*80)

if __name__ == "__main__":
    asyncio.run(test_organization_e2e())
