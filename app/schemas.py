from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal, Optional

class MoodleActivity(BaseModel):
    type: Literal["resource", "forum", "quiz", "url", "event", "announcement"]
    course_id: str
    content: dict
    timestamp: datetime
    source: Optional[str] = "moodle"

class SearchRequest(BaseModel):
    query: str
    course_id: Optional[str] = None
    top_k: int = 5
    threshold: float = 0.4
    filter_types: Optional[List[str]] = None

class SearchResult(BaseModel):
    text: str
    score: float
    metadata: dict
    course_id: str

class SearchResponse(BaseModel):
    answer: str
    sources: List[SearchResult]