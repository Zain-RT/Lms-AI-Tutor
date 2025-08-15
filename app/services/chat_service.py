from typing import List, Dict, Optional, Tuple, Set
from uuid import uuid4
import logging
from itertools import chain

from services.index_manager import IndexManager
from services.generation import GenerationService
from services.session_store import SessionStore

logger = logging.getLogger(__name__)


class ChatService:
    _instance = None
    _sessions: Dict[str, List[Dict[str, str]]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.index_manager = IndexManager()
            cls._instance.generator = GenerationService()
            cls._instance.session_store = SessionStore()
        return cls._instance

    def _ensure_session(self, session_id: Optional[str]) -> Optional[str]:
        if session_id is None:
            return None
        # initialize in-memory cache for quick short context (still persisted to DB)
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        return session_id

    def _append_history(self, session_id: Optional[str], role: str, content: str) -> None:
        if session_id is None:
            return
        self._sessions.setdefault(session_id, []).append({"role": role, "content": content})
        # keep last 12 turns max
        self._sessions[session_id] = self._sessions[session_id][-12:]
        # persist
        try:
            self.session_store.add_message(session_id, role, content)
        except Exception as e:
            logger.error(f"Failed to persist message for session {session_id}: {e}")

    def _format_history(self, session_id: Optional[str]) -> str:
        if session_id is None:
            return ""
        try:
            msgs = self.session_store.get_messages(session_id, limit=12)
            return "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in msgs])
        except Exception as e:
            logger.error(f"Failed to load messages for session {session_id}: {e}")
            return "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in self._sessions.get(session_id, [])])

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

    def _expand_queries(self, base_query: str, num: int, history: str) -> List[str]:
        """Use LLM to generate paraphrases/expansions for retrieval."""
        template = (
            "You expand a student's question into {num} alternative search queries focused on the same topic.\n"
            "Conversation so far (optional):\n{history}\n\n"
            "Original question: {q}\n\n"
            "Return ONLY the queries, one per line, concise and course-specific."
        )
        logger.debug("chat.expand: generating up to %d for %r", num, base_query)
        try:
            text = self.generator.generate_response(
                user_input=base_query,
                material="",
                task_type="default",
                template=template,
                num=num,
                history=history or "",
                q=base_query,
            )
        except Exception as e:
            logger.warning("chat.expand: generation failed: %s", e)
            return []
        queries = [line.strip("- • ").strip() for line in text.splitlines() if line.strip()]
        out: List[str] = []
        for q in queries:
            if q and q.lower() != base_query.lower() and q not in out:
                out.append(q)
            if len(out) >= num:
                break
        logger.debug("chat.expand: got %d → %s", len(out), out)
        return out

    def _merge_results(self, results_lists: List[List], max_k: int) -> List:
        """Merge nodes from multiple queries with simple de-dup (by text) and take top by score."""
        seen: Set[str] = set()
        merged: List = []
        for nodes in results_lists:
            for n in nodes:
                key = getattr(n, "text", None) or getattr(n, "get_content", lambda: "")()
                if not key:
                    continue
                if key in seen:
                    continue
                seen.add(key)
                merged.append(n)
        # Sort descending by score if available
        merged.sort(key=lambda x: float(getattr(x, "score", 0.0) or 0.0), reverse=True)
        logger.info("chat.select: merged=%d return=%d", len(merged), max_k)
        return merged[:max_k]

    def chat(self, *, course_id: str, query: str, top_k: Optional[int] = None, threshold: Optional[float] = None, session_id: Optional[str] = None, expand: bool = False, num_expansions: int = 3, top_k_per_query: Optional[int] = None) -> Dict:
        # Validate/ensure session if provided
        session_id = self._ensure_session(session_id)

        logger.info(
            "chat.request: course=%s sid=%s expand=%s top_k=%s thr=%s", course_id, session_id, expand, top_k, threshold
        )

        if session_id is not None and not self.session_store.session_exists(session_id):
            return {"answer": "This chat session has ended. Please start a new chat.", "sources": []}

        # Retrieve (optionally with query expansion)
        effective_top_k = top_k or 5
        per_query_k = top_k_per_query or effective_top_k
        results_lists: List[List] = []

        history_str = self._format_history(session_id)

        if expand:
            expansions = self._expand_queries(query, num=num_expansions, history=history_str)
            all_queries = [query] + expansions
            logger.info("chat.expand: base+alt=%d", len(all_queries))
            logger.debug("chat.expand.queries=%s", all_queries)
        else:
            all_queries = [query]

        for q in all_queries:
            nodes = self.index_manager.search(course_id, q, top_k=per_query_k)
            top_score = 0.0
            if nodes:
                try:
                    top_score = float(getattr(nodes[0], "score", 0.0) or 0.0)
                except Exception:
                    top_score = 0.0
            logger.debug("chat.retrieve: q=%r nodes=%d top=%.2f", q, len(nodes or []), top_score)
            if threshold is not None:
                try:
                    before = len(nodes)
                    nodes = [n for n in nodes if getattr(n, "score", None) is not None and float(n.score) >= float(threshold)]
                    logger.debug("chat.filter: thr=%s kept %d/%d", threshold, len(nodes), before)
                except Exception as e:
                    logger.debug("chat.filter: failed: %s", e)
            results_lists.append(nodes)

        nodes = self._merge_results(results_lists, max_k=effective_top_k)
        logger.info("chat.select: final=%d", len(nodes))

        # If no context
        if not nodes:
            answer = "I couldn’t find relevant information in this course to answer that."
            if session_id:
                self._append_history(session_id, "user", query)
                self._append_history(session_id, "assistant", answer)
            logger.info("chat.answer: no-context fallback")
            return {"answer": answer, "sources": []}

        # Build system prompt and context
        system_prompt = (
            "You are a virtual tutor strictly grounded to the provided course context. "
            "Answer only using information from Context. If the answer is not in Context, say you don’t have enough information. "
            "Be concise, helpful, and include citations like [1], [2] that map to the sources."
        )
        context, sources = self._nodes_to_context_and_sources(nodes)

        # Append user message to history
        if session_id:
            self._append_history(session_id, "user", query)

        # Compose template
        template = (
            "System:\n{system_prompt}\n\n"
            "Context:\n{material}\n\n"
            "Conversation so far:\n{history}\n\n"
            "User:\n{user_input}\n\n"
            "Assistant:"
        )

        # Generate
        answer = self.generator.generate_response(
            user_input=query,
            material=context,
            task_type="chat",
            template=template,
            system_prompt=system_prompt,
            history=history_str,
        )
        logger.info("chat.answer: length=%d", len(answer or ""))

        if session_id:
            self._append_history(session_id, "assistant", answer)

        return {"answer": answer, "sources": sources} 