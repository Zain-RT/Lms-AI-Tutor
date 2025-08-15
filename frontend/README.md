# Frontend Tester for Moodle Course Bot

A minimal static frontend to test chat endpoints:
- Create session: POST `/chat/session`
- Chat: POST `/chat`
- End session (with optional delete): POST `/chat/end`
- Delete session: DELETE `/chat/session/{session_id}`

## Run locally

- Option 1: Open directly
  - Open `frontend/index.html` in your browser (may be restricted by some browsers for fetch requests).

- Option 2: Serve via HTTP (recommended)
  - From repo root:
    ```bash
    python3 -m http.server 8080
    ```
  - Open `http://127.0.0.1:8080/frontend/index.html`

Ensure the FastAPI server is running (default `http://127.0.0.1:8000`). Update the API base URL in the UI if needed. 