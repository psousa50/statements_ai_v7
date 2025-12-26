import logging
import os
from typing import Optional

from groq import Groq

from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


class GroqAI(LLMClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "llama-3.3-70b-versatile",
        temperature: float = 0,
    ):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided either as an argument or as GROQ_API_KEY environment variable")

        self.model_name = model_name
        self.temperature = temperature
        self.client = Groq(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Error generating response: %s", str(e))
            raise Exception(f"Error generating response: {str(e)}")

    async def generate_async(self, prompt: str) -> str:
        return self.generate(prompt)
