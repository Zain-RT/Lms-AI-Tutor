# services/index_manager.py
import faiss
import numpy as np
from typing import List, Dict, Optional
import logging
from threading import Lock
from models import CourseDocument
import os

class IndexManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_index()
        return cls._instance
    
    def _initialize_index(self):
        """Initialize FAISS index and metadata storage"""
        from services.embedding import EmbeddingService
        
        self.embedding_service = EmbeddingService()
        self.dimension = self.embedding_service.dimension
        
        # Create FAISS index with ID mapping
        self.index = faiss.IndexIDMap2(faiss.IndexFlatIP(self.dimension))
        
        # Metadata storage
        self.metadata: Dict[int, Dict] = {}  # {vector_id: metadata}
        self.course_map: Dict[str, List[int]] = {}  # {course_id: [vector_ids]}
        
        self.lock = Lock()
        self.next_id = 0
        logging.info("Initialized FAISS index and metadata storage")

    def add_documents(self, documents: List[CourseDocument]):
        """
        Add documents to the index with metadata
        Args:
            documents: List of CourseDocument objects
        """
        if not documents:
            return

        try:
            texts = [doc.text for doc in documents]
            embeddings = self.embedding_service.encode(texts)
            
            with self.lock:
                start_id = self.next_id
                end_id = start_id + len(documents)
                ids = np.arange(start_id, end_id, dtype=np.int64)
                
                # Add to FAISS index
                self.index.add_with_ids(embeddings, ids)
                
                # Store metadata and course mappings
                for idx, doc in enumerate(documents):
                    vector_id = start_id + idx
                    self.metadata[vector_id] = doc.metadata
                    self.course_map.setdefault(doc.course_id, []).append(vector_id)
                
                self.next_id = end_id
                logging.info(f"Added {len(documents)} documents to index")

        except Exception as e:
            logging.error(f"Error adding documents: {str(e)}")
            raise

    def search(
        self,
        query: str,
        course_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Search the index with a text query
        Args:
            query: Search query text
            course_id: Optional course ID to filter results
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
        Returns:
            List of result dicts with 'text', 'score', and 'metadata'
        """
        try:
            # Encode query
            query_embed = self.embedding_service.encode(query)
            
            # Get candidate vector IDs if filtering by course
            if course_id:
                candidate_ids = np.array(
                    self.course_map.get(course_id, []),
                    dtype=np.int64
                )
            else:
                candidate_ids = None

            # Search FAISS index
            with self.lock:
                scores, vector_ids = self.index.search(
                    query_embed.reshape(1, -1),
                    k=top_k if not candidate_ids else len(candidate_ids)
                )

            # Process results
            results = []
            for score, vector_id in zip(scores[0], vector_ids[0]):
                if vector_id == -1 or score < threshold:
                    continue
                
                if candidate_ids is not None and vector_id not in candidate_ids:
                    continue
                
                metadata = self.metadata.get(vector_id, {})
                results.append({
                    "text": metadata.get("original_text", ""),
                    "score": float(score),
                    "metadata": metadata
                })

            return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

        except Exception as e:
            logging.error(f"Search error: {str(e)}")
            raise

    def save_index(self, path: str = "faiss_index"):
        """Save index and metadata to disk"""
        with self.lock:
            faiss.write_index(self.index, f"{path}.faiss")
            # In production, save metadata and course_map properly
            logging.info(f"Index saved to {path}.faiss")

    def load_index(self, path: str = "faiss_index"):
        """Load index from disk"""
        with self.lock:
            if os.path.exists(f"{path}.faiss"):
                self.index = faiss.read_index(f"{path}.faiss")
                # Load metadata and course_map from DB in real scenario
                logging.info(f"Index loaded from {path}.faiss")