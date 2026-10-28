"""Shared helpers for OpenAI-shaped chat completions."""

from __future__ import annotations

import json
from typing import Any

from undoom.models import ModelResponse, ToolCall


def coerce_arguments(arguments: Any) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str):
        if not arguments.strip():
            return {}
        loaded = json.loads(arguments)
        if not isinstance(loaded, dict):
            raise ValueError("tool arguments must be a JSON object")
        return loaded
    raise ValueError("tool arguments must be an object")


def parse_completion(response: Any) -> ModelResponse:
    message = response.choices[0].message
    calls: list[ToolCall] = []
    for tool_call in getattr(message, "tool_calls", None) or []:
        calls.append(
            ToolCall(
                id=tool_call.id,
                name=tool_call.function.name,
                arguments=coerce_arguments(tool_call.function.arguments),
            )
        )
    return ModelResponse(text=getattr(message, "content", None), tool_calls=calls)


def usage_dict(response: Any) -> dict[str, Any] | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    if hasattr(usage, "model_dump"):
        dumped = usage.model_dump()
        if isinstance(dumped, dict):
            return dumped
    if isinstance(usage, dict):
        return usage
    return None


def assistant_message(text: str | None, tool_calls: list[ToolCall]) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "assistant", "content": text or ""}
    if tool_calls:
        message["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments, sort_keys=True),
                },
            }
            for call in tool_calls
        ]
    return message


def tool_message(call_id: str, result: Any, error: str | None) -> dict[str, Any]:
    if error is not None:
        body: Any = {"error": error}
        if result is not None:
            body["result"] = result
    else:
        body = result
    return {
        "role": "tool",
        "tool_call_id": call_id,
        "content": json.dumps(body, default=str),
    }


def safe_params(kwargs: dict[str, Any]) -> dict[str, Any]:
    kept: dict[str, Any] = {}
    for key in ("temperature", "tools", "tool_choice", "top_p"):
        if key in kwargs:
            kept[key] = kwargs[key]
    return kept
