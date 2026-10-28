"""Replay a recorded failure with one change and a frozen tool cassette."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from undoom.errors import ReplayError
from undoom.models import (
    Changeset,
    ModelStep,
    Replay,
    Run,
    RunStatus,
    ToolCall,
    ToolStep,
    Verdict,
)
from undoom.openai_messages import assistant_message, tool_message
from undoom.replay.cassette import Cassette, entries_from_run
from undoom.replay.changeset import apply_prompt, ensure_changeset, read_prompt
from undoom.replay.diff import diff_trajectories, tool_names
from undoom.replay.loading import load_callable
from undoom.replay.providers import ModelProvider

MAX_TURNS = 8


@dataclass
class Execution:
    run: Run
    notes: list[str]
    diverged: bool


def replay_run(source: Run, changeset: Changeset, *, provider: ModelProvider) -> Replay:
    """Re-run `source` after applying `changeset`. Untouched tools are not executed."""

    ensure_changeset(changeset)
    try:
        execution = execute_case(
            messages=_initial_messages(source, changeset),
            model=_model_id(source, changeset),
            tools_schema=_tools_schema(source),
            cassette=Cassette(entries_from_run(source)),
            changeset=changeset,
            provider=provider,
            agent=source.agent,
            name=f"replay of {source.name}",
        )
    except ReplayError:
        raise
    except Exception as exc:
        failed = Run(
            agent=source.agent,
            name=f"replay of {source.name}",
            status=RunStatus.error,
            failure_reason=f"{type(exc).__name__}: {exc}",
            metadata={"source_run_id": source.id},
        )
        return Replay(
            source_run_id=source.id,
            changeset=changeset,
            run=failed,
            diff=diff_trajectories(source, failed),
            verdict=Verdict.error,
            notes=[str(exc)],
        )
    verdict = judge(source, execution)
    execution.run.metadata["source_run_id"] = source.id
    return Replay(
        source_run_id=source.id,
        changeset=changeset,
        run=execution.run,
        diff=diff_trajectories(source, execution.run),
        verdict=verdict,
        notes=execution.notes,
    )


def execute_case(
    *,
    messages: list[dict[str, Any]],
    model: str,
    tools_schema: list[dict[str, Any]],
    cassette: Cassette,
    changeset: Changeset,
    provider: ModelProvider,
    agent: str,
    name: str,
) -> Execution:
    transcript = copy.deepcopy(messages)
    new_run = Run(agent=agent, name=name, status=RunStatus.running)
    notes: list[str] = []
    diverged = False
    for _ in range(MAX_TURNS):
        response = provider.complete(
            model=model,
            messages=transcript,
            tools=tools_schema,
            temperature=0,
        )
        new_run.steps.append(
            ModelStep(
                model=model,
                messages=copy.deepcopy(transcript),
                params={"tools": tools_schema, "temperature": 0},
                response_text=response.text,
                tool_calls=response.tool_calls,
            )
        )
        if not response.tool_calls:
            break
        transcript.append(assistant_message(response.text, response.tool_calls))
        for call in response.tool_calls:
            result, error, missed = _resolve_tool(call, cassette, changeset)
            new_run.steps.append(
                ToolStep(
                    call_id=call.id,
                    name=call.name,
                    arguments=call.arguments,
                    result=result,
                    error=error,
                )
            )
            transcript.append(tool_message(call.id, result, error))
            if missed:
                diverged = True
                notes.append(f"cassette miss for {call.name}")
                break
        if diverged:
            break
    else:
        diverged = True
        notes.append(f"stopped after {MAX_TURNS} model turns")
    if diverged:
        new_run.status = RunStatus.failure
        new_run.failure_reason = notes[0] if notes else "diverged"
    elif new_run.status == RunStatus.running:
        new_run.status = RunStatus.success
    return Execution(new_run, notes, diverged)


def judge(source: Run, execution: Execution) -> Verdict:
    if execution.diverged:
        return Verdict.diverged
    if execution.run.status == RunStatus.error:
        return Verdict.error
    names = tool_names(execution.run)
    if any(name in names for name in source.unexpected_tools):
        execution.run.status = RunStatus.failure
        execution.run.failure_reason = source.failure_reason
        return Verdict.still_failing
    source_errors = [
        step.name for step in source.steps if isinstance(step, ToolStep) and step.error
    ]
    replay_errors = {
        step.name for step in execution.run.steps if isinstance(step, ToolStep) and step.error
    }
    if any(name in replay_errors for name in source_errors):
        execution.run.status = RunStatus.failure
        execution.run.failure_reason = source.failure_reason or "tool error recurred"
        return Verdict.still_failing
    if (
        not source.unexpected_tools
        and not source_errors
        and source.status == RunStatus.failure
        and tool_names(source) == names
    ):
        execution.run.status = RunStatus.failure
        execution.run.failure_reason = source.failure_reason
        return Verdict.still_failing
    execution.run.status = RunStatus.success
    execution.run.failure_reason = None
    return Verdict.fixed


def _initial_messages(source: Run, changeset: Changeset) -> list[dict[str, Any]]:
    messages = copy.deepcopy(first_model_step(source).messages)
    if changeset.kind == "prompt":
        return apply_prompt(messages, read_prompt(changeset))
    return messages


def _model_id(source: Run, changeset: Changeset) -> str:
    recorded = first_model_step(source).model
    if changeset.kind == "model" and changeset.model:
        return changeset.model
    return recorded


def _tools_schema(source: Run) -> list[dict[str, Any]]:
    params = first_model_step(source).params
    tools = params.get("tools") or []
    if not isinstance(tools, list):
        raise ReplayError("recorded tools schema is not a list")
    return tools


def first_model_step(run: Run) -> ModelStep:
    for step in run.steps:
        if isinstance(step, ModelStep):
            return step
    raise ReplayError("run has no model step to replay")


def _resolve_tool(
    call: ToolCall,
    cassette: Cassette,
    changeset: Changeset,
) -> tuple[Any, str | None, bool]:
    if changeset.kind == "tool" and call.name == changeset.tool_name:
        result, error = _invoke(changeset.tool_entrypoint or "", call.arguments)
        return result, error, False
    entry = cassette.lookup(call.name, call.arguments)
    if entry is None:
        return None, "cassette miss", True
    return entry.result, entry.error, False


def _invoke(entrypoint: str, arguments: dict[str, Any]) -> tuple[Any, str | None]:
    function = load_callable(entrypoint)
    try:
        return function(**arguments), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
