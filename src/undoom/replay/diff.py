"""Index-aligned comparison of tool trajectories."""

from __future__ import annotations

from undoom.canonical import canonical_json
from undoom.models import ModelStep, Run, StepDiff, ToolStep, TrajectoryDiff


def tool_steps(run: Run) -> list[ToolStep]:
    return [step for step in run.steps if isinstance(step, ToolStep)]


def tool_names(run: Run) -> list[str]:
    return [step.name for step in tool_steps(run)]


def final_text(run: Run) -> str | None:
    texts = [
        step.response_text
        for step in run.steps
        if isinstance(step, ModelStep) and step.response_text
    ]
    return texts[-1] if texts else None


def diff_trajectories(source: Run, replay: Run) -> TrajectoryDiff:
    source_tools = tool_steps(source)
    replay_tools = tool_steps(replay)
    count = max(len(source_tools), len(replay_tools))
    diffs = [_compare(_at(source_tools, index), _at(replay_tools, index)) for index in range(count)]
    return TrajectoryDiff(
        tool_diffs=diffs,
        source_tools=[step.name for step in source_tools],
        replay_tools=[step.name for step in replay_tools],
        final_text_source=final_text(source),
        final_text_replay=final_text(replay),
    )


def _at(steps: list[ToolStep], index: int) -> ToolStep | None:
    if index >= len(steps):
        return None
    return steps[index]


def _label(step: ToolStep) -> str:
    return f"{step.name}({canonical_json(step.arguments)})"


def _compare(left: ToolStep | None, right: ToolStep | None) -> StepDiff:
    if left is not None and right is not None:
        same_call = left.name == right.name and canonical_json(left.arguments) == canonical_json(
            right.arguments
        )
        same_outcome = left.result == right.result and left.error == right.error
        if same_call and same_outcome:
            return StepDiff(
                op="same", detail=_label(left), source_tool=left.name, replay_tool=right.name
            )
        return StepDiff(
            op="changed",
            detail=f"{_label(left)} -> {_label(right)}",
            source_tool=left.name,
            replay_tool=right.name,
        )
    if left is not None:
        return StepDiff(op="removed", detail=_label(left), source_tool=left.name)
    assert right is not None
    return StepDiff(op="added", detail=_label(right), replay_tool=right.name)
