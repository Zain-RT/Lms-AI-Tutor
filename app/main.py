from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services import IndexManager, GenerationService
from processors import get_processor
from schemas import MoodleActivity, SearchRequest, SearchResponse, LessonCreateRequest, LessonCreateResponse, ResourceGenerateRequest, ResourceGenerateResponse
from services.resource_service import ResourceService
import logging
from config import Config

app = FastAPI(title="Moodle Course Bot (LlamaIndex)", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
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
    nodes = IndexManager().search(request.course_id, request.query)
    
    if not nodes:
        return SearchResponse(
            answer="No relevant information found",
            sources=[]
        )
    
    # Generate answer
    context = "\n\n".join([
        f"Source {i+1} (Score: {node.score:.2f}):\n{node.text}" 
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
        metadata = node.metadata or {}
        sources.append({
            "text": node.text,
            "score": node.score,
            "metadata": metadata
        })
    
    return SearchResponse(
        answer=answer,
        sources=sources
    )

@app.post("/chat", response_model=SearchResponse)
async def chat(request: SearchRequest):
    """Chat endpoint using retrieved context"""
    try:
        logging.info(f"Received chat request: {request.query} for course {request.course_id}")
        # Retrieve relevant documents
        nodes = IndexManager().search(request.course_id, request.query)

        # Build context for generation
        context = "\n".join([f"Source {i+1}: {getattr(node, 'text', '')}" for i, node in enumerate(nodes)])

        # Generate answer
        answer = GenerationService().generate_response(
            user_input=request.query,
            material=context,
            task_type="chat"
        )

        # Format sources in the same way as /search
        sources = []
        for node in nodes:
            metadata = getattr(node, "metadata", {}) or {}
            text = getattr(node, "text", None)
            score = getattr(node, "score", None)
            if text is None and hasattr(node, "get_content"):
                try:
                    text = node.get_content()
                except Exception:
                    text = ""
            sources.append({
                "text": text or "",
                "score": float(score) if isinstance(score, (int, float)) else 0.0,
                "metadata": metadata
            })

        return SearchResponse(answer=answer, sources=sources)

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
    
   

# @app.post("/lessons", response_model=LessonCreateResponse)
# async def create_lesson(request: LessonCreateRequest):
#     """
#     Create a lesson from uploaded material using AI.
#     """
#     try:
#         lesson = await LessonService().create_lesson(request)
#         return lesson
#     except Exception as e:
#         logging.error(f"Lesson creation error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

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