# from utils.moodle_helpers import download_file, extract_file_text
# from services.generation import GenerationService
# from uuid import uuid4
# from schemas import LessonCreateRequest, LessonCreateResponse, LessonSection

# class LessonService:
#     async def create_lesson(self, request: LessonCreateRequest) -> LessonCreateResponse:
#         # 1. Download material
#         file_path = download_file(request.material_url, suffix=f".{request.material_type}")
#         # 2. Extract text (for video, use speech-to-text)
#         if request.material_type in ["pdf", "pptx", "docx"]:
#             text = extract_file_text(file_path, f".{request.material_type}")
#         elif request.material_type == "video":
#             text = self.extract_video_text(file_path)
#         else:
#             raise ValueError("Unsupported material type")
#         # 3. Generate lesson sections using AI
#         prompt = request.prompt or (
#             "Create a structured lesson with sections, summary, and quiz from the following material."
#         )
#         ai_input = f"{prompt}\n\nMaterial:\n{text}"
#         ai = GenerationService()
#         lesson_content = ai.generate_response("", ai_input)
#         # 4. Parse AI output (assume JSON or markdown structure)
#         sections, summary, quiz = self.parse_lesson_content(lesson_content)
#         # 5. Store lesson (could be DB or file, here just return)
#         lesson_id = str(uuid4())
#         return LessonCreateResponse(
#             lesson_id=lesson_id,
#             title=request.title,
#             sections=sections,
#             summary=summary,
#             quiz=quiz
#         )

#     def extract_video_text(self, file_path: str) -> str:
#         # Placeholder: integrate with speech-to-text service
#         return "Transcribed video text (implement speech-to-text here)"

#     def parse_lesson_content(self, ai_output: str):
#         # Placeholder: parse AI output into sections, summary, quiz
#         # For now, return dummy data
#         return (
#             [LessonSection(heading="Introduction", content=ai_output)],
#             "Summary goes here.",
#             [{"question": "Sample Q?", "answer": "Sample A"}]
#         )