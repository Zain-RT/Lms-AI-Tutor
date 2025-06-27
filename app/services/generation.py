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
    
    def generate_response(self, context: str, query: str) -> str:
        try:
            prompt = f"""You are a helpful course assistant. Use ONLY the context below to answer the question.
            If the answer isn't in the context, say you don't know. Be concise and accurate.
            Include source numbers like [1] when using specific information.
            
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
            logger.error(f"Generation error: {str(e)}")
            return "I couldn't generate a response at this time."