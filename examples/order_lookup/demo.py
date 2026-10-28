"""Offline story: a refund bug, a one-line prompt fix, and a regression case.

Run from a scratch directory so traces stay out of this repository:

    UNDOOM_DEMO_ROOT=/tmp/undoom-demo python examples/order_lookup/demo.py
    cd /tmp/undoom-demo
    UNDOOM_MODEL_PROVIDER=examples.order_lookup.fake:provider undoom test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.order_lookup.fake import provider
from examples.order_lookup.prompts import BUGGY, FIXED, TOOLS_SCHEMA, USER_MESSAGE
from examples.order_lookup.tools import lookup_order, refund_order
from undoom import configure, run
from undoom.config import get_config
from undoom.models import ToolCall, Verdict
from undoom.replay.changeset import build_changeset
from undoom.replay.engine import replay_run
from undoom.store.sqlite import SqliteStore
from undoom.suite.files import write_case
from undoom.suite.promote import promote_replay
from undoom.suite.report import render_text
from undoom.suite.runner import run_suite

CASE_NAME = "no-unsolicited-refund"


def run_story(root: Path) -> str:
    """Capture the failure, replay the fix, and write `.undoom/cases`."""

    root = root.resolve()
    previous = Path.cwd()
    os.chdir(root)
    try:
        return _run(root)
    finally:
        os.chdir(previous)


def export_fixtures(destination: Path) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        story_root = Path(tmp)
        run_story(story_root)
        store = SqliteStore(story_root / ".undoom" / "traces.sqlite")
        bundle = {
            "runs": [item.model_dump(mode="json") for item in store.list_runs(limit=100)],
            "replays": [item.model_dump(mode="json") for item in store.list_replays(limit=100)],
            "cases": [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((story_root / ".undoom" / "cases").glob("*.json"))
            ],
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(bundle, indent=2) + "\n"
    destination.write_text(text, encoding="utf-8")
    mirror = ROOT / "apps" / "ui" / "fixtures" / "demo.json"
    if destination.resolve() != mirror.resolve():
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(text, encoding="utf-8")


def _run(root: Path) -> str:
    prompts = root / "prompts"
    prompts.mkdir(parents=True, exist_ok=True)
    (prompts / "buggy.txt").write_text(BUGGY.strip() + "\n", encoding="utf-8")
    (prompts / "fixed.txt").write_text(FIXED.strip() + "\n", encoding="utf-8")
    configure(store=root / ".undoom" / "traces.sqlite", agent="support")
    run_id = _capture()
    source = get_config().store().get_run(run_id)
    if source is None:
        raise SystemExit(f"captured run {run_id} was not stored")
    replay = replay_run(
        source,
        build_changeset(prompt_file="prompts/fixed.txt"),
        provider=provider(),
    )
    if replay.verdict != Verdict.fixed:
        raise SystemExit(f"expected a fixed replay, got {replay.verdict.value}")
    get_config().store().save_replay(replay)
    case = promote_replay(replay, source, name=CASE_NAME)
    path = write_case(case, root / ".undoom" / "cases")
    report = run_suite(root / ".undoom" / "cases", provider=provider())
    if report.failed:
        raise SystemExit(render_text(report))
    print(f"promoted {path}")
    return case.name


def _capture() -> str:
    messages = [
        {"role": "system", "content": BUGGY.strip()},
        {"role": "user", "content": USER_MESSAGE},
    ]
    with run(agent="support", name="ticket-1042") as recorder:
        recorder.record_model(
            model="fake-order",
            messages=messages,
            response_text=None,
            tool_calls=[
                ToolCall(id="lookup_1", name="lookup_order", arguments={"order_id": "1042"}),
                ToolCall(id="refund_1", name="refund_order", arguments={"order_id": "1042"}),
            ],
            params={"tools": TOOLS_SCHEMA, "temperature": 0},
        )
        with recorder.tool("lookup_order", {"order_id": "1042"}, call_id="lookup_1") as handle:
            handle.record(lookup_order("1042"))
        with recorder.tool("refund_order", {"order_id": "1042"}, call_id="refund_1") as handle:
            handle.record(refund_order("1042"))
        recorder.record_model(
            model="fake-order",
            messages=messages,
            response_text="I refunded order 1042.",
            tool_calls=[],
            params={"temperature": 0},
        )
        recorder.fail(
            "refunded without an explicit request",
            unexpected_tools=["refund_order"],
        )
    return recorder.run.id


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the offline Undoom order-lookup story.")
    parser.add_argument(
        "--fixtures", type=Path, default=None, help="Also write a synthetic UI bundle."
    )
    args = parser.parse_args()
    if args.fixtures is not None:
        export_fixtures(args.fixtures)
        print(f"wrote {args.fixtures}")
        return
    root = Path(os.environ.get("UNDOOM_DEMO_ROOT", Path.cwd()))
    run_story(root)


if __name__ == "__main__":
    main()
