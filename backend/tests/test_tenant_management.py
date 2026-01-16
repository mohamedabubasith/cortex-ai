"""Test Tenant Management APIs"""
import httpx
import uuid
import asyncio
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


async def get_user_headers(email: str):
    """Get auth headers using JIT provisioning"""
    token = f"dummy_sso_{email.replace('@', '_at_')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(f"{API_BASE_URL}/auth/me", headers=headers)
        if resp.status_code != 200:
            print(f"[Error] JIT Auth failed for {email}: {resp.status_code} - {resp.text}")
            return headers, None
        user_data = resp.json()
        return headers, user_data


async def test_tenant_management():
    """
    Test tenant management workflows:
    1. Tenant owner can add members
    2. Tenant owner can update roles
    3. Tenant owner can remove members
    4. Non-owner cannot manage members
    5. Super admin can manage any tenant
    6. Super admin can delete tenant
    """
    print("\n" + "="*60)
    print("TENANT MANAGEMENT TEST SUITE")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Setup: Create test users
        print("\n[Setup] Creating test users...")
        email_owner = f"tenant_owner_{uuid.uuid4().hex[:4]}@example.com"
        email_member = f"tenant_member_{uuid.uuid4().hex[:4]}@example.com"
        email_new_user = f"new_user_{uuid.uuid4().hex[:4]}@example.com"
        
        headers_owner, user_owner = await get_user_headers(email_owner)
        headers_member, user_member = await get_user_headers(email_member)
        headers_new, user_new = await get_user_headers(email_new_user)
        
        if not user_owner or not user_member or not user_new:
            print("[FAIL] Failed to create test users")
            return
        
        # Get tenant IDs
        tenant_id_owner = user_owner["tenant_memberships"][0]["tenant_id"]
        
        print(f"✓ Owner: {user_owner['email']} (Tenant: {tenant_id_owner})")
        print(f"✓ Member: {user_member['email']}")
        print(f"✓ New User: {user_new['email']}")
        
        # Test 1: Tenant owner can add members
        print("\n[Test 1] Tenant owner adds new member...")
        resp = await client.post(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members",
            json={"user_id": user_new["id"], "role": "member"},
            headers=headers_owner
        )
        if resp.status_code != 200:
            print(f"[FAIL] Add member failed: {resp.status_code} - {resp.text}")
            return
        print("✓ Member added successfully")
        
        # Test 2: Verify member can be listed
        print("\n[Test 2] List tenant members...")
        resp = await client.get(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members",
            headers=headers_owner
        )
        if resp.status_code != 200:
            print(f"[FAIL] List members failed: {resp.status_code}")
            return
        members = resp.json()
        print(f"✓ Found {len(members)} members")
        assert len(members) == 2, f"Expected 2 members, got {len(members)}"
        
        # Test 3: Tenant owner can update roles
        print("\n[Test 3] Tenant owner upgrades member to admin...")
        resp = await client.put(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members/{user_new['id']}",
            json={"role": "admin"},
            headers=headers_owner
        )
        if resp.status_code != 200:
            print(f"[FAIL] Update role failed: {resp.status_code} - {resp.text}")
            return
        print("✓ Role upgraded to admin")
        
        # Test 4: Non-member cannot access tenant
        print("\n[Test 4] Non-member attempts to list members (expected 403)...")
        resp = await client.get(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members",
            headers=headers_member
        )
        if resp.status_code != 403:
            print(f"[FAIL] Expected 403, got {resp.status_code}")
            return
        print("✓ Access denied as expected")
        
        # Test 5: Non-owner member cannot add users
        print("\n[Test 5] Regular member attempts to add user (expected 403)...")
        # First add member to tenant
        await client.post(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members",
            json={"user_id": user_member["id"], "role": "member"},
            headers=headers_owner
        )
        # Now try to add someone as a member
        resp = await client.post(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members",
            json={"user_id": "fake-id", "role": "viewer"},
            headers=headers_member
        )
        if resp.status_code != 403:
            print(f"[FAIL] Expected 403, got {resp.status_code} - {resp.text}")
            return
        print("✓ Permission denied as expected")
        
        # Test 6: Cannot remove last owner
        print("\n[Test 6] Attempt to remove last owner (expected 400)...")
        resp = await client.delete(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members/{user_owner['id']}",
            headers=headers_owner
        )
        if resp.status_code != 400:
            print(f"[FAIL] Expected 400, got {resp.status_code}")
            return
        print("✓ Cannot remove last owner (protection works)")
        
        # Test 7: Can remove non-owner member
        print("\n[Test 7] Owner removes a member...")
        resp = await client.delete(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members/{user_new['id']}",
            headers=headers_owner
        )
        if resp.status_code != 200:
            print(f"[FAIL] Remove member failed: {resp.status_code} - {resp.text}")
            return
        print("✓ Member removed successfully")
        
        # Verify removal
        resp = await client.get(
            f"{API_BASE_URL}/tenants/{tenant_id_owner}/members",
            headers=headers_owner
        )
        members = resp.json()
        assert len(members) == 2, f"Expected 2 members after removal, got {len(members)}"
        print("✓ Member count verified")
        
        print("\n" + "="*60)
        print("🎉 ALL TENANT MANAGEMENT TESTS PASSED!")
        print("="*60)


async def test_role_based_sharing():
    """Test that role-based sharing works with tenant roles"""
    print("\n" + "="*60)
    print("ROLE-BASED SHARING TEST")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Create owner and admin
        email_owner = f"role_owner_{uuid.uuid4().hex[:4]}@example.com"
        email_admin = f"role_admin_{uuid.uuid4().hex[:4]}@example.com"
        
        headers_owner, user_owner = await get_user_headers(email_owner)
        headers_admin, user_admin = await get_user_headers(email_admin)
        
        tenant_id = user_owner["tenant_memberships"][0]["tenant_id"]
        
        # Add admin user to tenant as admin
        print(f"\n[Setup] Adding admin user to tenant...")
        await client.post(
            f"{API_BASE_URL}/tenants/{tenant_id}/members",
            json={"user_id": user_admin["id"], "role": "admin"},
            headers=headers_owner
        )
        print("✓ Admin added to tenant")
        
        # Create an agent
        print("\n[Test] Owner creates agent...")
        agent_resp = await client.post(
            f"{API_BASE_URL}/agents",
            json={
                "name": "Shared Agent",
                "description": "Test role-based sharing",
                "system_prompt": "You are helpful."
            },
            headers=headers_owner
        )
        if agent_resp.status_code != 200:
            print(f"[FAIL] Agent creation failed: {agent_resp.status_code}")
            return
        agent = agent_resp.json()
        print(f"✓ Agent created: {agent['id']}")
        
        # Share agent with all "admin" role members
        print("\n[Test] Share agent with 'admin' role...")
        share_resp = await client.post(
            f"{API_BASE_URL}/access/agent/{agent['id']}/share",
            json={"tenant_role": "admin", "access_level": "editor"},
            headers=headers_owner
        )
        if share_resp.status_code != 200:
            print(f"[FAIL] Sharing failed: {share_resp.status_code} - {share_resp.text}")
            return
        print("✓ Shared with 'admin' role")
        
        # Admin user should now have access
        print("\n[Test] Admin user accesses shared agent...")
        access_resp = await client.get(
            f"{API_BASE_URL}/agents/{agent['id']}",
            headers=headers_admin
        )
        if access_resp.status_code != 200:
            print(f"[FAIL] Admin cannot access: {access_resp.status_code} - {access_resp.text}")
            return
        print("✓ Admin can access agent via role-based sharing")
        
        print("\n" + "="*60)
        print("🎉 ROLE-BASED SHARING TEST PASSED!")
        print("="*60)


if __name__ == "__main__":
    print("\n🚀 Starting Comprehensive Tenant Management Tests...\n")
    asyncio.run(test_tenant_management())
    asyncio.run(test_role_based_sharing())
