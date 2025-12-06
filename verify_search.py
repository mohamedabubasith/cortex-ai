import requests
import os

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "test_kb_user@example.com"
PASSWORD = "password123"

def login():
    response = requests.post(f"{BASE_URL}/auth/token", data={"username": EMAIL, "password": PASSWORD})
    if response.status_code == 200:
        return response.json()["access_token"]
    print("Login failed")
    return None

def main():
    token = login()
    if not token: return

    headers = {"Authorization": f"Bearer {token}"}
    
    # List projects to get ID
    response = requests.get(f"{BASE_URL}/projects/", headers=headers)
    projects = response.json()
    if not projects:
        print("No projects found. Run verify_kb_ops.py first.")
        return
        
    project_id = projects[0]["id"]
    print(f"Using Project: {project_id}")

    # Test Search Endpoint
    print("\nTesting Search Endpoint...")
    query = "test document"
    response = requests.post(f"{BASE_URL}/projects/{project_id}/kb/search", json={"query": query}, headers=headers)
    if response.status_code == 200:
        print("Search Results:", response.json())
    else:
        print("Search Failed:", response.text)

if __name__ == "__main__":
    main()
