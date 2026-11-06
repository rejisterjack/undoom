"""Anthropic Messages API capture adapter.

Records `client.messages.create` calls. Pass a tool map to run the tool loop
and record each round-trip. Importing this module does not import the Anthropic
SDK; the caller supplies a client.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from undoom.capture.context import RunRecorder
from undoom.models import ModelResponse, ToolCall
from undoom.openai_messages import safe_params, usage_dict

MAX_TURNS = 8


def wrap_anthropic(
    client: Any,
    recorder: RunRecorder,
    tools: dict[str, Callable[..., Any]] | None = None,
) -> Any:
    """Record `client.messages.create` on `recorder`.

    When `tools` is omitted, one completion is recorded and returned.
    When `tools` is provided, tool_use blocks are executed, recorded, and fed
    back until the model stops or the turn limit is hit.
    """

    messages = client.messages
    original = messages.create

    def create(*args: Any, **kwargs: Any) -> Any:
        if args:
            raise TypeError("wrap_anthropic records keyword calls to messages.create")
        if tools is None:
            response = original(**kwargs)
            _record(recorder, kwargs, response)
            return response
        return _tool_loop(original, recorder, tools, kwargs)

    messages.create = create
    return client


def parse_message(response: Any) -> ModelResponse:
    text_parts: list[str] = []
    calls: list[ToolCall] = []
    for block in getattr(response, "content", None) or []:
        block_type = getattr(block, "type", None) or (block.get("type") if isinstance(block, dict) else None)
        if block_type == "text":
            value = getattr(block, "text", None)
            if value is None and isinstance(block, dict):
                value = block.get("text")
            if value:
                text_parts.append(str(value))
        elif block_type == "tool_use":
            call_id = getattr(block, "id", None) or (block.get("id") if isinstance(block, dict) else None)
            name = getattr(block, "name", None) or (block.get("name") if isinstance(block, dict) else None)
            raw_input = getattr(block, "input", None)
            if raw_input is None and isinstance(block, dict):
                raw_input = block.get("input")
            arguments = raw_input if isinstance(raw_input, dict) else {}
            calls.append(ToolCall(id=str(call_id or ""), name=str(name or ""), arguments=arguments))
    return ModelResponse(text="\n".join(text_parts) if text_parts else None, tool_calls=calls)


def _record(recorder: RunRecorder, kwargs: dict[str, Any], response: Any) -> None:
    parsed = parse_message(response)
    recorder.record_model(
        model=str(kwargs.get("model") or getattr(response, "model", "") or ""),
        messages=list(kwargs.get("messages") or []),
        response_text=parsed.text,
        tool_calls=parsed.tool_calls,
        params=safe_params(kwargs),
        usage=usage_dict(response),
    )


def _assistant_content(response: Any) -> list[Any]:
    content = getattr(response, "content", None)
    if content is None:
        return []
    if hasattr(content, "model_dump"):
        dumped = content.model_dump()
        if isinstance(dumped, list):
            return dumped
    out: list[Any] = []
    for block in content:
        if hasattr(block, "model_dump"):
            out.append(block.model_dump())
        elif isinstance(block, dict):
            out.append(block)
        else:
            out.append(
                {
                    "type": getattr(block, "type", None),
                    "text": getattr(block, "text", None),
                    "id": getattr(block, "id", None),
                    "name": getattr(block, "name", None),
                    "input": getattr(block, "input", None),
                }
            )
    return out


def _tool_result_message(call_id: str, result: Any, error: str | None) -> dict[str, Any]:
    if error is not None:
        body: Any = {"error": error}
        if result is not None:
            body["result"] = result
    else:
        body = result
    return {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": call_id,
                "content": json.dumps(body, default=str),
            }
        ],
    }


def _tool_loop(
    create: Callable[..., Any],
    recorder: RunRecorder,
    tools: dict[str, Callable[..., Any]],
    kwargs: dict[str, Any],
) -> Any:
    messages = list(kwargs.get("messages") or [])
    last = None
    for _ in range(MAX_TURNS):
        pending = dict(kwargs)
        pending["messages"] = messages
        response = create(**pending)
        last = response
        parsed = parse_message(response)
        _record(recorder, pending, response)
        if not parsed.tool_calls:
            return response
        messages.append({"role": "assistant", "content": _assistant_content(response)})
        for call in parsed.tool_calls:
            function = tools.get(call.name)
            if function is None:
                with recorder.tool(call.name, call.arguments, call_id=call.id) as handle:
                    handle.record({"error": f"unknown tool {call.name}"})
                recorder.fail(f"unknown tool {call.name}", unexpected_tools=[call.name])
                messages.append(
                    _tool_result_message(call.id, {"error": f"unknown tool {call.name}"}, "unknown tool")
                )
                return response
            with recorder.tool(call.name, call.arguments, call_id=call.id) as handle:
                result = function(**call.arguments)
                handle.record(result)
            messages.append(_tool_result_message(call.id, result, None))
    return last
