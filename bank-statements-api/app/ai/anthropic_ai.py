import inspect
import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any, Callable, Optional, Union, get_type_hints

import anthropic

from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


def _is_optional(type_hint) -> bool:
    origin = getattr(type_hint, "__origin__", None)
    if origin is Union:
        return type(None) in type_hint.__args__
    return False


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
        hint = hints.get(name, str)
        param_type = _get_base_type(hint)
        json_type = "string"
        if param_type is int:
            json_type = "integer"
        elif param_type is float:
            json_type = "number"
        elif param_type is bool:
            json_type = "boolean"

        if _is_optional(hint):
            props[name] = {"type": [json_type, "null"]}
        else:
            props[name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "name": func.__name__,
        "description": func.__doc__ or "",
        "input_schema": {"type": "object", "properties": props, "required": required},
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


class AnthropicAI(LLMClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "claude-haiku-4-5-20251001",
        temperature: float = 0,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided either as an argument or as ANTHROPIC_API_KEY environment variable")

        self.model_name = model_name
        self.temperature = temperature
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )
            return response.content[0].text if response.content else ""
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
        for msg in contents:
            messages.append({"role": msg["role"], "content": msg["content"]})

        max_tool_calls = 10
        tool_call_count = 0

        while tool_call_count < max_tool_calls:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                system=system_prompt or "",
                messages=messages,
                tools=tool_schemas,
                temperature=self.temperature,
            )

            if response.stop_reason != "tool_use":
                for block in response.content:
                    if block.type == "text" and block.text:
                        yield {"type": "text", "content": block.text}
                yield {"type": "done"}
                return

            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            tool_call_count += len(tool_use_blocks)

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in tool_use_blocks:
                func = tool_map.get(block.name)
                if func:
                    try:
                        args = _coerce_args(func, block.input)
                        result = await func(**args)
                        tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)})
                        yield {"type": "data", "function": block.name, "data": result}
                    except Exception as e:
                        logger.error("Tool execution error for %s: %s", block.name, str(e))
                        tool_results.append(
                            {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps({"error": str(e)})}
                        )
                else:
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps({"error": f"Unknown function: {block.name}"}),
                        }
                    )

            messages.append({"role": "user", "content": tool_results})

        yield {"type": "error", "content": "Maximum tool calls exceeded"}
