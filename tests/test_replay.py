from tests.support import Scripted, failed_order_run, lost_calls

from examples.order_lookup.fake import provider
from examples.order_lookup.prompts import FIXED
from examples.order_lookup.tools import calls, reset
from undoom.errors import ReplayError
from undoom.models import ModelResponse, ToolCall, Verdict
from undoom.replay.changeset import build_changeset
from undoom.replay.engine import replay_run


def test_prompt_replay_mocks_tools_and_does_not_call_them() -> None:
    reset()
    source = failed_order_run()
    replay = replay_run(
        source,
        build_changeset(prompt_text=FIXED),
        provider=provider(),
    )
    assert replay.verdict == Verdict.fixed
    assert calls["lookup_order"] == 0
    assert calls["refund_order"] == 0
    assert replay.diff.replay_tools == ["lookup_order"]
    assert any(
        item.op == "removed" and item.source_tool == "refund_order"
        for item in replay.diff.tool_diffs
    )
    assert replay.run.steps[0].params["temperature"] == 0


def test_same_prompt_is_still_failing() -> None:
    source = failed_order_run()
    replay = replay_run(
        source,
        build_changeset(prompt_text=source.steps[0].messages[0]["content"]),
        provider=provider(),
    )
    assert replay.verdict == Verdict.still_failing


def test_argument_mismatch_stops_without_calling_tools() -> None:
    reset()
    source = failed_order_run()
    scripted = Scripted(
        [
            ModelResponse(
                text=None,
                tool_calls=[ToolCall(id="x", name="lookup_order", arguments={"order_id": "9999"})],
            )
        ]
    )
    replay = replay_run(source, build_changeset(model="gpt-next"), provider=scripted)
    assert replay.verdict == Verdict.diverged
    assert calls["lookup_order"] == 0
    assert scripted.calls[0]["model"] == "gpt-next"
    assert scripted.calls[0]["temperature"] == 0


def test_tool_override_is_executed() -> None:
    lost_calls.clear()
    source = failed_order_run()
    scripted = Scripted(
        [
            ModelResponse(
                text=None,
                tool_calls=[ToolCall(id="1", name="lookup_order", arguments={"order_id": "1042"})],
            ),
            ModelResponse(text="It is lost.", tool_calls=[]),
        ]
    )
    replay = replay_run(
        source,
        build_changeset(tool_name="lookup_order", tool_entrypoint="tests.support:lookup_lost"),
        provider=scripted,
    )
    assert lost_calls == ["1042"]
    assert replay.verdict == Verdict.fixed
    assert any(item.op == "changed" for item in replay.diff.tool_diffs)


def test_two_changes_are_rejected() -> None:
    source = failed_order_run()
    try:
        build_changeset(prompt_text="new", model="other")
    except ReplayError as exc:
        assert "exactly one" in str(exc)
    else:
        raise AssertionError("expected ReplayError")
    replay = replay_run(source, build_changeset(prompt_text=""), provider=provider())
    assert replay is not None


def test_prompt_file_is_what_the_model_sees(tmp_path) -> None:
    prompt = tmp_path / "fixed.txt"
    prompt.write_text(FIXED, encoding="utf-8")
    scripted = Scripted([ModelResponse(text="ok", tool_calls=[])])
    replay_run(
        failed_order_run(),
        build_changeset(prompt_file=str(prompt)),
        provider=scripted,
    )
    assert FIXED in scripted.calls[0]["messages"][0]["content"]
