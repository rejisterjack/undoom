"""OpenTelemetry import: cassette-ready traces only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from undoom import configure
from undoom.cli import app
from undoom.errors import TraceImportError
from undoom.models import ModelStep, ToolStep
from undoom.otel.import_trace import import_trace
from undoom.replay.cassette import Cassette, entries_from_run
from undoom.store.sqlite import SqliteStore

FIXTURES = Path(__file__).parent / "fixtures" / "otel"
runner = CliRunner()


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_import_complete_trace_builds_cassette() -> None:
    run = import_trace(_load("complete_trace.json"), agent="support", name="ticket")
    assert run.agent == "support"
    assert any(isinstance(step, ModelStep) for step in run.steps)
    tools = [step for step in run.steps if isinstance(step, ToolStep)]
    assert len(tools) == 1
    assert tools[0].name == "lookup_order"
    assert tools[0].arguments == {"order_id": "1042"}
    assert tools[0].result == {
        "order_id": "1042",
        "status": "shipped",
        "authorization": "Bearer sk-secretTOKEN123456",
    }
    cassette = Cassette(entries_from_run(run))
    hit = cassette.lookup("lookup_order", {"order_id": "1042"})
    assert hit is not None
    assert hit.result["status"] == "shipped"


def test_missing_tool_arguments_and_result_are_rejected() -> None:
    with pytest.raises(TraceImportError, match="gen_ai.tool.call.arguments"):
        import_trace(_load("missing_tool_result.json"))


def test_multiple_traces_require_trace_id() -> None:
    document = _load("two_traces.json")
    with pytest.raises(TraceImportError, match="multiple traces"):
        import_trace(document)
    chosen = import_trace(document, trace_id="dddddddddddddddddddddddddddddddd")
    models = [step for step in chosen.steps if isinstance(step, ModelStep)]
    assert models[0].model == "fake-two"


def test_cli_import_redacts_and_persists(tmp_path: Path) -> None:
    db = tmp_path / "traces.sqlite"
    configure(store=db)
    result = runner.invoke(
        app,
        [
            "--store",
            str(db),
            "import",
            str(FIXTURES / "complete_trace.json"),
            "--agent",
            "support",
            "--name",
            "from-otel",
        ],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    run_id = result.stdout.strip()
    stored = SqliteStore(db).get_run(run_id)
    assert stored is not None
    tools = [step for step in stored.steps if isinstance(step, ToolStep)]
    assert tools[0].result["authorization"] == "[REDACTED]"
    assert "sk-secretTOKEN123456" not in json.dumps(tools[0].result)


def test_cli_import_rejects_incomplete_tool_span(tmp_path: Path) -> None:
    db = tmp_path / "traces.sqlite"
    before = list(SqliteStore(db).list_runs())
    result = runner.invoke(
        app,
        ["--store", str(db), "import", str(FIXTURES / "missing_tool_result.json")],
    )
    assert result.exit_code == 1
    assert "gen_ai.tool.call.arguments" in result.stderr
    assert SqliteStore(db).list_runs() == before


def test_cli_import_selects_one_of_two_traces(tmp_path: Path) -> None:
    db = tmp_path / "traces.sqlite"
    refused = runner.invoke(
        app,
        ["--store", str(db), "import", str(FIXTURES / "two_traces.json")],
    )
    assert refused.exit_code == 1
    assert "multiple traces" in refused.stderr
    accepted = runner.invoke(
        app,
        [
            "--store",
            str(db),
            "import",
            str(FIXTURES / "two_traces.json"),
            "--trace-id",
            "cccccccccccccccccccccccccccccccc",
        ],
    )
    assert accepted.exit_code == 0, accepted.stdout + accepted.stderr
    stored = SqliteStore(db).get_run(accepted.stdout.strip())
    assert stored is not None
    models = [step for step in stored.steps if isinstance(step, ModelStep)]
    assert models[0].model == "fake-one"
