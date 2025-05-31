# services/generation.py
from groq import Groq
from config import Config
import logging

class GenerationService:
    def __init__(self):
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = Config.GROQ_MODEL
        logging.info(f"Initialized Groq client with model: {self.model}")

    def generate_response(self, context: str, query: str) -> str:
        """Generate answer using Groq LLM"""
        try:
            prompt = f"""You are a helpful course assistant. Use this context to answer the question.
            If unsure, say you don't know. Be concise and accurate.

            Context:
            {context}

            Question: {query}

            Answer:"""
            
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=1024
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Generation error: {str(e)}")
            return "I couldn't generate a response at this time."