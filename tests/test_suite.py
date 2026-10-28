import pytest
from tests.support import failed_order_run

from examples.order_lookup.fake import provider
from examples.order_lookup.prompts import BUGGY, FIXED
from undoom.errors import PromoteError
from undoom.models import Verdict
from undoom.replay.changeset import build_changeset
from undoom.replay.engine import replay_run
from undoom.suite.files import load_cases, write_case
from undoom.suite.promote import promote_replay
from undoom.suite.report import render_json, render_junit, render_text
from undoom.suite.runner import run_suite


def test_promote_and_suite(tmp_path) -> None:
    source = failed_order_run()
    replay = replay_run(source, build_changeset(prompt_text=FIXED), provider=provider())
    assert replay.verdict == Verdict.fixed
    case = promote_replay(replay, source, name="no-unsolicited-refund", expect_tools=True)
    path = write_case(case, tmp_path)
    assert path.name == "no-unsolicited-refund.json"
    loaded = load_cases(tmp_path)
    assert loaded[0].expectation.absent_tools == ["refund_order"]
    assert loaded[0].expectation.required_tool_sequence == ["lookup_order"]
    report = run_suite(tmp_path, provider=provider())
    assert report.failed == 0
    assert "PASS no-unsolicited-refund" in render_text(report)
    assert '"passed": 1' in render_json(report)
    junit = render_junit(report)
    assert "<testcase" in junit
    assert "no-unsolicited-refund" in junit

    loaded[0].changeset.prompt_text = BUGGY
    write_case(loaded[0], tmp_path)
    failed = run_suite(tmp_path, provider=provider())
    assert failed.failed == 1
    assert "refund_order" in failed.cases[0].message
    assert "<failure" in render_junit(failed)


def test_promote_refuses_a_failure() -> None:
    source = failed_order_run()
    replay = replay_run(source, build_changeset(prompt_text=BUGGY), provider=provider())
    assert replay.verdict == Verdict.still_failing
    with pytest.raises(PromoteError):
        promote_replay(replay, source, name="still-bad")
