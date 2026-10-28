"""Turn a fixed replay into a self-contained regression case."""

from __future__ import annotations

import copy

from undoom.errors import PromoteError
from undoom.models import Case, Expectation, Replay, Run, ToolStep, Verdict
from undoom.replay.cassette import entries_from_run
from undoom.replay.diff import tool_names
from undoom.replay.engine import first_model_step
from undoom.suite.files import validate_name


def promote_replay(
    replay: Replay,
    source: Run,
    *,
    name: str,
    expect_tools: bool = False,
) -> Case:
    validate_name(name)
    if replay.verdict != Verdict.fixed:
        verdict = replay.verdict.value if hasattr(replay.verdict, "value") else replay.verdict
        raise PromoteError(f"only a fixed replay can be promoted (verdict={verdict})")
    step = first_model_step(source)
    tools = step.params.get("tools") or []
    source_errors = [
        item.name for item in source.steps if isinstance(item, ToolStep) and item.error
    ]
    replay_errors = {
        item.name for item in replay.run.steps if isinstance(item, ToolStep) and item.error
    }
    absent_errors = [item for item in source_errors if item not in replay_errors]
    absent_tools = list(source.unexpected_tools)
    if not absent_tools and not absent_errors:
        kept = set(tool_names(replay.run))
        absent_tools = [item for item in tool_names(source) if item not in kept]
    sequence = tool_names(replay.run) if expect_tools else None
    return Case(
        name=name,
        source_failure_id=source.id,
        replay_id=replay.id,
        messages=copy.deepcopy(step.messages),
        model=step.model,
        tools_schema=list(tools) if isinstance(tools, list) else [],
        cassette=entries_from_run(source),
        changeset=replay.changeset,
        expectation=Expectation(
            failure_reason=source.failure_reason,
            absent_tools=absent_tools,
            absent_tool_errors=absent_errors,
            required_tool_sequence=sequence,
        ),
    )
