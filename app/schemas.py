from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal, Optional, Dict

class MoodleActivity(BaseModel):
    type: Literal["resource", "forum", "quiz", "url", "event", "announcement"]
    course_id: str
    content: dict
    timestamp: datetime

class SearchRequest(BaseModel):
    course_id: str
    query: str

class SearchResult(BaseModel):
    text: str
    score: float
    metadata: Dict

class SearchResponse(BaseModel):
    answer: str
    sources: List[SearchResult]