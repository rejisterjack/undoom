"""Run committed cases against a model provider."""

from __future__ import annotations

import copy
from pathlib import Path

from undoom.models import Case, CaseResult, SuiteReport, ToolStep
from undoom.replay.cassette import Cassette
from undoom.replay.changeset import apply_prompt, ensure_changeset, read_prompt
from undoom.replay.diff import tool_names
from undoom.replay.engine import Execution, execute_case
from undoom.replay.providers import ModelProvider
from undoom.suite.files import load_cases


def run_suite(
    directory: Path,
    *,
    provider: ModelProvider,
    case_name: str | None = None,
) -> SuiteReport:
    cases = load_cases(directory)
    if case_name is not None:
        cases = [case for case in cases if case.name == case_name]
        if not cases:
            return SuiteReport(
                cases=[CaseResult(name=case_name, status="error", message="case not found")]
            )
    return SuiteReport(cases=[_run_case(case, provider) for case in cases])


def _run_case(case: Case, provider: ModelProvider) -> CaseResult:
    try:
        ensure_changeset(case.changeset)
        messages = copy.deepcopy(case.messages)
        model = case.model
        if case.changeset.kind == "prompt":
            messages = apply_prompt(messages, read_prompt(case.changeset))
        elif case.changeset.kind == "model" and case.changeset.model:
            model = case.changeset.model
        execution = execute_case(
            messages=messages,
            model=model,
            tools_schema=case.tools_schema,
            cassette=Cassette(list(case.cassette)),
            changeset=case.changeset,
            provider=provider,
            agent="suite",
            name=case.name,
        )
    except Exception as exc:
        return CaseResult(name=case.name, status="error", message=str(exc))
    return evaluate(case, execution)


def evaluate(case: Case, execution: Execution) -> CaseResult:
    if execution.diverged:
        message = execution.notes[0] if execution.notes else "diverged from the recording"
        return CaseResult(name=case.name, status="failed", message=message)
    names = tool_names(execution.run)
    for forbidden in case.expectation.absent_tools:
        if forbidden in names:
            return CaseResult(
                name=case.name,
                status="failed",
                message=f"failure recurred: unexpected tool {forbidden}",
            )
    errors = {
        step.name for step in execution.run.steps if isinstance(step, ToolStep) and step.error
    }
    for name in case.expectation.absent_tool_errors:
        if name in errors:
            return CaseResult(
                name=case.name,
                status="failed",
                message=f"failure recurred: tool error in {name}",
            )
    required = case.expectation.required_tool_sequence
    if required is not None and names != required:
        return CaseResult(
            name=case.name,
            status="failed",
            message=f"tool sequence {names} != {required}",
        )
    return CaseResult(name=case.name, status="passed")
