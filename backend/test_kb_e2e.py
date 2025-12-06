#!/usr/bin/env python3
"""
Production-Grade End-to-End Test for Knowledge Base APIs

Tests the actual KB functionality:
1. Upload document
2. Check status (polling until indexed)
3. Query/Search the document
4. Delete the document

Run: python test_kb_e2e.py
"""

import requests
import time
import os
import sys
from pathlib import Path
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "abubasith456@gmail.com"
TEST_PASSWORD = "123456"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class KBAPITester:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.token = None
        self.llm_config_id = None
        self.kb_id = None
        self.test_passed = 0
        self.test_failed = 0
        
    def print_header(self, text):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")
    
    def print_success(self, text):
        print(f"{Colors.GREEN}✅ {text}{Colors.END}")
        self.test_passed += 1
    
    def print_error(self, text):
        print(f"{Colors.RED}❌ {text}{Colors.END}")
        self.test_failed += 1
    
    def print_info(self, text):
        print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")
    
    def login(self):
        """Step 1: Authenticate"""
        self.print_header("STEP 1: Authentication")
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/token",
                data={
                    "username": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.print_success(f"Logged in as {TEST_EMAIL}")
                return True
            else:
                self.print_error(f"Login failed: {response.status_code}")
                self.print_info(f"Response: {response.text}")
                self.print_info("Make sure user exists. Create with:")
                self.print_info(f"  POST {self.base_url}/auth/register")
                return False
                
        except Exception as e:
            self.print_error(f"Login error: {str(e)}")
            self.print_info("Make sure backend is running on http://localhost:8000")
            return False
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"}
    
    def setup_llm_config(self):
        """Step 2: Get or create LLM configuration"""
        self.print_header("STEP 2: LLM Configuration")
        
        try:
            # Check existing configs
            response = requests.get(
                f"{self.base_url}/resources/llm",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                configs = response.json()
                if configs:
                    self.llm_config_id = configs[0]["id"]
                    self.print_success(f"Using existing LLM config: {self.llm_config_id[:8]}...")
                    self.print_info(f"Provider: {configs[0].get('provider', 'N/A')}")
                    return True
            
            # Create new config if none exist
            self.print_info("No LLM config found, creating one...")
            
            # Get from environment or use defaults
            api_key = os.getenv("OPENAI_API_KEY", "sk-test-key")
            base_url = os.getenv("OPENAI_API_BASE")
            
            # Build payload
            payload = {
                "name": "Test LLM Config",
                "api_key": api_key,
                "model": "gpt-4"
            }
            
            # Only add base_url if it exists
            if base_url:
                payload["base_url"] = base_url
            
            response = requests.post(
                f"{self.base_url}/resources/llm",
                headers=self.get_headers(),
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.llm_config_id = response.json()["id"]
                self.print_success(f"Created LLM config: {self.llm_config_id[:8]}...")
                return True
            else:
                self.print_error(f"Failed to create LLM config: {response.status_code}")
                self.print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"LLM config error: {str(e)}")
            return False
    
    def upload_document(self):
        """Step 3: Upload a test document"""
        self.print_header("STEP 3: Upload Document")
        
        try:
            # Create test document
            test_file = Path("test_kb_document.txt")
            test_content = """
            TEST DOCUMENT FOR KNOWLEDGE BASE

            This is a test document for validating the Knowledge Base APIs.
            
            Key Information:
            - The capital of France is Paris
            - Python is a programming language
            - Water boils at 100 degrees Celsius
            - The Earth orbits around the Sun
            
            Technical Details:
            - API testing is important for production systems
            - Knowledge bases use vector embeddings
            - Cognee is used for indexing in this system
            
            This document should be indexed and searchable.
            """
            
            test_file.write_text(test_content)
            self.print_info(f"Created test file: {test_file}")
            
            # Upload
            with open(test_file, 'rb') as f:
                files = {'file': (test_file.name, f, 'text/plain')}
                params = {'llm_config_id': self.llm_config_id}
                
                response = requests.post(
                    f"{self.base_url}/resources/kb/upload",
                    headers=self.get_headers(),
                    files=files,
                    params=params,
                    timeout=30
                )
            
            # Cleanup test file
            if test_file.exists():
                test_file.unlink()
            
            if response.status_code == 200:
                data = response.json()
                self.kb_id = data['id']
                self.print_success(f"Document uploaded successfully")
                self.print_info(f"KB ID: {self.kb_id[:8]}...")
                self.print_info(f"Filename: {data['filename']}")
                self.print_info(f"Initial Status: {data['status']}")
                return True
            else:
                self.print_error(f"Upload failed: {response.status_code}")
                self.print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Upload error: {str(e)}")
            return False
    
    def check_status(self, max_wait=60):
        """Step 4: Check indexing status (with polling)"""
        self.print_header("STEP 4: Check Indexing Status")
        
        try:
            start_time = time.time()
            attempt = 0
            
            while time.time() - start_time < max_wait:
                attempt += 1
                
                response = requests.get(
                    f"{self.base_url}/resources/kb/{self.kb_id}/status",
                    headers=self.get_headers(),
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    db_status = data['status']
                    cognee_status = data.get('cognee_status', 'unknown')
                    
                    print(f"   Attempt {attempt}: DB={db_status}, Cognee={cognee_status}")
                    
                    if db_status == "indexed" or cognee_status == "indexed":
                        elapsed = time.time() - start_time
                        self.print_success(f"Document indexed in {elapsed:.1f}s")
                        return True
                    elif db_status == "failed":
                        self.print_error(f"Indexing failed")
                        return False
                    
                    time.sleep(2)
                else:
                    self.print_error(f"Status check failed: {response.status_code}")
                    return False
            
            self.print_error(f"Indexing timeout after {max_wait}s")
            return False
            
        except Exception as e:
            self.print_error(f"Status check error: {str(e)}")
            return False
    
    def query_document(self):
        """Step 5: Query/Search the document"""
        self.print_header("STEP 5: Query/Search Document")
        
        test_queries = [
            "What is the capital of France?",
            "What temperature does water boil at?",
            "What is this document about?"
        ]
        
        try:
            for i, query in enumerate(test_queries, 1):
                self.print_info(f"Query {i}: {query}")
                
                response = requests.post(
                    f"{self.base_url}/resources/kb/{self.kb_id}/query",
                    headers=self.get_headers(),
                    json={
                        "query": query,
                        "llm_config_id": self.llm_config_id
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', '')
                    results_count = data.get('results_count', 0)
                    
                    if answer and "No relevant context" not in answer:
                        self.print_success(f"Query successful ({results_count} results)")
                        print(f"   Answer preview: {answer[:150]}...")
                    else:
                        self.print_error(f"No relevant results found")
                        self.print_info(f"Answer: {answer[:200]}")
                else:
                    self.print_error(f"Query failed: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    return False
                
                time.sleep(1)
            
            return True
            
        except Exception as e:
            self.print_error(f"Query error: {str(e)}")
            return False
    
    def list_documents(self):
        """Step 6: List all documents"""
        self.print_header("STEP 6: List All Documents")
        
        try:
            response = requests.get(
                f"{self.base_url}/resources/kb",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                docs = response.json()
                self.print_success(f"Found {len(docs)} document(s)")
                
                for doc in docs[:5]:  # Show max 5
                    print(f"   - {doc['filename']} (Status: {doc['status']})")
                
                # Verify our document is in the list
                if any(doc['id'] == self.kb_id for doc in docs):
                    self.print_success("Our uploaded document is in the list")
                else:
                    self.print_error("Our document not found in the list")
                    return False
                
                return True
            else:
                self.print_error(f"List failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_error(f"List error: {str(e)}")
            return False
    
    def delete_document(self):
        """Step 7: Delete the document"""
        self.print_header("STEP 7: Delete Document")
        
        try:
            response = requests.delete(
                f"{self.base_url}/resources/kb/{self.kb_id}",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                message = response.json().get('message', 'Deleted')
                self.print_success(f"Document deleted: {message}")
                
                # Verify deletion
                time.sleep(1)
                verify_response = requests.get(
                    f"{self.base_url}/resources/kb/{self.kb_id}/status",
                    headers=self.get_headers(),
                    timeout=10
                )
                
                if verify_response.status_code == 404:
                    self.print_success("Deletion verified (404 on status check)")
                else:
                    self.print_error("Document still exists after deletion")
                    return False
                
                return True
            else:
                self.print_error(f"Delete failed: {response.status_code}")
                self.print_info(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Delete error: {str(e)}")
            return False
    
    def run_full_test(self):
        """Run complete end-to-end test"""
        self.print_header("🧪 KNOWLEDGE BASE API - END-TO-END TEST")
        
        print(f"Testing against: {self.base_url}")
        print(f"Test user: {TEST_EMAIL}\n")
        
        # Run all tests
        if not self.login():
            return False
        
        if not self.setup_llm_config():
            return False
        
        if not self.upload_document():
            return False
        
        if not self.check_status():
            return False
        
        if not self.query_document():
            return False
        
        if not self.list_documents():
            return False
        
        if not self.delete_document():
            return False
        
        # Print summary
        self.print_header("📊 TEST SUMMARY")
        
        total = self.test_passed + self.test_failed
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.test_passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.test_failed}{Colors.END}")
        
        if self.test_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.END}")
            print(f"{Colors.GREEN}Knowledge Base APIs are production-ready!{Colors.END}\n")
            return True
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠️  SOME TESTS FAILED{Colors.END}")
            print(f"{Colors.RED}Please review the errors above{Colors.END}\n")
            return False

if __name__ == "__main__":
    tester = KBAPITester()
    success = tester.run_full_test()
    sys.exit(0 if success else 1)
