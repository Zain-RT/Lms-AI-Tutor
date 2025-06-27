import httpx
from pathlib import Path
import os
import mimetypes
import asyncio
from loguru import logger
from config import Config
import socket
import time
from datetime import datetime
import requests
import tempfile
def download_file(url, suffix):
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to download file from URL: {url}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(response.content)
        return tmp.name

def extract_file_text(file_path: str, file_type: str) -> str:
    """Extract text from various file types using LlamaIndex readers"""
    if file_type in [".pdf", ".docx", ".pptx"]:
        print(f"Extracting text from {file_path} of type {file_type}")
        from llama_index.core import SimpleDirectoryReader
        reader = SimpleDirectoryReader(input_files=[file_path])
        print(f"Extracting text from {file_path} with reader {reader}")
        documents = reader.load_data()
        return "\n".join([d.text for d in documents])
    else:  # Plain text
        with open(file_path, "r") as f:
            return f.read()

def normalize_moodle_date(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp)