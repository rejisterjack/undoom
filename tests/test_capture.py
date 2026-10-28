import json
from types import SimpleNamespace

from undoom import configure, run, wrap_openai
from undoom.models import RunStatus, ToolStep


class _Function:
    def __init__(self, name: str, arguments: dict[str, object]) -> None:
        self.name = name
        self.arguments = json.dumps(arguments)


class _ToolCall:
    def __init__(self, name: str, arguments: dict[str, object]) -> None:
        self.id = f"call_{name}"
        self.function = _Function(name, arguments)


class _Message:
    def __init__(self, content: str | None, tool_calls: list[_ToolCall] | None) -> None:
        self.content = content
        self.tool_calls = tool_calls


class _Response:
    def __init__(self, content: str | None, tool_calls: list[_ToolCall] | None) -> None:
        self.choices = [SimpleNamespace(message=_Message(content, tool_calls))]
        self.usage = None


class _Completions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs: object) -> _Response:
        self.calls += 1
        if self.calls == 1:
            return _Response(None, [_ToolCall("lookup_order", {"order_id": "1042"})])
        return _Response("Order 1042 has shipped.", None)


def _client() -> SimpleNamespace:
    completions = _Completions()
    return SimpleNamespace(chat=SimpleNamespace(completions=completions), completions=completions)


def test_manual_run_records_failure_and_redacts(tmp_path) -> None:
    configure(store=tmp_path / "traces.sqlite", agent="support")
    with run(name="ticket") as recorder:
        recorder.record_model(
            model="fake",
            messages=[{"role": "user", "content": "sk-abcdefghijklmnopqrstuvwxyz"}],
            response_text=None,
            tool_calls=[],
        )
        with recorder.tool("lookup_order", {"order_id": "1042"}) as handle:
            handle.record({"status": "shipped"})
        recorder.fail("wrong order", unexpected_tools=["lookup_order"])
    assert recorder.run.status == RunStatus.failure
    assert recorder.run.unexpected_tools == ["lookup_order"]
    assert "sk-" not in recorder.run.model_dump_json()


def test_tool_exception_is_a_failure(tmp_path) -> None:
    configure(store=tmp_path / "traces.sqlite")

    def boom() -> None:
        raise RuntimeError("down")

    with pytest_raises_runtime():
        with run(name="broken") as recorder:
            with recorder.tool("lookup_order", {}) as handle:
                boom()
                handle.record(None)
    assert recorder.run.status == RunStatus.failure
    tool_steps = [step for step in recorder.run.steps if isinstance(step, ToolStep)]
    assert tool_steps[0].error is not None
    assert "down" in tool_steps[0].error


def pytest_raises_runtime():
    import pytest

    return pytest.raises(RuntimeError)


def test_openai_wrapper_records_the_tool_round_trip(tmp_path) -> None:
    configure(store=tmp_path / "traces.sqlite", agent="support")
    seen: list[str] = []

    def lookup_order(order_id: str) -> dict[str, str]:
        seen.append(order_id)
        return {"status": "shipped"}

    client = _client()
    with run(name="wrapped") as recorder:
        wrap_openai(client, recorder, tools={"lookup_order": lookup_order})
        client.chat.completions.create(
            model="fake",
            messages=[{"role": "user", "content": "Where is order 1042?"}],
        )
    assert seen == ["1042"]
    assert client.completions.calls == 2
    kinds = [step.kind for step in recorder.run.steps]
    assert kinds == ["model", "tool", "model"]
    assert recorder.run.status == RunStatus.success
