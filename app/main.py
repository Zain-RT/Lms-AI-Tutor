from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services import IndexManager, EmbeddingService
from schemas import MoodleActivity, SearchRequest, SearchResult, SearchResponse
from processors import get_processor
import logging
from services import GenerationService
from typing import List

app = FastAPI(title="Moodle Course Bot API", version="1.0.0")

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
    try:
        # Warm up services
        EmbeddingService().encode("warmup")
        IndexManager().search("warmup")
        logging.info("Services initialized successfully")
    except Exception as e:
        logging.error(f"Startup failed: {str(e)}")
        raise

@app.post("/activities", status_code=202)
async def process_activity(activity: MoodleActivity):
    """Endpoint for processing Moodle activities"""
    try:
        processor = get_processor(activity.type)
        if not processor:
            raise HTTPException(status_code=400, detail="Unsupported activity type")
        
        await processor().process(activity.course_id, activity.content)
        return {"status": "Processing started"}
    
    except Exception as e:
        logging.error(f"Activity processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[SearchResult])
async def search_content(request: SearchRequest):
    """Search across course content"""
    try:
        results = IndexManager().search(
            query=request.query,
            course_id=request.course_id,
            top_k=request.top_k,
            threshold=request.threshold
        )
        return [SearchResult(**result) for result in results]
    
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# main.py
@app.post("/chat", response_model=SearchResponse)
async def search_content(request: SearchRequest):
    """Search and generate response"""
    try:
        print(f"Received search request: {request.query} for course {request.course_id}")
        # Retrieve relevant documents
        results = IndexManager().search(
            query=request.query,
            course_id=request.course_id,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        # Generate answer
        context = "\n".join([f"Source {i+1}: {res.text}" for i, res in enumerate(results)])
        answer = GenerationService().generate_response(context, request.query)
        
        return SearchResponse(
            answer=answer,
            sources=results
        )
    
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/health")
async def health_check():
    """System health endpoint"""
    return {
        "status": "healthy",
        "index_size": IndexManager().index.ntotal,
        "courses": len(IndexManager().course_map)
    }

# Add this temporary endpoint to check indexed content
@app.get("/debug/courses/{course_id}")
async def debug_course(course_id: str):
    """Debug endpoint to check indexed content"""
    index = IndexManager()
    if course_id not in index.course_map:
        return {"error": f"No documents found for course {course_id}"}
    
    vector_ids = index.course_map[course_id]
    sample_docs = []
    for vid in vector_ids[:3]:  # Show first 3 documents
        doc = {
            "vector_id": vid,
            "metadata": index.metadata.get(vid, {}),
            "text": "..."  # Truncated for brevity
        }
        sample_docs.append(doc)
    
    return {
        "course_id": course_id,
        "document_count": len(vector_ids),
        "sample_documents": sample_docs
    }