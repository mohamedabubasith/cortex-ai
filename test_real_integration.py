import requests
import os
import sys

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "integration_test@example.com"
PASSWORD = "password123"

def login_or_register():
    response = requests.post(f"{BASE_URL}/auth/token", data={"username": EMAIL, "password": PASSWORD})
    if response.status_code == 200:
        return response.json()["access_token"]
    
    response = requests.post(f"{BASE_URL}/auth/register", json={"email": EMAIL, "password": PASSWORD, "full_name": "Integration Tester"})
    if response.status_code == 200:
        response = requests.post(f"{BASE_URL}/auth/token", data={"username": EMAIL, "password": PASSWORD})
        return response.json()["access_token"]
    return None

def main():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        print("Error: NVIDIA_API_KEY environment variable is required.")
        print("Usage: NVIDIA_API_KEY=nvapi-... python3 test_real_integration.py")
        sys.exit(1)

    token = login_or_register()
    if not token:
        print("Authentication failed.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project with NVIDIA Config
    print("\n1. Creating Project with NVIDIA Config...")
    project_data = {
        "name": "NVIDIA RAG Project",
        "description": "Testing with NVIDIA NIM",
        "llm_base_url": "https://integrate.api.nvidia.com/v1",
        "llm_api_key": api_key,
        "llm_model": "meta/llama-3.1-405b-instruct" 
    }
    response = requests.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    if response.status_code != 200:
        print(f"Failed to create project: {response.text}")
        return
        
    project = response.json()
    project_id = project["id"]
    print(f"Project created: {project_id}")

    # 2. Upload File
    print("\n2. Uploading File (Real Indexing)...")
    filename = "nvidia_test.txt"
    with open(filename, "w") as f:
        f.write("NVIDIA is a technology company known for its GPUs. Jensen Huang is the CEO of NVIDIA.")
    
    with open(filename, "rb") as f:
        files = {"file": (filename, f, "text/plain")}
        response = requests.post(f"{BASE_URL}/projects/{project_id}/kb/upload", headers=headers, files=files)
    
    print("Upload Response:", response.json())
    
    # 3. Test Search
    print("\n3. Testing Search (Real Retrieval)...")
    query = "Who is the CEO of NVIDIA?"
    response = requests.post(f"{BASE_URL}/projects/{project_id}/kb/search", json={"query": query}, headers=headers)
    print("Search Results:", response.json())

    # 4. Cleanup
    os.remove(filename)

if __name__ == "__main__":
    main()
