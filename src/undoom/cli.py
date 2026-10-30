"""Command line for capture inspection, replay, and the regression suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from undoom.config import configure, get_config
from undoom.errors import PromoteError, ReplayError, TraceImportError, UndoomError
from undoom.models import RunStatus
from undoom.otel.import_trace import import_trace
from undoom.present import format_replay, format_run, format_run_line
from undoom.replay.changeset import build_changeset
from undoom.replay.engine import replay_run
from undoom.replay.providers import resolve_provider
from undoom.suite.files import write_case
from undoom.suite.promote import promote_replay
from undoom.suite.report import render_report
from undoom.suite.runner import run_suite

app = typer.Typer(
    no_args_is_help=True, help="Replay agent failures and lock the fix into a regression test."
)
runs_app = typer.Typer(no_args_is_help=True, help="Inspect captured runs.")
app.add_typer(runs_app, name="runs")


@app.callback()
def _root(
    store: Annotated[
        str | None,
        typer.Option(
            "--store", envvar="UNDOOM_STORE", help="sqlite path, sqlite URL, or postgres URL"
        ),
    ] = None,
) -> None:
    configure(store=store)


@runs_app.command("list")
def runs_list(
    limit: Annotated[int, typer.Option("--limit")] = 50,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """List captured runs, newest first."""

    found = get_config().store().list_runs(limit=limit)
    if as_json:
        typer.echo(json.dumps([run.model_dump(mode="json") for run in found], indent=2))
        return
    if not found:
        typer.echo("no runs")
        return
    for run in found:
        typer.echo(format_run_line(run))


@runs_app.command("show")
def runs_show(
    run_id: str,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show one captured run."""

    run = get_config().store().get_run(run_id)
    if run is None:
        typer.echo(f"run not found: {run_id}", err=True)
        raise typer.Exit(1)
    if as_json:
        typer.echo(json.dumps(run.model_dump(mode="json"), indent=2))
        return
    typer.echo(format_run(run))


@runs_app.command("fail")
def runs_fail(
    run_id: str,
    reason: Annotated[str, typer.Option("--reason")],
    unexpected_tool: Annotated[list[str] | None, typer.Option("--unexpected-tool")] = None,
) -> None:
    """Mark a run as a failure and name the tools that must not return."""

    store = get_config().store()
    run = store.get_run(run_id)
    if run is None:
        typer.echo(f"run not found: {run_id}", err=True)
        raise typer.Exit(1)
    run.status = RunStatus.failure
    run.failure_reason = reason
    for name in unexpected_tool or []:
        if name not in run.unexpected_tools:
            run.unexpected_tools.append(name)
    store.save_run(run)
    stored = store.get_run(run_id)
    typer.echo(format_run(stored if stored is not None else run))


@app.command("import")
def import_cmd(
    trace_file: Annotated[Path, typer.Argument(help="OTLP/JSON export with resourceSpans")],
    trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
    agent: Annotated[str, typer.Option("--agent")] = "default",
    name: Annotated[str, typer.Option("--name")] = "imported",
) -> None:
    """Import a GenAI OTLP/JSON trace that includes tool arguments and results."""

    try:
        document = json.loads(trace_file.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise TraceImportError("trace file must contain a JSON object")
        run = import_trace(document, trace_id=trace_id, agent=agent, name=name)
        store = get_config().store()
        store.save_run(run)
    except (OSError, json.JSONDecodeError, TraceImportError, UndoomError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(run.id)


@app.command("replay")
def replay_cmd(
    run_id: str,
    prompt_file: Annotated[Path | None, typer.Option("--prompt-file")] = None,
    prompt: Annotated[str | None, typer.Option("--prompt")] = None,
    model: Annotated[str | None, typer.Option("--model")] = None,
    tool: Annotated[str | None, typer.Option("--tool", help="name=module:function")] = None,
    provider: Annotated[str | None, typer.Option("--provider")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Replay a run with exactly one change. Other tools stay on the recording."""

    try:
        tool_name, tool_entrypoint = _split_tool(tool)
        changeset = build_changeset(
            prompt_text=prompt,
            prompt_file=str(prompt_file) if prompt_file is not None else None,
            model=model,
            tool_name=tool_name,
            tool_entrypoint=tool_entrypoint,
        )
        store = get_config().store()
        source = store.get_run(run_id)
        if source is None:
            typer.echo(f"run not found: {run_id}", err=True)
            raise typer.Exit(1)
        result = replay_run(source, changeset, provider=resolve_provider(provider))
        store.save_replay(result)
    except (ReplayError, UndoomError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json.dumps(result.model_dump(mode="json"), indent=2))
        return
    typer.echo(format_replay(result))


@app.command("promote")
def promote_cmd(
    replay_id: str,
    name: Annotated[str, typer.Option("--name")],
    expect_tools: Annotated[bool, typer.Option("--expect-tools")] = False,
    cases_dir: Annotated[Path, typer.Option("--cases-dir")] = Path(".undoom/cases"),
) -> None:
    """Write a fixed replay to a regression case file."""

    try:
        store = get_config().store()
        replay = store.get_replay(replay_id)
        if replay is None:
            typer.echo(f"replay not found: {replay_id}", err=True)
            raise typer.Exit(1)
        source = store.get_run(replay.source_run_id)
        if source is None:
            typer.echo(f"source run not found: {replay.source_run_id}", err=True)
            raise typer.Exit(1)
        case = promote_replay(replay, source, name=name, expect_tools=expect_tools)
        path = write_case(case, cases_dir)
    except (PromoteError, ReplayError, UndoomError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(str(path))


@app.command("test")
def test_cmd(
    case: Annotated[str | None, typer.Option("--case")] = None,
    report_format: Annotated[str, typer.Option("--format")] = "text",
    cases_dir: Annotated[Path, typer.Option("--cases-dir")] = Path(".undoom/cases"),
    provider: Annotated[str | None, typer.Option("--provider")] = None,
) -> None:
    """Run regression cases. Exits non-zero when a known failure returns."""

    try:
        if report_format not in {"text", "json", "junit"}:
            raise ReplayError("format must be text, json, or junit")
        report = run_suite(cases_dir, provider=resolve_provider(provider), case_name=case)
    except (ReplayError, UndoomError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(render_report(report, report_format))
    if report.failed:
        raise typer.Exit(1)


@app.command("serve")
def serve_cmd(
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port")] = 8787,
    demo: Annotated[
        bool, typer.Option("--demo", help="Disable writes. For a synthetic demo only.")
    ] = False,
    cases_dir: Annotated[Path, typer.Option("--cases-dir")] = Path(".undoom/cases"),
) -> None:
    """Serve the local read API used by the diff UI."""

    try:
        import uvicorn

        from undoom.api import create_app
    except ImportError as exc:
        typer.echo("Install the ui extra: pip install 'undoom[ui]'", err=True)
        raise typer.Exit(1) from exc
    application = create_app(get_config().store(), cases_dir, demo=demo)
    uvicorn.run(application, host=host, port=port)


def _split_tool(tool: str | None) -> tuple[str | None, str | None]:
    if tool is None:
        return None, None
    if "=" not in tool:
        raise ReplayError("--tool must look like name=module:function")
    name, entrypoint = tool.split("=", 1)
    if not name or ":" not in entrypoint:
        raise ReplayError("--tool must look like name=module:function")
    return name, entrypoint


def main() -> None:
    app()
