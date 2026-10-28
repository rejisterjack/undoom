"""OpenAI chat-completions adapter.

The adapter records model calls. Pass a tool map and it also runs the tool
loop, recording each round-trip. Importing this module does not import the
OpenAI SDK; the caller supplies a client.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from undoom.capture.context import RunRecorder
from undoom.openai_messages import (
    assistant_message,
    parse_completion,
    safe_params,
    tool_message,
    usage_dict,
)

MAX_TURNS = 8


def wrap_openai(
    client: Any,
    recorder: RunRecorder,
    tools: dict[str, Callable[..., Any]] | None = None,
) -> Any:
    """Record `client.chat.completions.create` on `recorder`.

    When `tools` is omitted, one completion is recorded and returned.
    When `tools` is provided, tool calls are executed, recorded, and fed back
    to the model until it stops or the turn limit is hit.
    """

    completions = client.chat.completions
    original = completions.create

    def create(*args: Any, **kwargs: Any) -> Any:
        if args:
            raise TypeError("wrap_openai records keyword calls to chat.completions.create")
        if tools is None:
            response = original(**kwargs)
            _record(recorder, kwargs, response)
            return response
        return _tool_loop(original, recorder, tools, kwargs)

    completions.create = create
    return client


def _record(recorder: RunRecorder, kwargs: dict[str, Any], response: Any) -> None:
    parsed = parse_completion(response)
    recorder.record_model(
        model=str(kwargs.get("model") or ""),
        messages=list(kwargs.get("messages") or []),
        response_text=parsed.text,
        tool_calls=parsed.tool_calls,
        params=safe_params(kwargs),
        usage=usage_dict(response),
    )


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
        parsed = parse_completion(response)
        _record(recorder, pending, response)
        if not parsed.tool_calls:
            return response
        messages.append(assistant_message(parsed.text, parsed.tool_calls))
        for call in parsed.tool_calls:
            function = tools.get(call.name)
            if function is None:
                with recorder.tool(call.name, call.arguments, call_id=call.id) as handle:
                    handle.record({"error": f"unknown tool {call.name}"})
                recorder.fail(f"unknown tool {call.name}", unexpected_tools=[call.name])
                messages.append(
                    tool_message(call.id, {"error": f"unknown tool {call.name}"}, "unknown tool")
                )
                return response
            with recorder.tool(call.name, call.arguments, call_id=call.id) as handle:
                result = function(**call.arguments)
                handle.record(result)
            messages.append(tool_message(call.id, result, None))
    return last
