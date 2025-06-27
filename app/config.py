import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

class Config:
    # Storage configuration
    STORAGE_PATH = "storage"
    TEMP_DIR="temp"
    # Embedding configuration
    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    
    # LlamaIndex configuration
    CHUNK_SIZE = 1024
    CHUNK_OVERLAP = 200
    SIMILARITY_TOP_K = 5
    
    # Moodle integration
    MOODLE_API_KEY = os.getenv("MOODLE_API_KEY")
    
    # Groq configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "llama3-8b-8192"
    
    # Logging configuration
    LOG_LEVEL = "INFO"