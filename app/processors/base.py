from abc import ABC, abstractmethod
from services import IndexManager
from models import CourseDocument
from typing import Dict

class BaseProcessor(ABC):
    def __init__(self):
        self.index_manager = IndexManager()
    
    @abstractmethod
    async def process(self, course_id: str, content: Dict):
        pass
    
    def _create_document(self, text: str, course_id: str, metadata: Dict) -> CourseDocument:
        return CourseDocument(
            text=text,
            course_id=course_id,
            metadata=metadata,
        )