from app.ai.llm_client import LLMClient


class NoopLLMClient(LLMClient):
    def generate(self, prompt: str) -> str:
        return ""

    async def generate_async(self, prompt: str) -> str:
        return ""
