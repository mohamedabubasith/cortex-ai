import httpx
import uuid
import asyncio
import os
import json

# Base URL for the running API
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

async def get_user_headers(email: str):
    token = f"dummy_sso_{email.replace('@', '_at_')}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # JIT Provisioning trigger
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(f"{API_BASE_URL}/auth/me", headers=headers)
        if resp.status_code != 200:
            print(f"[Error] JIT Auth failed for {email}: {resp.status_code} - {resp.text}")
        user_data = resp.json()
        return headers, user_data

async def test_agent_sharing_flow():
    """
    Test flow:
    1. User A creates an Agent.
    2. User B cannot see it.
    3. User A shares Agent with User B (viewer).
    4. User B can see but not delete (403).
    5. User A shares Agent with User B (admin).
    6. User B can delete (or perform admin task).
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        # SETUP
        email_a = f"owner_{uuid.uuid4().hex[:4]}@example.com"
        email_b = f"collaborator_{uuid.uuid4().hex[:4]}@example.com"
        
        print(f"\n[RBAC Test] Setting up Users...")
        headers_a, user_a = await get_user_headers(email_a)
        headers_b, user_b = await get_user_headers(email_b)
        
        user_b_id = user_b["id"]
        print(f"[RBAC Test] User A ID: {user_a['id']}")
        print(f"[RBAC Test] User B ID: {user_b_id}")

        # 1. User A creates an Agent
        print("\n[Step 1] User A creates an Agent...")
        agent_data = {
            "name": "RBAC Test Agent",
            "description": "Agent to test sharing",
            "system_prompt": "You are a helpful assistant."
        }
        resp = await client.post(f"{API_BASE_URL}/agents", json=agent_data, headers=headers_a)
        if resp.status_code != 200:
             print(f"[Error] Agent creation failed: {resp.status_code} - {resp.text}")
        assert resp.status_code == 200
        agent = resp.json()
        agent_id = agent["id"]
        print(f"✓ Agent created: {agent_id}")

        # 2. User B tries to see User A's Agent (should fail or not be in list)
        print("\n[Step 2] User B attempts to access Agent (expected failure)...")
        resp = await client.get(f"{API_BASE_URL}/agents/{agent_id}", headers=headers_b)
        # Should be 403 or 404 since it's personal
        assert resp.status_code in [403, 404], f"User B should not have access. Got {resp.status_code} - {resp.text}"
        print(f"✓ Access denied for User B (status {resp.status_code})")

        # 3. User A shares Agent with User B (VIEWER)
        print(f"\n[Step 3] User A shares Agent with User B as VIEWER...")
        share_data = {
            "user_id": user_b_id,
            "access_level": "viewer"
        }
        resp = await client.post(f"{API_BASE_URL}/access/agent/{agent_id}/share", json=share_data, headers=headers_a)
        if resp.status_code != 200:
            print(f"[Error] Share failed: {resp.status_code} - {resp.text}")
        assert resp.status_code == 200
        print("✓ Resource shared successfully")

        # 4. User B tries to see Agent again (should succeed)
        print("\n[Step 4] User B attempts to access shared Agent...")
        resp = await client.get(f"{API_BASE_URL}/agents/{agent_id}", headers=headers_b)
        if resp.status_code != 200:
            print(f"[Error] Get agent failed: {resp.status_code} - {resp.text}")
        assert resp.status_code == 200
        assert resp.json()["name"] == agent["name"]
        print("✓ User B can now see the Agent")

        # 5. User B tries to DELETE Agent (should fail - forbidden)
        print("\n[Step 5] User B attempts to DELETE shared Agent (expected 403)...")
        resp = await client.delete(f"{API_BASE_URL}/agents/{agent_id}", headers=headers_b)
        assert resp.status_code == 403
        print("✓ Permission Denied (403) as expected for VIEWER")

        # 6. User A upgrades User B to ADMIN
        print(f"\n[Step 6] User A upgrades User B to ADMIN...")
        share_data["access_level"] = "admin"
        resp = await client.post(f"{API_BASE_URL}/access/agent/{agent_id}/share", json=share_data, headers=headers_a)
        if resp.status_code != 200:
            print(f"[Error] Upgrade failed: {resp.status_code} - {resp.text}")
        assert resp.status_code == 200
        print("✓ Access upgraded to ADMIN")

        # 7. User B tries to DELETE Agent again (should succeed)
        print("\n[Step 7] User B attempts to DELETE shared Agent as ADMIN...")
        resp = await client.delete(f"{API_BASE_URL}/agents/{agent_id}", headers=headers_b)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("✓ User B successfully deleted the Agent as ADMIN")

        print("\n🎉 RBAC Sharing Test Passed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_agent_sharing_flow())
