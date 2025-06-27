from services import IndexManager
from utils.llama_helpers import create_document, chunk_document
from typing import Dict

class BaseProcessor:
    def __init__(self):
        self.index_manager = IndexManager()
    
    def _create_document(self, text: str, course_id: str, metadata: Dict):
        doc = create_document(text, {
            "course_id": course_id,
            **metadata
        })
        return chunk_document(doc)
    
    async def process(self, course_id: str, content: Dict):
        raise NotImplementedError