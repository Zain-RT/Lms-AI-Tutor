from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services import IndexManager, GenerationService, ResourceService, LessonService, ChatService, SessionStore
from processors import get_processor
from schemas import MoodleActivity, SearchRequest, SearchResponse, LessonCreateRequest, LessonCreateResponse, ResourceGenerateRequest, ResourceGenerateResponse, ChatResponse, ChatMessage
import logging
from config import Config
from datetime import datetime, timedelta

app = FastAPI(title="Moodle Course Bot (LlamaIndex)", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_store = SessionStore()

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    level_name = getattr(Config, "LOG_LEVEL", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.info("Services initialized successfully")

@app.post("/activities", status_code=202)
async def process_activity(activity: MoodleActivity):
    processor = get_processor(activity.type)
    if not processor:
        raise HTTPException(status_code=400, detail="Unsupported activity type")
    print(activity)
    await processor().process(activity.course_id, activity.content)
    return {"status": "Processing started"}

@app.post("/search", response_model=SearchResponse)
async def search_content(request: SearchRequest):
    # Retrieve relevant nodes
    nodes = IndexManager().search(request.course_id, request.query, top_k=request.top_k)
    
    # Optional threshold filtering
    if request.threshold is not None:
        try:
            nodes = [n for n in nodes if getattr(n, "score", None) is not None and float(n.score) >= float(request.threshold)]
        except Exception:
            pass
    
    if not nodes:
        return SearchResponse(
            answer="No relevant information found",
            sources=[]
        )
    
    # Generate answer
    context = "\n\n".join([
        f"Source {i+1} (Score: {getattr(node, 'score', 0.0):.2f}):\n{getattr(node, 'text', '')}" 
        for i, node in enumerate(nodes)
    ])
    
    # Use the new generic interface, set task_type to "search" for clarity
    answer = GenerationService().generate_response(
        user_input=request.query,
        material=context,
        task_type="search"
    )
    
    # Format sources
    sources = []
    for node in nodes:
        metadata = getattr(node, 'metadata', {}) or {}
        sources.append({
            "text": getattr(node, 'text', ''),
            "score": float(getattr(node, 'score', 0.0)),
            "metadata": metadata
        })
    
    return SearchResponse(
        answer=answer,
        sources=sources
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: SearchRequest):
    """Chat endpoint using retrieved context and returning full session thread."""
    try:
        logging.info(f"Received chat request: {request.query} for course {request.course_id}")
        if request.session_id is not None and not session_store.session_exists(request.session_id):
            raise HTTPException(status_code=404, detail="Session not found or has ended")
        chat_service = ChatService()
        result = chat_service.chat(
            course_id=request.course_id,
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            session_id=request.session_id,
            expand=bool(request.expand or False),
            num_expansions=int(request.num_expansions or 3),
            top_k_per_query=request.top_k_per_query,
        )
        sid = request.session_id or ""
        messages_raw = session_store.get_session_messages(sid, limit=200) if sid else []
        messages = [ChatMessage(role=m["role"], content=m["content"], created_at=m["created_at"]) for m in messages_raw]
        return ChatResponse(session_id=sid, answer=result["answer"], sources=result["sources"], messages=messages)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/health")
async def health_check():
    """System health endpoint"""
    return {
        "status": "healthy"
    }

# Add this temporary endpoint to check indexed content
@app.get("/debug/courses/{course_id}")
async def debug_course(course_id: str):
    """Debug endpoint to check indexed content"""
    index = IndexManager()
    if not index.course_index_exists(course_id):
        raise HTTPException(status_code=404, detail="Course index not found")
    try:
        documents = index.get_course_documents(course_id)
        return {
            "course_id": course_id,
            "documents": [doc.to_dict() for doc in documents]
        }
    except Exception as e:
        logging.error(f"Debug error for course {course_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
    
   

@app.post("/lessons", response_model=LessonCreateResponse)
async def create_lesson(request: LessonCreateRequest):
    """
    Create a lesson from uploaded material using AI.
    """
    try:
        lesson = await LessonService().create_lesson(request)
        return lesson
    except Exception as e:
        logging.error(f"Lesson creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-resource", response_model=ResourceGenerateResponse)
async def generate_resource(request: ResourceGenerateRequest):
    """
    Unified AI resource generator for lessons, assignments, quizzes.
    """
    try:
        resource = await ResourceService().generate(request)
        return resource
    except Exception as e:
        logging.error(f"Resource generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
# write endpoint to list all courses with their indexed documents
@app.get("/courses")
async def list_courses():
    """
    List all courses with their indexed documents.
    """
    try:
        index_manager = IndexManager()
        courses = index_manager.list_courses()
        return {"courses": courses}
    except Exception as e:
        logging.error(f"Error listing courses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

@app.post("/chat/session")
async def create_chat_session(course_id: str):
    try:
        session_id = session_store.create_session(course_id)
        return {"session_id": session_id}
    except Exception as e:
        logging.error(f"Create session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/end")
async def end_chat_session(session_id: str, delete: bool = False):
    try:
        if not session_store.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        summary = session_store.end_session(session_id)
        if delete:
            session_store.delete_session(session_id)
        return {"session_id": session_id, "summary": summary, "deleted": delete}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"End session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 

@app.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    try:
        if not session_store.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        session_store.delete_session(session_id)
        return {"session_id": session_id, "deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Delete session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 