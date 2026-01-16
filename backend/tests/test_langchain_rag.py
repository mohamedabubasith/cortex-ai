import asyncio
import httpx
import uuid
import os
import time

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

async def get_auth_token(client, email, password):
    resp = await client.post(
        f"{API_BASE_URL}/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.text}")
    return resp.json()["access_token"]

async def create_dummy_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)
    return filename

async def wait_for_server(client):
    print("Waiting for server to be ready...")
    health_url = API_BASE_URL.replace("/api/v1", "") + "/health"
    for _ in range(120): # Wait up to 120 seconds for MiniLM model download
        try:
            resp = await client.get(health_url)
            if resp.status_code == 200:
                print("Server is ready!")
                return
        except Exception:
            pass
        await asyncio.sleep(1)
    raise Exception("Server not ready after 120 seconds")

async def test_langchain_rag_flow():
    async with httpx.AsyncClient(timeout=30.0) as client:
        await wait_for_server(client)
        
        # 1. Setup User A
        unique_id = str(uuid.uuid4())[:8]
        email = f"rag_user_{unique_id}@example.com"
        password = "password123"
        
        # Register (triggers JIT tenant)
        await client.post(f"{API_BASE_URL}/auth/register", json={
            "email": email, "password": password, "full_name": "RAG User"
        })
        token_a = await get_auth_token(client, email, password)
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        print(f"✓ User A created: {email} (Token acquired)")

        # 2. Upload File
        filename = f"test_doc_{unique_id}.txt"
        file_content = f"This is a secret document for Tenant {unique_id}. The magic code is 42."
        await create_dummy_file(filename, file_content)
        
        try:
            with open(filename, "rb") as f:
                files = {"file": (filename, f, "text/plain")}
                # Use correct endpoint: /kb/upload
                resp = await client.post(f"{API_BASE_URL}/kb/upload", headers=headers_a, files=files)
                
            if resp.status_code != 200:
                print(f"Upload failed: {resp.text}")
                return
            
            kb_id = resp.json()["id"]
            print(f"✓ File uploaded: {kb_id}")
            
            # 3. Wait for Indexing
            print("Waiting for indexing...")
            for _ in range(10):
                # Use correct endpoint: /kb/{id}/status
                resp = await client.get(f"{API_BASE_URL}/kb/{kb_id}/status", headers=headers_a)
                status = resp.json()["status"]
                print(f"Status: {status}")
                if status == "indexed":
                    break
                if status == "failed":
                    raise Exception("Indexing failed")
                await asyncio.sleep(1)
            
            if status != "indexed":
                raise Exception("Indexing timed out")
            print("✓ Indexing complete")
            
            # 4. Query (User A)
            query_payload = {"query": "What is the magic code?", "llm_config_id": "dummy_for_schema"} 
            
            resp = await client.post(
                f"{API_BASE_URL}/kb/{kb_id}/query", 
                headers=headers_a, 
                json={"query": "What is the magic code?", "llm_config_id": "ignored"}
            )
            
            if resp.status_code != 200:
                 print(f"Query failed: {resp.text}")
                 raise Exception("Query failed")
            
            results = resp.json()["results"]
            print(f"Query Results: {results}")
            
            # Verify Content
            found = any("magic code is 42" in r["content"] for r in results)
            assert found, "Magic code not found in search results"
            print("✓ Query verification passed (User A)")
            
            # 5. Isolation Test (User B)
            unique_id_b = str(uuid.uuid4())[:8]
            email_b = f"rag_attacker_{unique_id_b}@example.com"
            await client.post(f"{API_BASE_URL}/auth/register", json={
                "email": email_b, "password": password, "full_name": "Attacker"
            })
            token_b = await get_auth_token(client, email_b, password)
            headers_b = {"Authorization": f"Bearer {token_b}"}
            
            print("Testing Isolation (User B accessing User A's KB)...")
            resp = await client.post(
                f"{API_BASE_URL}/kb/{kb_id}/query", 
                headers=headers_b, 
                json={"query": "What is the magic code?", "llm_config_id": "ignored"}
            )
            
            # Expecting 400 Access Denied, 400 KB not found, or 404
            if resp.status_code == 400 and ("Access Denied" in resp.text or "KB not found" in resp.text):
                print("✓ Isolation Verified: User B denied access.")
            elif resp.status_code == 404:
                print("✓ Isolation Verified: KB not found for User B.") 
            else:
                print(f"❌ Isolation Failed: {resp.status_code} {resp.text}")
                raise Exception("Isolation Failed")

        finally:
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_langchain_rag_flow())
