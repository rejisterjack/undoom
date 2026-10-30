"""Build a cassette-ready Run from an OTLP/JSON GenAI export.

GenAI conventions mark tool arguments and results as opt-in. Spans that omit
them cannot fill a cassette, so this importer refuses them instead of inventing
values. It does not call tools and does not attach to a tracing backend.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from undoom.errors import TraceImportError
from undoom.models import ModelStep, Run, RunStatus, ToolCall, ToolStep

_CHAT_OPS = frozenset({"chat", "generate_content"})
_TOOL_OP = "execute_tool"


def import_trace(
    document: dict[str, Any],
    *,
    trace_id: str | None = None,
    agent: str = "default",
    name: str = "imported",
    status: RunStatus = RunStatus.success,
) -> Run:
    """Convert one OTLP/JSON trace into a `Run`.

    The caller saves the result. Failure signatures stay on `undoom runs fail`.
    """

    spans = _collect_spans(document)
    if not spans:
        raise TraceImportError("document has no spans under resourceSpans")
    selected = _select_trace(spans, trace_id)
    selected.sort(key=lambda span: _start_time(span))
    steps: list[ModelStep | ToolStep] = []
    for span in selected:
        attrs = _attributes(span)
        operation = _as_str(attrs.get("gen_ai.operation.name"))
        if operation in _CHAT_OPS:
            steps.append(_model_step(span, attrs))
        elif operation == _TOOL_OP:
            steps.append(_tool_step(span, attrs))
    if not any(isinstance(step, ModelStep) for step in steps):
        raise TraceImportError("trace has no chat or generate_content model span")
    return Run(agent=agent, name=name, status=status, steps=steps)


def _collect_spans(document: dict[str, Any]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for resource in document.get("resourceSpans") or []:
        if not isinstance(resource, dict):
            continue
        for scope in resource.get("scopeSpans") or []:
            if not isinstance(scope, dict):
                continue
            for span in scope.get("spans") or []:
                if isinstance(span, dict):
                    spans.append(span)
    return spans


def _select_trace(spans: list[dict[str, Any]], trace_id: str | None) -> list[dict[str, Any]]:
    ids = sorted({_as_str(span.get("traceId")) or "" for span in spans} - {""})
    if not ids:
        raise TraceImportError("spans are missing traceId")
    if trace_id is None:
        if len(ids) > 1:
            raise TraceImportError(
                "document contains multiple traces; pass --trace-id with one of: " + ", ".join(ids)
            )
        chosen = ids[0]
    else:
        chosen = trace_id
        if chosen not in ids:
            raise TraceImportError(f"trace id not found: {chosen}")
    return [span for span in spans if _as_str(span.get("traceId")) == chosen]


def _model_step(span: dict[str, Any], attrs: dict[str, Any]) -> ModelStep:
    model = (
        _as_str(attrs.get("gen_ai.request.model"))
        or _as_str(attrs.get("gen_ai.response.model"))
        or ""
    )
    messages = _messages(span, attrs)
    tools = _json_value(attrs.get("gen_ai.tool.definitions"))
    params: dict[str, Any] = {}
    if isinstance(tools, list):
        params["tools"] = tools
    response_text = _as_str(attrs.get("gen_ai.output.messages"))
    if response_text is None:
        response_text = _as_str(attrs.get("gen_ai.response.text"))
    tool_calls = _tool_calls_from_attrs(attrs)
    return ModelStep(
        model=model,
        messages=messages,
        params=params,
        response_text=response_text if isinstance(response_text, str) else None,
        tool_calls=tool_calls,
    )


def _tool_step(span: dict[str, Any], attrs: dict[str, Any]) -> ToolStep:
    label = _as_str(span.get("name")) or "execute_tool"
    name = _as_str(attrs.get("gen_ai.tool.name"))
    if not name:
        raise TraceImportError(f"tool span {label!r} is missing gen_ai.tool.name")
    if "gen_ai.tool.call.arguments" not in attrs:
        raise TraceImportError(
            f"tool span {label!r} is missing gen_ai.tool.call.arguments; "
            "a cassette needs the recorded arguments"
        )
    arguments = _json_value(attrs["gen_ai.tool.call.arguments"])
    if not isinstance(arguments, dict):
        raise TraceImportError(
            f"tool span {label!r} gen_ai.tool.call.arguments must be a JSON object"
        )
    has_result = "gen_ai.tool.call.result" in attrs
    error = _as_str(attrs.get("gen_ai.tool.call.error")) or _as_str(attrs.get("error.message"))
    if not has_result and not error:
        raise TraceImportError(
            f"tool span {label!r} has neither gen_ai.tool.call.result nor a tool error; "
            "a cassette needs the recorded outcome"
        )
    result = _json_value(attrs["gen_ai.tool.call.result"]) if has_result else None
    call_id = _as_str(attrs.get("gen_ai.tool.call.id")) or uuid4().hex
    return ToolStep(
        call_id=call_id,
        name=name,
        arguments=arguments,
        result=result,
        error=error,
    )


def _messages(span: dict[str, Any], attrs: dict[str, Any]) -> list[dict[str, Any]]:
    raw = attrs.get("gen_ai.input.messages")
    if raw is not None:
        loaded = _json_value(raw)
        if isinstance(loaded, list):
            return [item for item in loaded if isinstance(item, dict)]
        raise TraceImportError("gen_ai.input.messages must be a JSON array of messages")
    from_events: list[dict[str, Any]] = []
    for event in span.get("events") or []:
        if not isinstance(event, dict):
            continue
        event_attrs = _attributes(event)
        if "gen_ai.input.messages" in event_attrs:
            loaded = _json_value(event_attrs["gen_ai.input.messages"])
            if isinstance(loaded, list):
                from_events.extend(item for item in loaded if isinstance(item, dict))
        role = _as_str(event_attrs.get("gen_ai.message.role")) or _as_str(event.get("name"))
        content = _as_str(event_attrs.get("gen_ai.message.content"))
        if role and content is not None:
            from_events.append({"role": role, "content": content})
    return from_events


def _tool_calls_from_attrs(attrs: dict[str, Any]) -> list[ToolCall]:
    raw = attrs.get("gen_ai.response.tool_calls")
    if raw is None:
        return []
    loaded = _json_value(raw)
    if not isinstance(loaded, list):
        return []
    calls: list[ToolCall] = []
    for item in loaded:
        if not isinstance(item, dict):
            continue
        name = _as_str(item.get("name")) or _as_str(item.get("function", {}).get("name"))
        if not name:
            continue
        arguments = item.get("arguments")
        if arguments is None and isinstance(item.get("function"), dict):
            arguments = item["function"].get("arguments")
        parsed = _json_value(arguments) if arguments is not None else {}
        if not isinstance(parsed, dict):
            parsed = {}
        calls.append(
            ToolCall(
                id=_as_str(item.get("id")) or uuid4().hex,
                name=name,
                arguments=parsed,
            )
        )
    return calls


def _attributes(node: dict[str, Any]) -> dict[str, Any]:
    raw = node.get("attributes")
    if isinstance(raw, dict):
        return dict(raw)
    out: dict[str, Any] = {}
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        if not isinstance(key, str):
            continue
        out[key] = _unwrap_value(item.get("value"))
    return out


def _unwrap_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    if "stringValue" in value:
        return value["stringValue"]
    if "intValue" in value:
        try:
            return int(value["intValue"])
        except (TypeError, ValueError):
            return value["intValue"]
    if "doubleValue" in value:
        return value["doubleValue"]
    if "boolValue" in value:
        return value["boolValue"]
    if "bytesValue" in value:
        return value["bytesValue"]
    array = value.get("arrayValue")
    if isinstance(array, dict) and isinstance(array.get("values"), list):
        return [_unwrap_value(item) for item in array["values"]]
    kvlist = value.get("kvlistValue")
    if isinstance(kvlist, dict) and isinstance(kvlist.get("values"), list):
        nested: dict[str, Any] = {}
        for item in kvlist["values"]:
            if isinstance(item, dict) and isinstance(item.get("key"), str):
                nested[item["key"]] = _unwrap_value(item.get("value"))
        return nested
    return value


def _json_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return value
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return value
    return value


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return None


def _start_time(span: dict[str, Any]) -> int:
    raw = span.get("startTimeUnixNano") or span.get("start_time_unix_nano") or 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0
