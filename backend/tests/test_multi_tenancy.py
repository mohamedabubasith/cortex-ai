import httpx
import uuid
import asyncio
import os

# Base URL for the running API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

async def test_jit_tenant_provisioning_flow():
    """
    Test the complete flow of:
    1. Authenticating a brand new user via SSO (Dummy Token).
    2. Verifying JIT provisioning of the User.
    3. Verifying JIT provisioning of the Default Tenant.
    4. Verifying User is assigned as 'owner' of the Tenant.
    """
    async with httpx.AsyncClient() as client:
        # 1. Generate unique user email to ensure JIT triggers
        unique_id = str(uuid.uuid4())[:8]
        email = f"test_user_{unique_id}@example.com"
        # Dummy token format: dummy_sso_email_at_domain
        token = f"dummy_sso_{email.replace('@', '_at_')}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print(f"\n[Test] Attempting SSO login with new user: {email}")
        
        # 2. Call /me endpoint
        response = await client.get(f"{API_BASE_URL}/auth/me", headers=headers)
        
        if response.status_code != 200:
            print(f"[Error] Response: {response.text}")
            
        assert response.status_code == 200, "SSO Login failed"
        
        user_data = response.json()
        print(f"[Test] User created: {user_data['id']}")
        
        # 3. Verify User fields
        assert user_data["email"] == email
        assert user_data["is_active"] == True
        
        # 4. Verify Tenant Provisioning
        # The schema should now include 'tenant_memberships'
        assert "tenant_memberships" in user_data, "Response missing 'tenant_memberships'"
        memberships = user_data["tenant_memberships"]
        
        assert isinstance(memberships, list)
        assert len(memberships) > 0, "No tenant created for new user"
        
        # 5. Verify Membership Details
        primary_membership = memberships[0]
        assert primary_membership["role"] == "owner", "User is not owner of their new tenant"
        assert "tenant" in primary_membership
        
        tenant = primary_membership["tenant"]
        print(f"[Test] Tenant created: {tenant['name']} ({tenant['id']})")
        
        # Verify tenant naming convention
        expected_name_part = f"test_user_{unique_id}"
        assert expected_name_part in tenant["name"] or expected_name_part in tenant["slug"]
        
        print("✓ JIT Tenant Provisioning Verified Successfully")
        return user_data, token

async def test_rls_isolation():
    """
    Test that resources are strictly isolated between tenants.
    User B should NOT see User A's resources.
    """
    async with httpx.AsyncClient() as client:
        # 1. Create User A and Resource
        print("\n[Test] Setting up User A (Tenant A)...")
        user_a, token_a = await test_jit_tenant_provisioning_flow()
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        # Create a DB Connection as User A
        db_data = {
            "name": "User A DB",
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
            "username": "admin",
            "password": "password",
            "database_name": "mydb"
        }
        resp = await client.post(f"{API_BASE_URL}/resources/databases", json=db_data, headers=headers_a)
        assert resp.status_code == 200
        resource_id = resp.json()["id"]
        print(f"[Test] User A created resource: {resource_id}")
        
        # 2. Create User B (Tenant B)
        print("[Test] Setting up User B (Tenant B)...")
        # Generate distinct user
        unique_id_b = str(uuid.uuid4())[:8]
        token_b = f"dummy_sso_test_user_{unique_id_b}_at_example.com"
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        # Trigger JIT for B
        await client.get(f"{API_BASE_URL}/auth/me", headers=headers_b)
        
        # 3. User B tries to access User A's resource
        print(f"[Test] User B attempting to access User A's resource ({resource_id})...")
        
        # Attempt GET (Direct ID)
        resp_get = await client.get(f"{API_BASE_URL}/resources/databases", headers=headers_b)
        params_list = resp_get.json()
        assert len(params_list) == 0, "User B should see empty list (Leakage detected!)"
        
        # Attempt DELETE (Targeted ID)
        resp_del = await client.delete(f"{API_BASE_URL}/resources/databases/{resource_id}", headers=headers_b)
        
        if resp_del.status_code == 404:
             print("✓ Isolation Verified: User B received 404 for User A's resource.")
        else:
             print(f"❌ Isolation Failed: User B received {resp_del.status_code}")
             raise Exception("RLS Isolation Failed")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_rls_isolation())
