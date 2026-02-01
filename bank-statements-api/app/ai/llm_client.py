from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any, Callable


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

    @abstractmethod
    async def generate_async(self, prompt: str) -> str:
        pass

    async def generate_with_tools(
        self,
        contents: list[dict[str, Any]],
        tools: list[Callable],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        yield {"type": "error", "content": "Tool-based generation not supported by this client"}
