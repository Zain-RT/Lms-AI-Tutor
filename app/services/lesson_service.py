import json
import os
from uuid import uuid4
from pathlib import Path
from typing import List, Tuple

from utils.moodle_helpers import download_file, extract_file_text
from services.generation import GenerationService
from services.index_manager import IndexManager
from utils.llama_helpers import create_document
from schemas import LessonCreateRequest, LessonCreateResponse, LessonSection
from config import Config


class LessonService:
    def __init__(self):
        self.index_manager = IndexManager()

    async def create_lesson(self, request: LessonCreateRequest) -> LessonCreateResponse:
        # 1) Download and extract material
        file_path, text = self._load_material(request.material_url, request.material_type)

        # 2) Generate lesson content (strict JSON)
        template = (
            "You are a teaching assistant. Create a structured lesson ONLY as strict JSON matching this schema without any extra text or markdown.\n"
            "Schema:\n"
            "{\n"
            "  \"title\": string,\n"
            "  \"summary\": string,\n"
            "  \"sections\": [ { \"heading\": string, \"content\": string } ],\n"
            "  \"quiz\": [ { \"questiontext\": string, \"answers\": [string], \"correct\": number } ]\n"
            "}\n\n"
            "Material:\n{material}\n\n"
            "User prompt (optional): {user_input}\n"
            "Respond with JSON only."
        )

        ai = GenerationService()
        ai_output = ai.generate_response(
            user_input=request.prompt or "",
            material=text,
            task_type="lesson",
            template=template,
        )

        title, summary, sections, quiz = self._parse_lesson_json(ai_output)

        # 3) Persist lesson locally
        lesson_id = str(uuid4())
        self._persist_lesson(request.course_id, lesson_id, title, summary, sections, quiz)

        # 4) Index lesson content back into course index
        self._index_lesson(request.course_id, title, sections)

        # 5) Return structured response
        return LessonCreateResponse(
            lesson_id=lesson_id,
            title=title,
            sections=[LessonSection(heading=s.heading, content=s.content) for s in sections],
            summary=summary,
            quiz=quiz,
        )

    def _load_material(self, material_url: str, material_type: str) -> Tuple[str, str]:
        suffix = f".{material_type.lower()}" if not material_type.startswith(".") else material_type
        file_path = download_file(material_url, suffix=suffix)
        if material_type.lower() in ["pdf", "pptx", "docx"]:
            text = extract_file_text(file_path, suffix)
        elif material_type.lower() in ["mp4", "avi", "mov", "mkv"]:
            # Placeholder: implement transcription later
            raise ValueError("Video transcription not implemented yet. Please use pdf/pptx/docx for now.")
        else:
            raise ValueError(f"Unsupported material type: {material_type}")
        return file_path, text

    def _parse_lesson_json(self, ai_output: str) -> Tuple[str, str, List[LessonSection], list]:
        try:
            data = json.loads(ai_output)
            title = data.get("title") or "Lesson"
            summary = data.get("summary") or ""
            sections_raw = data.get("sections") or []
            sections = [LessonSection(heading=s.get("heading", "Section"), content=s.get("content", "")) for s in sections_raw]
            quiz = data.get("quiz") or []
            return title, summary, sections, quiz
        except Exception:
            # Fallback: wrap as a single section
            return "Lesson", "", [LessonSection(heading="Content", content=ai_output)], []

    def _persist_lesson(self, course_id: str, lesson_id: str, title: str, summary: str, sections: List[LessonSection], quiz: list) -> None:
        base = Path(Config.STORAGE_PATH) / "lessons" / f"course_{course_id}"
        os.makedirs(base, exist_ok=True)
        payload = {
            "lesson_id": lesson_id,
            "title": title,
            "summary": summary,
            "sections": [s.model_dump() for s in sections],
            "quiz": quiz,
        }
        out_path = base / f"lesson_{lesson_id}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    def _index_lesson(self, course_id: str, title: str, sections: List[LessonSection]) -> None:
        docs = []
        for section in sections:
            text = f"{section.heading}\n\n{section.content}"
            metadata = {
                "type": "generated_lesson",
                "title": title,
                "section_heading": section.heading,
                "source": "generated",
                "course_id": course_id,
            }
            docs.append(create_document(text, metadata))
        if docs:
            self.index_manager.add_documents(course_id, docs)