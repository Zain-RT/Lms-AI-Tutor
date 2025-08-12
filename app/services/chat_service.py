from typing import List, Dict, Optional, Tuple
from uuid import uuid4
import logging

from services.index_manager import IndexManager
from services.generation import GenerationService

logger = logging.getLogger(__name__)


class ChatService:
    _instance = None
    _sessions: Dict[str, List[Dict[str, str]]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.index_manager = IndexManager()
            cls._instance.generator = GenerationService()
        return cls._instance

    def _ensure_session(self, session_id: Optional[str]) -> Optional[str]:
        if session_id is None:
            return None
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return session_id

    def _append_history(self, session_id: Optional[str], role: str, content: str) -> None:
        if session_id is None:
            return
        self._sessions.setdefault(session_id, []).append({"role": role, "content": content})
        # keep last 12 turns max
        self._sessions[session_id] = self._sessions[session_id][-12:]

    def _format_history(self, session_id: Optional[str]) -> str:
        if session_id is None or session_id not in self._sessions:
            return ""
        return "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in self._sessions[session_id]])

    def _nodes_to_context_and_sources(self, nodes: List) -> Tuple[str, List[Dict]]:
        context_lines: List[str] = []
        sources: List[Dict] = []
        for idx, node in enumerate(nodes):
            text = getattr(node, "text", None)
            if text is None and hasattr(node, "get_content"):
                try:
                    text = node.get_content()
                except Exception:
                    text = ""
            score = getattr(node, "score", 0.0)
            metadata = getattr(node, "metadata", {}) or {}
            context_lines.append(f"[{idx+1}] (score={float(score):.2f})\n{text}")
            sources.append({
                "text": text or "",
                "score": float(score) if isinstance(score, (int, float)) else 0.0,
                "metadata": metadata,
            })
        return "\n\n".join(context_lines), sources

    def chat(self, *, course_id: str, query: str, top_k: Optional[int] = None, threshold: Optional[float] = None, session_id: Optional[str] = None) -> Dict:
        # Ensure session if provided
        session_id = self._ensure_session(session_id)

        # Retrieve
        nodes = self.index_manager.search(course_id, query, top_k=top_k)
        if threshold is not None:
            try:
                nodes = [n for n in nodes if getattr(n, "score", None) is not None and float(n.score) >= float(threshold)]
            except Exception:
                pass

        # If no context
        if not nodes:
            answer = "I couldn’t find relevant information in this course to answer that."
            if session_id:
                self._append_history(session_id, "user", query)
                self._append_history(session_id, "assistant", answer)
            return {"answer": answer, "sources": []}

        # Build system prompt and context
        system_prompt = (
            "You are a virtual tutor strictly grounded to the provided course context. "
            "Answer only using information from Context. If the answer is not in Context, say you don’t have enough information. "
            "Be concise, helpful, and include citations like [1], [2] that map to the sources."
        )
        context, sources = self._nodes_to_context_and_sources(nodes)
        history_str = self._format_history(session_id)

        # Compose template
        template = (
            "System:\n{system_prompt}\n\n"
            "Context:\n{material}\n\n"
            "Conversation so far:\n{history}\n\n"
            "User:\n{user_input}\n\n"
            "Assistant:"
        )

        # Append user message to history
        if session_id:
            self._append_history(session_id, "user", query)

        # Generate
        answer = self.generator.generate_response(
            user_input=query,
            material=context,
            task_type="chat",
            template=template,
            system_prompt=system_prompt,
            history=history_str,
        )

        if session_id:
            self._append_history(session_id, "assistant", answer)

        return {"answer": answer, "sources": sources} 