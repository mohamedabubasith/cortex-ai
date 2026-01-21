import os
import logging
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import UnstructuredFileLoader, TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_core.documents import Document
from app.core.config import settings

logger = logging.getLogger(__name__)

# Constants
CHROMA_PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/chroma")

class LangChainService:
    def __init__(self):
        # Local cache directory for models
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/models")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            
        # Using HuggingFaceEmbeddings with the configured model
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            cache_folder=self.cache_dir,
            model_kwargs={'device': 'cpu'}, # Can be changed to 'cuda' or 'mps' if available
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Ensure persist directory exists
        if not os.path.exists(CHROMA_PERSIST_DIRECTORY):
            os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            
        self.vector_store = Chroma(
            collection_name="cortex_knowledge_base",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_PERSIST_DIRECTORY
        )
        logger.info(f"Initialized LangChain with HuggingFaceEmbeddings at {CHROMA_PERSIST_DIRECTORY}")

    def parse_file(self, file_path: str) -> List[Document]:
        """
        Parse file into documents (Synchronous - CPU Bound)
        Uses Docling for advanced parsing where applicable.
        """
        try:
            return self._load_file(file_path)
        except Exception as e:
            logger.error(f"Parsing failed for {file_path}: {e}")
            raise e

    def index_documents(self, docs: List[Document], kb_id: str, tenant_id: str, file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Dict[str, Any]:
        """
        Split and Index documents (Synchronous - CPU Bound)
        Uses Markdown structure splitting to respect headers and tables.
        """
        try:
            # 1. Structure Split (Markdown)
            # Define headers to split on - this preserves structure
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
            markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            
            md_docs = []
            for doc in docs:
                 # Split the markdown content by headers
                 if doc.metadata.get("file_type") in [".pdf", ".docx", ".pptx", ".md"]:
                     # Only use markdown splitter for docling outputs or md files
                     splits = markdown_splitter.split_text(doc.page_content)
                     # Merge original metadata with new header metadata
                     for split in splits:
                         split.metadata.update(doc.metadata)
                     md_docs.extend(splits)
                 else:
                     # Fallback for plain text
                     md_docs.append(doc)

            # 2. Size Split (Recursive Fallback)
            # Only splits further if a section is larger than chunk_size
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                is_separator_regex=False,
            )
            final_splits = text_splitter.split_documents(md_docs)
            
            # 3. Add Metadata (Critical for RLS and Management)
            for split in final_splits:
                split.metadata["kb_id"] = kb_id
                split.metadata["tenant_id"] = tenant_id
                split.metadata["source"] = os.path.basename(file_path)

            # 4. Add to Vector Store
            ids = self.vector_store.add_documents(documents=final_splits)
            logger.info(f"Ingested {len(ids)} chunks for KB {kb_id} (Tenant: {tenant_id})")
            
            return {
                "success": True, 
                "chunks_count": len(ids), 
                "message": "Successfully indexed"
            }
        
        except Exception as e:
            logger.error(f"Indexing failed for KB {kb_id}: {e}")
            return {"success": False, "message": str(e)}

    # Legacy wrapper for backward compatibility if needed, but we will move to granular calls
    def ingest_file(self, file_path: str, kb_id: str, tenant_id: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> Dict[str, Any]:
        docs = self.parse_file(file_path)
        return self.index_documents(docs, kb_id, tenant_id, file_path, chunk_size, chunk_overlap)

    def _load_file(self, file_path: str):
        """Helper to load different file types using Docling for advanced parsing"""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Use Docling for PDFs and Office docs for better structure/table extraction
        if ext in [".pdf", ".docx", ".pptx"]:
            try:
                from docling.document_converter import DocumentConverter
                
                logger.info(f"Using Docling parser for {ext} file")
                
                # Initialize Docling converter
                converter = DocumentConverter()
                result = converter.convert(file_path)
                
                # Extract markdown text (preserves tables and structure)
                markdown_text = result.document.export_to_markdown()
                
                # Create LangChain document
                doc = Document(
                    page_content=markdown_text,
                    metadata={
                        "source": os.path.basename(file_path),
                        "file_type": ext,
                        "parser": "docling"
                    }
                )
                
                logger.info(f"Docling successfully parsed {file_path}")
                return [doc]
                
            except Exception as e:
                logger.warning(f"Docling failed, falling back to PyPDF: {e}")
                # Fallback to PyPDF
                loader = PyPDFLoader(file_path) if ext == ".pdf" else UnstructuredFileLoader(file_path)
                return loader.load()
        
        elif ext == ".txt":
            loader = TextLoader(file_path)
        else:
            loader = UnstructuredFileLoader(file_path)
            
        return loader.load()

    async def query(self, query_text: str, tenant_id: str, k: int = 4, kb_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Query the vector store with RLS (tenant_id filter).
        """
        try:
            # Build Filter
            conditions = [{"tenant_id": tenant_id}]
            
            # Optional: Filter by specific KB IDs
            if kb_ids:
                if len(kb_ids) == 1:
                    conditions.append({"kb_id": kb_ids[0]})
                else:
                    conditions.append({"kb_id": {"$in": kb_ids}})
            
            if len(conditions) > 1:
                filter_dict = {"$and": conditions}
            else:
                filter_dict = conditions[0]
            
            # Search
            results = self.vector_store.similarity_search_with_score(
                query=query_text,
                k=k,
                filter=filter_dict
            )
            
            # Format Results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise e

    async def delete_kb(self, kb_id: str, tenant_id: str) -> bool:
        """
        Delete all documents associated with a KB ID.
        """
        try:
            # We must verify tenant_id in the delete filter to prevent cross-tenant deletion
            # Chroma delete by metadata
            self.vector_store._collection.delete(
                where={"$and": [{"kb_id": kb_id}, {"tenant_id": tenant_id}]}
            )
            logger.info(f"Deleted documents for KB {kb_id}")
            return True
        except Exception as e:
            logger.error(f"Deletion failed for KB {kb_id}: {e}")
            return False

# Singleton instance
langchain_service = LangChainService()
