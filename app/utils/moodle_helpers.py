from datetime import datetime
import re

def normalize_moodle_date(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp)

def clean_html_content(html: str) -> str:
    clean_text = re.sub(r'<[^>]+>', '', html)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text
import requests
import tempfile
from pathlib import Path

def extract_file_text(file_path: str, file_type: str) -> str:
    def download_to_temp(url, suffix):
        response = requests.get(url)
        if response.status_code != 200:
            raise ValueError(f"Failed to download file from URL: {url}")
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(response.content)
            return tmp.name

    # If file_path is a URL, download it temporarily
    is_url = file_path.startswith("http://") or file_path.startswith("https://")

    if file_type == "pdf":
        from pdfminer.high_level import extract_text
        if is_url:
            file_path = download_to_temp(file_path, ".pdf")
        return extract_text(file_path)

    elif file_type == "docx":
        from docx import Document
        print("Extracting text from DOCX file")
        if is_url:
            file_path = download_to_temp(file_path, ".docx")
        return " ".join([p.text for p in Document(file_path).paragraphs])

    else:
        if is_url:
            file_path = download_to_temp(file_path, ".txt")
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
