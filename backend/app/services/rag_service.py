from typing import List, Dict, Any, Optional
import os
import shutil
import logging
from datetime import datetime

# LangChain Imports
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from app.core.config import settings

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        # Use absolute path for ChromaDB persistence (Docker-friendly)
        self.persist_directory = "/app/data/chroma_db"
        os.makedirs(self.persist_directory, exist_ok=True)
        
    def _get_embeddings(self, llm_config, embedding_model_name: Optional[str] = None):
        """Factory for embedding model with dynamic model selection"""
        # 1. Use specific model if provided
        model_to_use = embedding_model_name or settings.EMBEDDING_MODEL

        # Determine provider (default to fastembed if not specified or explicit)
        # We can expand this logic based on llm_config.provider or env vars
        
        # If user wants local/fastembed
        if settings.EMBEDDING_PROVIDER == "fastembed":
            return FastEmbedEmbeddings(
                model_name=model_to_use
            )
        
        # If user wants OpenAI or compatible
        api_key = llm_config.api_key if llm_config else None
        base_url = llm_config.base_url if llm_config else None
        
        if not api_key:
             # Fallback to fastembed if no key
             logger.warning("No API key found for embeddings, falling back to FastEmbed")
             return FastEmbedEmbeddings(model_name=model_to_use)

        return OpenAIEmbeddings(
            model=model_to_use,
            api_key=api_key,
            base_url=base_url,
            check_embedding_ctx_length=False 
        )

    def _get_vector_store(self, collection_name: str, embeddings):
        """Get Chroma vector store instance"""
        return Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=self.persist_directory
        )

    async def process_document(
        self, 
        file_path: str, 
        kb_id: str, 
        user_id: str, 
        tenant_id: str,
        chunk_size: int, 
        chunk_overlap: int, 
        llm_config,
        embedding_model: Optional[str] = None
    ):
        """
        Load, split, and index a document.
        """
        try:
            logger.info(f"Processing KB {kb_id}: Loading file {file_path}")
            
            # 1. Load Document
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
            elif ext in [".txt", ".md"]:
                loader = TextLoader(file_path)
            else:
                # Fallback
                loader = UnstructuredFileLoader(file_path)
                
            docs = loader.load()
            
            if not docs:
                raise ValueError("No content extracted from document")

            # 2. Add Global Metadata
            for doc in docs:
                doc.metadata["kb_id"] = kb_id
                doc.metadata["user_id"] = user_id
                doc.metadata["tenant_id"] = str(tenant_id) if tenant_id else "default"
                doc.metadata["source"] = os.path.basename(file_path)
                doc.metadata["created_at"] = datetime.utcnow().isoformat()
                # Ensure page is present (PyPDF adds page, others might not)
                if "page" not in doc.metadata:
                     doc.metadata["page"] = 1

            # 3. Split Text
            logger.info(f"Splitting text: Size={chunk_size}, Overlap={chunk_overlap}")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            )
            splits = text_splitter.split_documents(docs)
            logger.info(f"Created {len(splits)} chunks")

            # 4. Index
            embeddings = self._get_embeddings(llm_config, embedding_model)
            vector_store = self._get_vector_store("knowledge_base", embeddings)
            
            # Add to Chroma (sync operation, usually fast enough for moderate docs, or run in thread)
            vector_store.add_documents(documents=splits)
            
            logger.info(f"Successfully indexed KB {kb_id}")
            return {"success": True, "chunks": len(splits)}

        except Exception as e:
            logger.error(f"Error processing KB {kb_id}: {e}")
            raise e

    async def delete_kb(self, kb_id: str):
        """Delete all chunks for a KB ID"""
        try:
            # We need an embedding function even for deletion to initialize Chroma
            # Using defaults is fine
            embeddings = FastEmbedEmbeddings(model_name=settings.EMBEDDING_MODEL) 
            vector_store = self._get_vector_store("knowledge_base", embeddings)
            
            # Chroma specific deletion by metadata
            # Note: LangChain Chroma wrapper might not expose delete_where matching cleanly
            # but usually it's accessed via underlying client or generic delete
            
            # Verify if current langchain-chroma supports delete by metadata directly
            # If not, we iterate. But modern Chroma supports it.
            # Workaround: Fetch IDs by metadata then delete
            
            # Ideally: vector_store.delete(where={"kb_id": kb_id})
            # Let's try the direct client access if needed, or standard method
            
            # Langchain abstraction:
            # vector_store.delete(ids=[...])
            
            # Efficient way accessing internal client:
            vector_store._client.get_or_create_collection("knowledge_base").delete(
                where={"kb_id": kb_id}
            )
            
            logger.info(f"Deleted vector entries for KB {kb_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting KB {kb_id}: {e}")
            return False

    async def search(self, query: str, config_filter: Dict[str, Any], llm_config, embedding_model: Optional[str] = None, k: int = 4):
        """
        Search for context.
        config_filter: e.g. {"user_id": "...", "kb_id": "..."} or just user/tenant context
        """
        try:
            embeddings = self._get_embeddings(llm_config, embedding_model)
            vector_store = self._get_vector_store("knowledge_base", embeddings)
            
            results = vector_store.similarity_search_with_score(
                query,
                k=k,
                filter=config_filter
            )
            
            # Format results
            formatted = []
            for doc, score in results:
                formatted.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
                
            return formatted
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

rag_service = RAGService()
