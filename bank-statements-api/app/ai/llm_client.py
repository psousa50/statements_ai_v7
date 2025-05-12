from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

    @abstractmethod
    async def generate_async(self, prompt: str) -> str:
        pass
