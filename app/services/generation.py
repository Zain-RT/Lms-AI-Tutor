from groq import Groq
from config import Config
import logging

logger = logging.getLogger(__name__)

class GenerationService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = Groq(api_key=Config.GROQ_API_KEY)
            cls._instance.model = Config.GROQ_MODEL
            logger.info(f"Initialized Groq client with model: {cls._instance.model}")
        return cls._instance
    
    def __init__(self):
        pass

    def generate_response(self, user_input: str, material: str = "", task_type: str = "default", template: str = None, **kwargs):
        """
        Generic AI generation function.
        - user_input: User's prompt or question.
        - material: Source material (text), optional.
        - task_type: Type of AI task (lesson, quiz, summary, etc.).
        - template: Optional custom template.
        - kwargs: Additional params for future extensibility.
        """
        # Dispatch table for task-specific templates/prompts
        task_templates = {
            "lesson": "Create a structured lesson with sections, summary, and quiz from the following material:\n{material}",
            "quiz": "Generate quiz questions from the following material:\n{material}",
            "assignment": "Generate an assignment with title, description, duedate, and grade from the following material:\n{material}",
            "summary": "Summarize the following material:\n{material}",
            "default": " This is student's questions :{user_input}\nanswer it based on context which is below :{material}"
        }

        # Select template: custom > task-specific > default
        if template:
            prompt = template.format(user_input=user_input, material=material, **kwargs)
        else:
            prompt_template = task_templates.get(task_type, task_templates["default"])
            # If material is empty, use only user_input (prompt)
            if material:
                prompt = prompt_template.format(user_input=user_input, material=material, **kwargs)
            else:
                # Fallback: use user_input as the main prompt
                if task_type in task_templates and "{material}" in prompt_template:
                    prompt = prompt_template.format(user_input=user_input, material=user_input, **kwargs)
                else:
                    prompt = user_input

        # Call the AI model (abstracted, e.g., OpenAI, local LLM, etc.)
        ai_response = self._call_ai_model(prompt)
        return ai_response

    def _call_ai_model(self, prompt: str):
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1024
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            return "I couldn't generate a response at this time."