# Moodle Course Bot API

AI-powered course assistant with RAG capabilities

## Features
- Real-time processing of Moodle activities
- Course-specific semantic search with query expansion
- Support for multiple content types (PDF, PPTX, DOCX)
- FAISS-based vector search with per-course indexing
- Groq LLM integration for generation
- Session-aware chat with persistent history
- Lesson creation from materials

## Prerequisites
- Python 3.8+
- GROQ API key (required for LLM generation)

## Local Development Setup

### 1. Clone and Setup
```bash
git clone <your-repo>
cd moodle-course-bot-ai_backend
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
MOODLE_API_KEY=your_moodle_api_key
LOG_LEVEL=INFO
```

**Get GROQ API Key:**
1. Go to [Groq Console](https://console.groq.com/)
2. Sign up/Login
3. Create an API key
4. Copy and paste it in your `.env` file

### 5. Run the API Server
```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

### 6. Test the Frontend
Open a new terminal and serve the frontend tester:
```bash
# From project root
python3 -m http.server 8080
```

Then open: http://localhost:8080/frontend/index.html

## API Endpoints

### Chat & Sessions
- `POST /chat/session?course_id={id}` - Create new chat session
- `POST /chat` - Send message (supports query expansion)
- `POST /chat/end?session_id={id}&delete={bool}` - End session
- `DELETE /chat/session/{id}` - Delete session

### Content & Search
- `POST /search` - Search course content
- `POST /lessons` - Create lesson from material
- `POST /activities` - Process Moodle activity
- `GET /courses` - List indexed courses
- `GET /health` - Health check

### Example Chat Request
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "math",
    "query": "Explain calculus",
    "expand": true,
    "num_expansions": 3,
    "top_k": 5,
    "threshold": 0.2
  }'
```

## Configuration Options

### Chat Settings
- `expand`: Enable LLM-based query expansion (default: false)
- `num_expansions`: Number of alternative queries to generate (default: 3)
- `top_k`: Total results to return (default: 5)
- `threshold`: Minimum similarity score (default: none)
- `top_k_per_query`: Results per individual query when expanding

### Environment Variables
- `GROQ_API_KEY`: Required for LLM generation
- `MOODLE_API_KEY`: Optional for Moodle integration
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)
- `STORAGE_PATH`: Storage directory (default: "storage")
- `CHUNK_SIZE`: Document chunk size (default: 1024)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)

## Project Structure
```
moodle-course-bot-ai_backend/
├── app/                    # Main application
│   ├── main.py           # FastAPI app and endpoints
│   ├── services/         # Business logic services
│   ├── processors/       # Content processors
│   ├── schemas.py        # Pydantic models
│   └── utils/            # Utility functions
├── frontend/             # Testing UI
├── docs/                 # Technical documentation
├── storage/              # Vector indices and data
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables
```

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure virtual environment is activated
2. **GROQ API errors**: Check your API key in `.env`
3. **Port conflicts**: Change port in uvicorn command
4. **Storage issues**: Ensure `storage/` directory exists

### Logs
- API logs appear in the terminal running uvicorn
- Set `LOG_LEVEL=DEBUG` in `.env` for verbose logging
- Chat logs show query expansion, retrieval counts, and generation status

## Next Steps
- Add course materials via `/activities` endpoint
- Test chat with query expansion enabled
- Explore the floating chat widget in the frontend
- Check `docs/` folder for technical details
