# API Reference

## POST /chat/session
Create a chat session for a course.

Query:
- `course_id`: string

Response:
```json
{ "session_id": "uuid" }
```

## POST /chat
Send a chat message. Returns full session thread.

Body:
```json
{
  "course_id": "COURSE123",
  "query": "What is X?",
  "top_k": 5,
  "threshold": 0.2,
  "session_id": "uuid"
}
```

Response:
```json
{
  "session_id": "uuid",
  "answer": "...",
  "sources": [ {"text":"..","score":0.85,"metadata":{}} ],
  "messages": [ {"role":"user","content":"...","created_at":"..."} ]
}
```

## POST /chat/end
End a session, optional delete.

Query:
- `session_id`: string
- `delete`: boolean (optional)

Response:
```json
{ "session_id": "uuid", "summary": "...", "deleted": false }
```

## DELETE /chat/session/{id}
Hard delete a chat session and its messages.

Response:
```json
{ "session_id": "uuid", "deleted": true }
```

## POST /lessons
Create a lesson from material.

Body:
```json
{
  "course_id": "COURSE123",
  "title": "Intro",
  "material_url": "https://.../file.pdf",
  "material_type": "pdf",
  "prompt": "Focus on definitions"
}
```

Response: JSON with `lesson_id`, `title`, `sections`, `summary`, `quiz`. 