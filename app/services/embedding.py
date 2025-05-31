# services/embedding.py
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
from config import Config

class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_model()
        return cls._instance
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logging.info(f"Loaded embedding model: {Config.EMBEDDING_MODEL}")
        except Exception as e:
            logging.error(f"Error initializing embedding model: {str(e)}")
            raise

    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Encode text(s) into embeddings
        Args:
            texts: Single text string or list of texts
            batch_size: Batch size for encoding
        Returns:
            Numpy array of embeddings with shape (num_texts, dimension)
        """
        if isinstance(texts, str):
            texts = [texts]
            
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True  # For cosine similarity
            )
            return embeddings.astype('float32')
        except Exception as e:
            logging.error(f"Encoding error: {str(e)}")
            raise

    async def aencode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Async version of encode"""
        # In production, you'd use real async here
        return self.encode(texts, batch_size)