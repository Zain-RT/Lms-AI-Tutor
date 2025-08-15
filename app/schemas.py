from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any

class MoodleActivity(BaseModel):
    type: Literal["resource", "forum", "quiz", "url", "event", "announcement"]
    course_id: str
    content: dict
    timestamp: datetime

class SearchRequest(BaseModel):
    course_id: str
    query: str
    top_k: Optional[int] = None
    threshold: Optional[float] = None
    session_id: Optional[str] = None
    # Query expansion options
    expand: Optional[bool] = False
    num_expansions: Optional[int] = 3
    top_k_per_query: Optional[int] = None

class SearchResult(BaseModel):
    text: str
    score: float
    metadata: Dict

class SearchResponse(BaseModel):
    answer: str
    sources: List[SearchResult]

class LessonCreateRequest(BaseModel):
    course_id: str
    title: str
    material_url: str  # URL or path to the file
    material_type: str  # "pdf", "pptx", "video", etc.
    prompt: Optional[str] = None  # AI prompt for lesson generation

class LessonSection(BaseModel):
    heading: str
    content: str

class LessonCreateResponse(BaseModel):
    lesson_id: str
    title: str
    sections: List[LessonSection]
    summary: Optional[str]
    quiz: Optional[List[Dict]]

class ResourceGenerateRequest(BaseModel):
    type: str  # lesson | quiz | assignment
    prompt: Optional[str] = None
    file_url: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

class LessonPage(BaseModel):
    title: str
    content: str

class QuizQuestion(BaseModel):
    questiontext: str
    answers: List[str]
    correct: int

class ResourceGenerateResponse(BaseModel):
    type: str
    title: str
    summary: Optional[str] = None
    pages: Optional[List[LessonPage]] = None
    description: Optional[str] = None
    duedate: Optional[str] = None
    grade: Optional[int] = None
    attempts: Optional[int] = None
    questions: Optional[List[QuizQuestion]] = None

# Chat-specific models
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[SearchResult]
    messages: List[ChatMessage]