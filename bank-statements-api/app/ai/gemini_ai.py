import logging
import os
from collections.abc import AsyncGenerator
from typing import Any, Callable, Optional

import google.generativeai as genai
from google import genai as genai_new
from google.genai import types

from app.ai.llm_client import LLMClient

logger_content = logging.getLogger("app.llm.big")
logger = logging.getLogger("app")


class GeminiAI(LLMClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-2.0-flash",
        temperature: float = 0,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided either as an argument or as GEMINI_API_KEY environment variable")

        self.model_name = model_name
        self.temperature = temperature

        genai.configure(api_key=self.api_key)

        self.model = genai.GenerativeModel(
            model_name=self.model_name,
        )

        self.client = genai_new.Client(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error("Error generating response: %s", str(e))
            raise Exception(f"Error generating response: {str(e)}")

    async def generate_async(self, prompt: str) -> str:
        try:
            response = await self.model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            logger.error("Error generating response: %s", str(e))
            raise Exception(f"Error generating response: {str(e)}")

    async def generate_with_tools(
        self,
        contents: list[dict[str, Any]],
        tools: list[Callable],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        config = types.GenerateContentConfig(
            tools=tools,
            system_instruction=system_prompt,
            temperature=self.temperature,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        genai_contents = self._convert_contents(contents)
        max_tool_calls = 5
        tool_call_count = 0

        while tool_call_count < max_tool_calls:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=genai_contents,
                config=config,
            )

            candidate = response.candidates[0]

            if not response.function_calls:
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            yield {"type": "text", "content": part.text}
                yield {"type": "done"}
                return

            tool_call_count += 1
            genai_contents.append(candidate.content)

            function_responses = []
            for fc in response.function_calls:
                tool_func = next((t for t in tools if t.__name__ == fc.name), None)
                if tool_func:
                    try:
                        result = await tool_func(**fc.args)
                        function_responses.append(types.Part.from_function_response(name=fc.name, response={"result": result}))
                        yield {"type": "data", "function": fc.name, "data": result}
                    except Exception as e:
                        logger.error("Tool execution error for %s: %s", fc.name, str(e))
                        function_responses.append(types.Part.from_function_response(name=fc.name, response={"error": str(e)}))
                else:
                    function_responses.append(
                        types.Part.from_function_response(name=fc.name, response={"error": f"Unknown function: {fc.name}"})
                    )

            genai_contents.append(types.Content(role="tool", parts=function_responses))

        yield {"type": "error", "content": "Maximum tool calls exceeded"}

    def _convert_contents(self, contents: list[dict[str, Any]]) -> list[types.Content]:
        result = []
        for msg in contents:
            role = "model" if msg["role"] == "assistant" else msg["role"]
            result.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
        return result
