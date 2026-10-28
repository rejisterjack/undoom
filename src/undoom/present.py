"""Terminal rendering for runs and replays."""

from __future__ import annotations

from undoom.models import ModelStep, Replay, Run, ToolStep


def format_run(run: Run) -> str:
    status = run.status.value if hasattr(run.status, "value") else str(run.status)
    lines = [
        f"id: {run.id}",
        f"agent: {run.agent}",
        f"name: {run.name}",
        f"status: {status}",
        f"failure: {run.failure_reason or '-'}",
    ]
    if run.unexpected_tools:
        lines.append(f"unexpected tools: {', '.join(run.unexpected_tools)}")
    for index, step in enumerate(run.steps, start=1):
        lines.append(f"{index}. {_format_step(step)}")
    return "\n".join(lines)


def format_run_line(run: Run) -> str:
    status = run.status.value if hasattr(run.status, "value") else str(run.status)
    reason = run.failure_reason or ""
    return f"{run.id}  {status:8}  {run.agent}  {run.name}  {reason}"


def format_replay(replay: Replay) -> str:
    verdict = replay.verdict.value if hasattr(replay.verdict, "value") else str(replay.verdict)
    lines = [
        f"replay {replay.id}",
        f"source {replay.source_run_id}",
        f"verdict: {verdict}",
        "tools:",
    ]
    if not replay.diff.tool_diffs:
        lines.append("  (no tool calls)")
    for item in replay.diff.tool_diffs:
        lines.append(f"  {item.op:8} {item.detail}")
    if replay.notes:
        lines.append("notes:")
        lines.extend(f"  {note}" for note in replay.notes)
    lines.append(f"final source: {replay.diff.final_text_source or '-'}")
    lines.append(f"final replay: {replay.diff.final_text_replay or '-'}")
    return "\n".join(lines)


def _format_step(step: ModelStep | ToolStep) -> str:
    if isinstance(step, ModelStep):
        calls = ", ".join(call.name for call in step.tool_calls) or "-"
        text = step.response_text or "-"
        return f"model {step.model} tools={calls} text={text}"
    error = f" error={step.error}" if step.error else ""
    return f"tool {step.name}{error} result={step.result}"
