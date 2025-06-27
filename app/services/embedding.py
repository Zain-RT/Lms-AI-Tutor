from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from config import Config
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = HuggingFaceEmbedding(
                model_name=Config.EMBEDDING_MODEL,
                device="cpu"
            )
            logger.info(f"Loaded embedding model: {Config.EMBEDDING_MODEL}")
        return cls._instance
    
    def get_model(self):
        return self.model