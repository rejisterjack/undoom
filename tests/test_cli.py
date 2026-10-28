import json

from tests.support import failed_order_run
from typer.testing import CliRunner

from examples.order_lookup.prompts import FIXED
from undoom import configure, run
from undoom.cli import app
from undoom.store.sqlite import SqliteStore

runner = CliRunner()


def test_runs_list_show_and_fail(tmp_path) -> None:
    db = tmp_path / "traces.sqlite"
    configure(store=db, agent="support")
    with run(name="ticket") as recorder:
        recorder.record_model(
            model="fake",
            messages=[{"role": "user", "content": "hi"}],
            response_text="ok",
            tool_calls=[],
        )
    run_id = recorder.run.id
    listed = runner.invoke(app, ["--store", str(db), "runs", "list"])
    assert listed.exit_code == 0
    assert run_id in listed.stdout
    shown = runner.invoke(app, ["--store", str(db), "runs", "show", run_id])
    assert "status: success" in shown.stdout
    failed = runner.invoke(
        app,
        [
            "--store",
            str(db),
            "runs",
            "fail",
            run_id,
            "--reason",
            "refunded without an explicit request",
            "--unexpected-tool",
            "refund_order",
        ],
    )
    assert failed.exit_code == 0
    stored = SqliteStore(db).get_run(run_id)
    assert stored is not None
    assert stored.failure_reason == "refunded without an explicit request"
    assert stored.unexpected_tools == ["refund_order"]


def test_replay_refuses_two_changes(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            "--store",
            str(tmp_path / "t.sqlite"),
            "replay",
            "missing",
            "--prompt",
            "a",
            "--model",
            "b",
        ],
    )
    assert result.exit_code != 0
    assert "exactly one" in result.stderr + result.stdout


def test_replay_promote_and_test(tmp_path, monkeypatch) -> None:
    db = tmp_path / "traces.sqlite"
    store = SqliteStore(db)
    source = failed_order_run()
    store.save_run(source)
    monkeypatch.chdir(tmp_path)
    replayed = runner.invoke(
        app,
        [
            "--store",
            str(db),
            "replay",
            source.id,
            "--prompt",
            FIXED,
            "--provider",
            "examples.order_lookup.fake:provider",
        ],
    )
    assert replayed.exit_code == 0, replayed.stdout + replayed.stderr
    assert "verdict: fixed" in replayed.stdout
    replay_id = SqliteStore(db).list_replays()[0].id
    promoted = runner.invoke(
        app,
        ["--store", str(db), "promote", replay_id, "--name", "no-unsolicited-refund"],
    )
    assert promoted.exit_code == 0, promoted.stdout + promoted.stderr
    case_path = tmp_path / ".undoom" / "cases" / "no-unsolicited-refund.json"
    assert case_path.is_file()
    tested = runner.invoke(
        app,
        ["test", "--provider", "examples.order_lookup.fake:provider", "--format", "junit"],
    )
    assert tested.exit_code == 0, tested.stdout + tested.stderr
    assert "no-unsolicited-refund" in tested.stdout
    payload = json.loads(case_path.read_text(encoding="utf-8"))
    assert "refund_order" in payload["expectation"]["absent_tools"]


def test_show_missing_run(tmp_path) -> None:
    result = runner.invoke(app, ["--store", str(tmp_path / "t.sqlite"), "runs", "show", "missing"])
    assert result.exit_code == 1
