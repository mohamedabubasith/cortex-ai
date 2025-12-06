import asyncio
import httpx
import os

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "testuser@example.com"
PASSWORD = "password123"

async def run_test():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("--- 1. Authentication ---")
        # 1. Register
        print(f"Registering user {EMAIL}...")
        resp = await client.post("/auth/register", json={
            "email": EMAIL,
            "password": PASSWORD,
            "full_name": "Test User"
        })
        if resp.status_code == 400 and "already registered" in resp.text:
            print("User already exists, proceeding to login.")
        elif resp.status_code != 200:
            print(f"Registration failed: {resp.text}")
            return
        else:
            print("Registration successful.")

        # 2. Login
        print("Logging in...")
        resp = await client.post("/auth/token", data={
            "username": EMAIL,
            "password": PASSWORD
        })
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login successful. Token acquired.")

        print("\n--- 2. Project Management ---")
        # 3. Create Project
        print("Creating project 'Backend Test Project'...")
        resp = await client.post("/projects/", json={
            "name": "Backend Test Project",
            "description": "Project for automated backend testing",
            "llm_model": "gpt-4",
            "is_public": True
        }, headers=headers)
        
        if resp.status_code != 200:
            print(f"Create project failed: {resp.text}")
            return
            
        project = resp.json()
        project_id = project["id"]
        print(f"Project created. ID: {project_id}")

        print("\n--- 3. Database Integration ---")
        # 4. Create DB Connection (Connect to self)
        print("Configuring Database Connection (PostgreSQL)...")
        resp = await client.post(f"/projects/{project_id}/databases/", json={
            "name": "Local Chatbot DB",
            "type": "postgres",
            "host": "localhost",
            "port": 5432,
            "username": "postgres",
            "password": "password",
            "database_name": "chatbot_db",
            "ssl_mode": "prefer"
        }, headers=headers)
        
        if resp.status_code != 200:
            print(f"Create DB connection failed: {resp.text}")
        else:
            conn = resp.json()
            conn_id = conn["id"]
            print(f"DB Connection created. ID: {conn_id}")
            
            # 5. Test Connection
            print("Testing DB Connection...")
            resp = await client.post(f"/projects/{project_id}/databases/{conn_id}/test", headers=headers)
            print(f"Test Result: {resp.json()}")
            
            # 6. Execute Query
            print("Executing Query 'SELECT count(*) FROM users'...")
            resp = await client.post(f"/projects/{project_id}/databases/{conn_id}/execute", json={
                "query": "SELECT count(*) FROM users"
            }, headers=headers)
            print(f"Query Result: {resp.json()}")

        print("\n--- 4. Knowledge Base ---")
        # 7. Upload File
        print("Uploading dummy KB file...")
        # Create dummy file
        with open("test_kb.txt", "w") as f:
            f.write("This is a test document for the knowledge base.")
            
        files = {"file": ("test_kb.txt", open("test_kb.txt", "rb"), "text/plain")}
        resp = await client.post(f"/projects/{project_id}/kb/upload", files=files, headers=headers)
        
        if resp.status_code != 200:
            print(f"Upload failed: {resp.text}")
        else:
            print(f"Upload successful: {resp.json()}")
            # Clean up local dummy
            os.remove("test_kb.txt")

        print("\n--- 5. Project Cleanup ---")
        # 8. Delete Project (Reset)
        print("Resetting Project (Delete)...")
        resp = await client.delete(f"/projects/{project_id}", headers=headers)
        print(f"Delete Result: {resp.json()}")
        
        # Verify Project still exists but is empty
        resp = await client.get(f"/projects/{project_id}", headers=headers)
        if resp.status_code == 200:
            p = resp.json()
            if p["llm_model"] is None:
                print("Verification Successful: Project exists but config is reset.")
            else:
                print("Verification Failed: Project config was not reset.")
        else:
            print("Verification Failed: Project was deleted entirely.")

if __name__ == "__main__":
    asyncio.run(run_test())
