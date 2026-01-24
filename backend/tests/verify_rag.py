import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.rag_service import rag_service

async def verify():
    print("🧪 Starting RAG Verification...")
    
    # 1. Create dummy file
    test_file = "verify_test.txt"
    content = "The secret code is APPLE-123. This is a verification test."
    with open(test_file, "w") as f:
        f.write(content)
        
    try:
        # 2. Process
        print("📥 Indexing test document...")
        kb_id = "verify-kb-id"
        user_id = "verify-user-id"
        await rag_service.process_document(
            file_path=test_file,
            kb_id=kb_id,
            user_id=user_id,
            tenant_id="verify-tenant",
            chunk_size=100,
            chunk_overlap=20,
            llm_config=None
        )
        print("✅ Indexing successful.")
        
        # 3. Search
        print("🔍 Searching for 'secret code'...")
        results = await rag_service.search("secret code", {"kb_id": kb_id}, None)
        
        if len(results) > 0 and "APPLE-123" in results[0]["content"]:
            print(f"✅ Search successful! Found: {results[0]['content']}")
        else:
            print("❌ Search failed to find expected content.")
            
        # 4. Delete
        print("🗑️ Cleaning up vectors...")
        await rag_service.delete_kb(kb_id)
        print("✅ Cleanup successful.")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
            
    print("\n🎉 RAG Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify())
