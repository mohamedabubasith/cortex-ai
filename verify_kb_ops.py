import requests
import os

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "test_kb_user@example.com"
PASSWORD = "password123"

def login_or_register():
    # Try login
    print("Attempting login...")
    response = requests.post(f"{BASE_URL}/auth/token", data={"username": EMAIL, "password": PASSWORD})
    if response.status_code == 200:
        return response.json()["access_token"]
    
    # Register if login fails
    print("Login failed, registering...")
    response = requests.post(f"{BASE_URL}/auth/register", json={"email": EMAIL, "password": PASSWORD, "full_name": "Test User"})
    if response.status_code == 200:
        # Login again
        response = requests.post(f"{BASE_URL}/auth/token", data={"username": EMAIL, "password": PASSWORD})
        return response.json()["access_token"]
    else:
        print(f"Registration failed: {response.text}")
        return None

def main():
    token = login_or_register()
    if not token:
        print("Could not authenticate.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project
    print("\n1. Creating Project...")
    project_data = {
        "name": "KB Test Project",
        "description": "Testing KB operations",
        "is_public": False
    }
    response = requests.post(f"{BASE_URL}/projects/", json=project_data, headers=headers)
    if response.status_code != 200:
        print(f"Failed to create project: {response.text}")
        return
    project = response.json()
    project_id = project["id"]
    print(f"Project created: {project_id}")

    # 2. Upload File
    print("\n2. Uploading File...")
    filename = "test_doc.txt"
    with open(filename, "w") as f:
        f.write("This is a test document for the knowledge base.")
    
    with open(filename, "rb") as f:
        files = {"file": (filename, f, "text/plain")}
        response = requests.post(f"{BASE_URL}/projects/{project_id}/kb/upload", headers=headers, files=files)
    
    if response.status_code == 200:
        print("Upload successful.")
    else:
        print(f"Upload failed: {response.text}")
        # Clean up local file
        os.remove(filename)
        return

    # 3. Verify Indexing (Check Project Details)
    print("\n3. Verifying Indexing...")
    response = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
    project_details = response.json()
    kb_files = project_details.get("knowledge_bases", [])
    
    if not kb_files:
        print("No KB files found in project details.")
    else:
        print(f"Found {len(kb_files)} KB files.")
        kb_entry = kb_files[0]
        print(f"File: {kb_entry['filename']}, Status: {kb_entry['status']}")
        kb_id = kb_entry["id"]

        # 4. Delete File
        print(f"\n4. Deleting File {kb_id}...")
        response = requests.delete(f"{BASE_URL}/projects/{project_id}/kb/{kb_id}", headers=headers)
        if response.status_code == 200:
            print("Delete successful.")
        else:
            print(f"Delete failed: {response.text}")

        # 5. Verify Deletion
        print("\n5. Verifying Deletion...")
        response = requests.get(f"{BASE_URL}/projects/{project_id}", headers=headers)
        project_details = response.json()
        kb_files = project_details.get("knowledge_bases", [])
        if not kb_files:
            print("Verification successful: No KB files found.")
        else:
            print(f"Verification failed: Found {len(kb_files)} KB files.")

    # Clean up local file
    if os.path.exists(filename):
        os.remove(filename)

if __name__ == "__main__":
    main()
