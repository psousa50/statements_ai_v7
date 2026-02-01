import inspect
import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any, Callable, Optional, Union, get_type_hints

from groq import Groq

from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _get_base_type(type_hint):
    origin = getattr(type_hint, "__origin__", None)
    if origin is Union:
        args = [a for a in type_hint.__args__ if a is not type(None)]
        return args[0] if args else str
    return type_hint


def _function_to_tool_schema(func: Callable) -> dict:
    hints = get_type_hints(func)
    sig = inspect.signature(func)
    props = {}
    required = []

    for name, param in sig.parameters.items():
        param_type = _get_base_type(hints.get(name, str))
        json_type = "string"
        if param_type is int:
            json_type = "integer"
        elif param_type is float:
            json_type = "number"
        elif param_type is bool:
            json_type = "boolean"

        props[name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {"type": "object", "properties": props, "required": required},
        },
    }


def _coerce_args(func: Callable, args: dict | None) -> dict:
    if not args:
        return {}
    hints = get_type_hints(func)
    coerced = {}
    for key, value in args.items():
        if value is None:
            coerced[key] = None
            continue
        expected_type = _get_base_type(hints.get(key, str))
        try:
            if expected_type is int:
                coerced[key] = int(value)
            elif expected_type is float:
                coerced[key] = float(value)
            elif expected_type is bool:
                coerced[key] = value if isinstance(value, bool) else str(value).lower() in ("true", "1")
            else:
                coerced[key] = value
        except (ValueError, TypeError):
            coerced[key] = value
    return coerced


class GroqAI(LLMClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "llama-3.1-8b-instant",
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

    async def generate_with_tools(
        self,
        contents: list[dict[str, Any]],
        tools: list[Callable],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        tool_schemas = [_function_to_tool_schema(t) for t in tools]
        tool_map = {t.__name__: t for t in tools}

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for msg in contents:
            role = "assistant" if msg["role"] == "assistant" else msg["role"]
            messages.append({"role": role, "content": msg["content"]})

        max_tool_calls = 10
        tool_call_count = 0

        while tool_call_count < max_tool_calls:
            logger.info("=== GROQ REQUEST ===")
            logger.info(f"Model: {self.model_name}")
            logger.info(f"Messages: {json.dumps(messages, indent=2, default=str)}")
            logger.info(f"Tools: {json.dumps(tool_schemas, indent=2)}")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tool_schemas,
                tool_choice="auto",
                temperature=self.temperature,
            )

            choice = response.choices[0]
            message = choice.message

            logger.info("=== GROQ RESPONSE ===")
            logger.info(f"Content: {message.content}")
            logger.info(f"Tool calls: {message.tool_calls}")
            logger.info(f"Finish reason: {choice.finish_reason}")

            if not message.tool_calls:
                if message.content:
                    yield {"type": "text", "content": message.content}
                yield {"type": "done"}
                return

            tool_call_count += 1
            messages.append({"role": "assistant", "tool_calls": message.tool_calls, "content": message.content or ""})

            for tc in message.tool_calls:
                func = tool_map.get(tc.function.name)
                if func:
                    try:
                        args = json.loads(tc.function.arguments)
                        args = _coerce_args(func, args)
                        result = await func(**args)
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
                        yield {"type": "data", "function": tc.function.name, "data": result}
                    except Exception as e:
                        logger.error("Tool execution error for %s: %s", tc.function.name, str(e))
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps({"error": str(e)})})
                else:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps({"error": f"Unknown function: {tc.function.name}"}),
                        }
                    )

        yield {"type": "error", "content": "Maximum tool calls exceeded"}
