from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class CourseDocument(BaseModel):
    text: str
    embedding: Optional[List[float]] = None  # now optional
    metadata: Dict = Field(default_factory=dict)
    course_id: str
    vector_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ProcessedActivity(BaseModel):
    course_id: str
    activity_type: str
    content_hash: str
    processed_at: datetime = Field(default_factory=datetime.now)