from .base import BaseProcessor
from utils.chunkers import resource_chunker
from utils.moodle_helpers import clean_html_content, extract_file_text
from typing import Dict
class ResourceProcessor(BaseProcessor):
    async def process(self, course_id: str, content: Dict):
        file_type = content.get("file_type", "text")
        print(f"Processing resource of type: {file_type} for course {course_id}")
        raw_text = extract_file_text(content["file_path"], file_type=file_type)
        print(raw_text)
        cleaned_text = clean_html_content(raw_text)
        chunks = resource_chunker(cleaned_text)
        documents = [
            self._create_document(
                text=chunk,
                course_id=course_id,
                metadata={
                    "type": "resource",
                    "file_type": file_type,
                    "original_path": content["file_path"]
                }
            ) for chunk in chunks
        ]
        self.index_manager.add_documents(documents)