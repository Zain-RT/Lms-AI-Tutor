# Chat and Session Management

## Session Lifecycle
- Create: `POST /chat/session?course_id=...` → returns `session_id`
- Message: `POST /chat` with `course_id`, `query`, `session_id` (optional on first call)
- End: `POST /chat/end?session_id=...` (optional `delete=true`)
- Delete: `DELETE /chat/session/{id}`

Policies:
- If `session_id` is ended/deleted, reuse returns 404
- Optional inactivity TTL (future): summarize then end

## Grounded Answers
- Tutor answers strictly from the retrieved course context
- If context insufficient, politely decline and suggest materials
- Citations formatted as [1], [2] mapped to sources with titles and links

## Retrieval and Controls
- Dense vector retrieval with optional `top_k`, `threshold`
- Future: BM25 re-rank / hybrid fusion

## History and Summarization
- Last N turns + running summary (future) to keep continuity
- Summary stored in `sessions.summary_text`

## Query Rewriting (future)
- Transform follow-ups into explicit queries using short history + summary
- Examples: resolve “this”, “that slide”, “the previous definition” 