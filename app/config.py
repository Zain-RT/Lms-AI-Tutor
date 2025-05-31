import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

class Config:
    # Embedding configuration
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE = "cpu"
    
    # Index configuration
    FAISS_INDEX_PATH = "data/faiss_index"
    INDEX_METADATA_PATH = "data/metadata.json"
    
    # Processing configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_CONTEXT_LENGTH = 4096
    
    # Groq configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "llama3-8b-8192"
    
    # Logging configuration
    LOG_LEVEL = "INFO"