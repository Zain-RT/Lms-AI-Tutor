import sqlite3
import threading
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from config import Config

_DB_PATH = Path(Config.STORAGE_PATH) / "state.sqlite"
_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        course_id TEXT NOT NULL,
        title TEXT,
        summary_text TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL,
        last_active_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_course ON sessions(course_id, last_active_at);",
]


class SessionStore:
    _lock = threading.RLock()

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or _DB_PATH)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn, self._lock:
            cur = conn.cursor()
            for stmt in _SCHEMA:
                cur.execute(stmt)
            conn.commit()

    def create_session(self, course_id: str, title: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self._connect() as conn, self._lock:
            conn.execute(
                "INSERT INTO sessions(id, course_id, title, summary_text, status, created_at, last_active_at) VALUES (?, ?, ?, ?, 'active', ?, ?)",
                (session_id, course_id, title, "", now, now),
            )
            conn.commit()
        return session_id

    def end_session(self, session_id: str, summary_text: Optional[str] = None) -> Optional[str]:
        with self._connect() as conn, self._lock:
            # If no summary provided, build a naive one from last few messages
            if not summary_text:
                msgs = self.get_messages(session_id, limit=6)
                parts = []
                for m in msgs:
                    role = m.get("role", "user").capitalize()
                    content = m.get("content", "")
                    parts.append(f"{role}: {content}")
                summary_text = "\n".join(parts)[:2000]
            now = datetime.utcnow().isoformat()
            conn.execute(
                "UPDATE sessions SET status='ended', summary_text=?, last_active_at=? WHERE id=?",
                (summary_text or "", now, session_id),
            )
            conn.commit()
            return summary_text or ""

    def add_message(self, session_id: str, role: str, content: str) -> None:
        msg_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        with self._connect() as conn, self._lock:
            conn.execute(
                "INSERT INTO messages(id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, now),
            )
            conn.execute(
                "UPDATE sessions SET last_active_at=? WHERE id=?",
                (now, session_id),
            )
            conn.commit()

    def get_messages(self, session_id: str, limit: int = 12) -> List[Dict]:
        with self._connect() as conn, self._lock:
            cur = conn.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            )
            rows = list(cur.fetchall())
        rows.reverse()
        return [dict(r) for r in rows]

    def get_session_messages(self, session_id: str, limit: int = 200) -> List[Dict]:
        with self._connect() as conn, self._lock:
            cur = conn.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id=? ORDER BY created_at ASC LIMIT ?",
                (session_id, limit),
            )
            return [dict(r) for r in cur.fetchall()]

    def delete_session(self, session_id: str) -> None:
        with self._connect() as conn, self._lock:
            conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
            conn.commit()

    def session_exists(self, session_id: str) -> bool:
        with self._connect() as conn, self._lock:
            cur = conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,))
            return cur.fetchone() is not None

    def list_sessions(self, course_id: str, limit: int = 20) -> List[Dict]:
        with self._connect() as conn, self._lock:
            cur = conn.execute(
                "SELECT id, title, status, created_at, last_active_at FROM sessions WHERE course_id=? ORDER BY last_active_at DESC LIMIT ?",
                (course_id, limit),
            )
            return [dict(r) for r in cur.fetchall()] 