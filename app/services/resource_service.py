from utils.moodle_helpers import download_file, extract_file_text
from services.generation import GenerationService
from schemas import ResourceGenerateRequest, ResourceGenerateResponse, LessonPage, QuizQuestion

class ResourceService:
    async def generate(self, request: ResourceGenerateRequest) -> ResourceGenerateResponse:
        # 1. Parse file if provided
        material = ""
        if request.file_url:
            ext = request.file_url.split('.')[-1].lower()
            file_path = download_file(request.file_url, suffix=f".{ext}")
            if ext in ["pdf", "pptx", "docx"]:
                material = extract_file_text(file_path, f".{ext}")
            elif ext in ["mp4", "avi"]:
                material = self.extract_video_text(file_path)
            else:
                raise ValueError("Unsupported file type")
        # 2. Compose AI prompt
        prompt = request.prompt or self.default_prompt(request.type)
        ai_input = f"{prompt}\n\nMaterial:\n{material}" if material else prompt
        print(f"AI Input: {ai_input}")  # Debugging output
        # 3. Generate resource using AI
        ai = GenerationService()
        ai_output = ai.generate_response(
            user_input=ai_input,
            material=material,
            task_type=request.type,
            options=request.options or {}
        )
        print(f"AI Output: {ai_output}")  # Debugging output
        # 4. Parse AI output into structured response
        return self.parse_output(request.type, ai_output, request.options)

    def default_prompt(self, resource_type: str) -> str:
        if resource_type == "lesson":
            return "Create a structured lesson with summary and pages from the following material."
        if resource_type == "assignment":
            return "Generate an assignment with title, description, duedate, and grade."
        if resource_type == "quiz":
            return "Generate a quiz with title, description, questions, grade, and attempts."
        return "Generate resource."

    def extract_video_text(self, file_path: str) -> str:
        # Placeholder for speech-to-text
        return "Transcribed video text (implement speech-to-text here)"

    def parse_output(self, resource_type: str, ai_output: str, options: dict) -> ResourceGenerateResponse:
        # In production, parse AI output (JSON/Markdown). Here, dummy logic:
        if resource_type == "lesson":
            return ResourceGenerateResponse(
                type="lesson",
                title="Lesson on Climate Change",
                summary="This lesson explains causes and solutions of climate change.",
                pages=[
                    LessonPage(title="Introduction", content="Climate change refers to..."),
                    LessonPage(title="Causes", content="<ul><li>Fossil fuels</li><li>Deforestation</li></ul>")
                ]
            )
        if resource_type == "assignment":
            return ResourceGenerateResponse(
                type="assignment",
                title="Essay: Renewable Energy",
                description="Write a 1000-word essay on why renewable energy matters.",
                duedate=options.get("duedate"),
                grade=options.get("grade", 100)
            )
        if resource_type == "quiz":
            return ResourceGenerateResponse(
                type="quiz",
                title="Climate Change Quiz",
                description="A short quiz on the basics of climate change.",
                questions=[
                    QuizQuestion(
                        questiontext="What gas is the primary cause of global warming?",
                        answers=["O₂", "CO₂", "N₂"],
                        correct=1
                    ),
                    QuizQuestion(
                        questiontext="Which of these is a renewable energy source?",
                        answers=["Coal", "Solar", "Gasoline"],
                        correct=1
                    )
                ],
                grade=options.get("grade", 100),
                attempts=options.get("attempts", 1)
            )
        raise ValueError("Unknown resource type")