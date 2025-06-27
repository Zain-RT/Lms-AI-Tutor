from .base import BaseProcessor
from utils.moodle_helpers import download_file, extract_file_text
from utils.llama_helpers import create_document, chunk_document
import mimetypes
from typing import Dict

class ResourceProcessor(BaseProcessor):
    async def process(self, course_id: str, content: Dict):
        file_url = content["file_path"]
        print(file_url)
        file_type = content.get("file_type") or mimetypes.guess_extension(
            mimetypes.guess_type(file_url)[0] or "pdf"
        )
        print(file_type)
        # Download and extract text
        file_path = download_file(file_url, suffix=file_type)
        print(file_path)
        text = extract_file_text(file_path, file_type)
        print(text)
        # Create document
        document = create_document(text, {
            "type": "resource",
            "file_type": file_type,
            "source": file_url,
            "course_id": course_id
        })
        print(document)
        # Chunk and index
        #chunks = chunk_document(document)
        #print(f"Indexing {len(chunks)} chunks for course {course_id}")
        self.index_manager.add_documents(course_id, documents=[document])