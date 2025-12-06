"""
Production-Grade Knowledge Base API Test Suite

Tests all Cognee/Knowledge Base APIs:
- Upload
- Status tracking
- Query/Search
- Delete

Run this script to verify all KB functionality.
"""

import requests
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class KnowledgeBaseAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.llm_config_id = None
        self.kb_id = None
        
    def login(self):
        """Login and get access token."""
        print("\n1️⃣  Testing Login...")
        response = requests.post(
            f"{self.base_url}/auth/login",
            data={
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def create_llm_config(self):
        """Create or get LLM config for testing."""
        print("\n2️⃣  Creating/Getting LLM Configuration...")
        
        # First check if we have any configs
        response = requests.get(
            f"{self.base_url}/resources/llm",
            headers=self.get_headers()
        )
        
        if response.status_code == 200 and response.json():
            self.llm_config_id = response.json()[0]["id"]
            print(f"✅ Using existing LLM config: {self.llm_config_id}")
            return True
        
        # Create new config
        response = requests.post(
            f"{self.base_url}/resources/llm",
            headers=self.get_headers(),
            json={
                "name": "Test LLM",
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "sk-test-key",
                "base_url": None
            }
        )
        
        if response.status_code == 200:
            self.llm_config_id = response.json()["id"]
            print(f"✅ Created LLM config: {self.llm_config_id}")
            return True
        else:
            print(f"❌ Failed to create LLM config: {response.text}")
            return False
    
    def upload_document(self, file_path):
        """Upload a document to knowledge base."""
        print(f"\n3️⃣  Uploading document: {file_path}...")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            params = {'llm_config_id': self.llm_config_id}
            
            response = requests.post(
                f"{self.base_url}/resources/kb/upload",
                headers=self.get_headers(),
                files=files,
                params=params
            )
        
        if response.status_code == 200:
            data = response.json()
            self.kb_id = data["id"]
            print(f"✅ Upload successful")
            print(f"   - ID: {self.kb_id}")
            print(f"   - Filename: {data['filename']}")
            print(f"   - Status: {data['status']}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
    
    def check_status(self):
        """Check document processing status."""
        print(f"\n4️⃣  Checking processing status...")
        
        max_attempts = 10
        for attempt in range(max_attempts):
            response = requests.get(
                f"{self.base_url}/resources/kb/{self.kb_id}/status",
                headers=self.get_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                cognee_status = data.get('cognee_status', 'unknown')
                
                print(f"   Attempt {attempt + 1}/{max_attempts}:")
                print(f"   - DB Status: {status}")
                print(f"   - Cognee Status: {cognee_status}")
                
                if status == "indexed" or cognee_status == "indexed":
                    print("✅ Document indexed successfully!")
                    return True
                elif status == "failed":
                    print("❌ Document indexing failed")
                    return False
                
                time.sleep(2)
            else:
                print(f"❌ Status check failed: {response.text}")
                return False
        
        print("⚠️  Timeout waiting for indexing")
        return False
    
    def query_document(self, query):
        """Query the knowledge base."""
        print(f"\n5️⃣  Querying document with: '{query}'...")
        
        response = requests.post(
            f"{self.base_url}/resources/kb/{self.kb_id}/query",
            headers=self.get_headers(),
            json={
                "query": query,
                "llm_config_id": self.llm_config_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Query successful")
            print(f"   - Results count: {data.get('results_count', 0)}")
            print(f"   - Answer preview: {data['answer'][:200]}...")
            return True
        else:
            print(f"❌ Query failed: {response.status_code} - {response.text}")
            return False
    
    def list_documents(self):
        """List all knowledge base documents."""
        print("\n6️⃣  Listing all documents...")
        
        response = requests.get(
            f"{self.base_url}/resources/kb",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Found {len(docs)} documents:")
            for doc in docs:
                print(f"   - {doc['filename']} (Status: {doc['status']})")
            return True
        else:
            print(f"❌ List failed: {response.text}")
            return False
    
    def delete_document(self):
        """Delete a document from knowledge base."""
        print(f"\n7️⃣  Deleting document...")
        
        response = requests.delete(
            f"{self.base_url}/resources/kb/{self.kb_id}",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            print("✅ Delete successful")
            print(f"   - {response.json().get('message')}")
            return True
        else:
            print(f"❌ Delete failed: {response.text}")
            return False
    
    def run_full_test(self, test_file):
        """Run complete test suite."""
        print("=" * 60)
        print("🧪  KNOWLEDGE BASE API TEST SUITE")
        print("=" * 60)
        
        results = []
        
        # Login
        results.append(("Login", self.login()))
        if not results[-1][1]:
            return self.print_summary(results)
        
        # Create LLM config
        results.append(("LLM Config", self.create_llm_config()))
        if not results[-1][1]:
            return self.print_summary(results)
        
        # Upload
        results.append(("Upload", self.upload_document(test_file)))
        if not results[-1][1]:
            return self.print_summary(results)
        
        # Check status
        results.append(("Status Check", self.check_status()))
        
        # Query (only if indexed)
        if results[-1][1]:
            results.append(("Query", self.query_document("What is this document about?")))
        
        # List
        results.append(("List", self.list_documents()))
        
        # Delete
        results.append(("Delete", self.delete_document()))
        
        return self.print_summary(results)
    
    def print_summary(self, results):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊  TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n{passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED - Knowledge Base APIs are production-ready!")
            return True
        else:
            print("\n⚠️  SOME TESTS FAILED - Please review the errors above")
            return False

if __name__ == "__main__":
    # Create a test document
    test_file = Path("test_document.txt")
    if not test_file.exists():
        test_file.write_text("""
        This is a test document for the Knowledge Base API.
        
        It contains information about testing and validation.
        The knowledge base should be able to index this document
        and answer questions about it.
        
        Key topics: testing, validation, knowledge base, API
        """)
        print(f"📄 Created test document: {test_file}")
    
    tester = KnowledgeBaseAPITester()
    success = tester.run_full_test(str(test_file))
    
    exit(0 if success else 1)
