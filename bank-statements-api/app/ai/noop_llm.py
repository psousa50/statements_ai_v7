from collections.abc import AsyncGenerator
from typing import Any, Callable

from app.ai.llm_client import LLMClient


class NoopLLMClient(LLMClient):
    def generate(self, prompt: str) -> str:
        return ""

    async def generate_async(self, prompt: str) -> str:
        return ""

    async def generate_with_tools(
        self,
        contents: list[dict[str, Any]],
        tools: list[Callable],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        yield {"type": "text", "content": "Chat is not available in test mode."}
        yield {"type": "done"}
