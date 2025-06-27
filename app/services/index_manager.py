# from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
# from llama_index.vector_stores.faiss import FaissVectorStore
# from llama_index.core.embeddings import resolve_embed_model
# from llama_index.core.schema import Document, BaseNode
# from llama_index.core.retrievers import VectorIndexRetriever
# from config import Config

# import faiss
# from pathlib import Path
# from typing import Dict, List
# import logging

# logger = logging.getLogger(__name__)

# class IndexManager:
#     def __init__(self):
#         self.storage_path = Path(Config.STORAGE_PATH)
#         self.storage_path.mkdir(parents=True, exist_ok=True)
#         self.indexes: Dict[str, VectorStoreIndex] = {}
#         self.retrievers: Dict[str, VectorIndexRetriever] = {}

#         # Use local HuggingFace model for embedding
#         self.embed_model = resolve_embed_model("local:sentence-transformers/all-MiniLM-L6-v2")

#     def get_index_path(self, course_id: str) -> Path:
#         return self.storage_path / f"course_{course_id}"

#     def course_index_exists(self, course_id: str) -> bool:
#         index_path = self.get_index_path(course_id)
#         return index_path.exists() and any(index_path.iterdir())

#     def initialize_index(self, course_id: str, documents: List[Document] = None):
#         index_path = self.get_index_path(course_id)
#         print(f"Initializing index for course {course_id} at {index_path}")

#         if self.course_index_exists(course_id):
#             print(f"Loading existing index for course {course_id}")
#             storage_context = StorageContext.from_defaults(
#                 persist_dir=str(index_path),
#             )
#             print(f"Storage context loaded from {index_path}")
#             index = load_index_from_storage(storage_context, embed_model=self.embed_model)
#             print(f"Index loaded with {len(index.storage_context.vector_store.index)} nodes")
#         else:
#             print(f"No existing index found for course {course_id}, creating new index")
#             dimension = 384  # Based on all-MiniLM-L6-v2
#             faiss_index = faiss.IndexFlatL2(dimension)
#             vector_store = FaissVectorStore(faiss_index=faiss_index)

#             storage_context = StorageContext.from_defaults(vector_store=vector_store)

#             index = VectorStoreIndex.from_documents(
#                 documents or [],
#                 storage_context=storage_context,
#                 vector_store=vector_store,
#                 embed_model=self.embed_model,
#                 show_progress=True
#             )

#             storage_context.persist(persist_dir=str(index_path))

#         self.indexes[course_id] = index
#         self.retrievers[course_id] = index.as_retriever(
#             similarity_top_k=Config.SIMILARITY_TOP_K
#         )
#         return index

#     def add_documents(self, course_id: str, documents: List[Document]):
#         #print(documents)
#         dimension = 384  # Based on all-MiniLM-L6-v2
#         faiss_index = faiss.IndexFlatL2(dimension)
#         vector_store = FaissVectorStore(faiss_index=faiss_index)
#         storage_context = StorageContext.from_defaults(vector_store=vector_store)
#         index = VectorStoreIndex.from_documents(
#             documents, storage_context=storage_context,embed_model=self.embed_model, show_progress=True
#         )
#         index.storage_context.persist()

#     def search(self, course_id: str, query: str) -> List[str]:
#         # Load FAISS vector store from disk
#         vector_store = FaissVectorStore.from_persist_dir(persist_dir="./storage")

#         # Recreate storage context
#         storage_context = StorageContext.from_defaults(
#             vector_store=vector_store, persist_dir="./storage"
#         )

#         # Load index from storage
#         index = load_index_from_storage(
#             storage_context=storage_context,
#             embed_model=self.embed_model
#         )

#         # Create a retriever to fetch relevant nodes
#         retriever = index.as_retriever(similarity_top_k=Config.SIMILARITY_TOP_K)
#         print(retriever)
#         # Retrieve top nodes (documents/snippets) based on similarity
#         nodes = retriever.retrieve(query)
#         print(f"Retrieved {len(nodes)} nodes for query '{query}' in course {course_id}")
#         print(nodes[0].get_content())
#         return nodes
    
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.schema import Document
from config import Config
import faiss
from pathlib import Path
from typing import List, Dict, Optional
import os
import shutil

class IndexManager:
    def __init__(self):
        self.storage_path = Path(Config.STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.embed_model = resolve_embed_model("local:sentence-transformers/all-MiniLM-L6-v2")
        self.dimension = 384  # Fixed dimension for all-MiniLM-L6-v2

    def get_course_storage_path(self, course_id: str) -> Path:
        """Get storage path for a specific course"""
        return self.storage_path / f"course_{course_id}"

    def course_index_exists(self, course_id: str) -> bool:
        """Check if a course index exists"""
        course_path = self.get_course_storage_path(course_id)
        return course_path.exists() and any(course_path.iterdir())

    def add_documents(self, course_id: str, documents: List[Document]):
        """Add documents to a course-specific index"""
        # Create course-specific storage path
        course_path = self.get_course_storage_path(course_id)
        course_path.mkdir(parents=True, exist_ok=True)
        
        # Create FAISS index and vector store
        faiss_index = faiss.IndexFlatL2(self.dimension)
        vector_store = FaissVectorStore(
            faiss_index=faiss_index,
        )        
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
                
        # Create index from documents
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context,
            embed_model=self.embed_model,
            show_progress=True
        )
        faiss_index = vector_store._faiss_index
        print(f"Number of vectors stored: {faiss_index.ntotal}")

        # Persist index to course-specific directory
        storage_context.persist(persist_dir=str(course_path))
        print(f"Persisted index for course {course_id} at {course_path}")

    def search(self, course_id: str, query: str) -> List[Dict]:
        """Search within a course-specific index"""
        course_path = self.get_course_storage_path(course_id)
        
        if not self.course_index_exists(course_id):
            print(f"No index found for course {course_id}")
            return []
        
        # Load FAISS vector store
        try:
            vector_store = FaissVectorStore.from_persist_dir(str(course_path))
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store,
                persist_dir=str(course_path)
            )
            
            # Load index
            index = load_index_from_storage(
                storage_context=storage_context,
                embed_model=self.embed_model
            )
            
            # Create retriever
            retriever = index.as_retriever(similarity_top_k=Config.SIMILARITY_TOP_K)
            
            # Retrieve results
            nodes = retriever.retrieve(query)
            return nodes
            
        except Exception as e:
            print(f"Error loading index for course {course_id}: {str(e)}")
            # Attempt to repair by deleting and recreating
            shutil.rmtree(course_path, ignore_errors=True)
            return []

    def delete_course_index(self, course_id: str):
        """Delete a course-specific index"""
        course_path = self.get_course_storage_path(course_id)
        if course_path.exists():
            shutil.rmtree(course_path)
            print(f"Deleted index for course {course_id}")
        else:
            print(f"No index found for course {course_id}")