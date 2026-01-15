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
        # e.g., "test_user_xyz's Workspace" (from full_name default) or email part
        # Logic matches: user.email.split('@')[0] if full_name is derived from email
        assert expected_name_part in tenant["name"] or expected_name_part in tenant["slug"]
        
        print("✓ JIT Tenant Provisioning Verified Successfully")

if __name__ == "__main__":
    # Allow running directly with python
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_jit_tenant_provisioning_flow())
