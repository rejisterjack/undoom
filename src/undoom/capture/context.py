"""Record a tool-calling run."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

from undoom.config import get_config
from undoom.models import ModelStep, Run, RunStatus, ToolCall, ToolStep


class ToolHandle:
    """Receiver for the result of one tool call."""

    def __init__(self, step: ToolStep) -> None:
        self._step = step

    def record(self, result: Any) -> None:
        self._step.result = result


class RunRecorder:
    """Open run. Steps are stored when the `run` block exits."""

    def __init__(self, record: Run) -> None:
        self.run = record
        self.failed = False

    def fail(self, reason: str, unexpected_tools: list[str] | None = None) -> None:
        """Mark the run as a failure.

        `unexpected_tools` names the calls that must not return. Promote turns
        those names into the regression expectation.
        """

        self.failed = True
        if self.run.failure_reason is None:
            self.run.failure_reason = reason
        for name in unexpected_tools or []:
            if name not in self.run.unexpected_tools:
                self.run.unexpected_tools.append(name)

    def record_model(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        response_text: str | None,
        tool_calls: list[ToolCall],
        params: dict[str, Any] | None = None,
        usage: dict[str, Any] | None = None,
    ) -> None:
        self.run.steps.append(
            ModelStep(
                model=model,
                messages=json.loads(json.dumps(messages, default=str)),
                params=json.loads(json.dumps(params or {}, default=str)),
                response_text=response_text,
                tool_calls=tool_calls,
                usage=usage,
            )
        )

    @contextmanager
    def tool(
        self,
        name: str,
        arguments: dict[str, Any],
        call_id: str | None = None,
    ) -> Iterator[ToolHandle]:
        step = ToolStep(
            call_id=call_id or uuid4().hex,
            name=name,
            arguments=arguments,
        )
        handle = ToolHandle(step)
        try:
            yield handle
        except Exception as exc:
            step.error = f"{type(exc).__name__}: {exc}"
            self.fail(f"tool {name} failed: {exc}")
            raise
        finally:
            self.run.steps.append(step)


@contextmanager
def run(agent: str | None = None, name: str | None = None) -> Iterator[RunRecorder]:
    """Capture one agent run and write it when the block exits."""

    config = get_config()
    record = Run(agent=agent or config.agent, name=name or "run")
    recorder = RunRecorder(record)
    try:
        yield recorder
    except Exception as exc:
        if recorder.failed:
            record.status = RunStatus.failure
        elif record.status == RunStatus.running:
            record.status = RunStatus.error
            record.failure_reason = f"{type(exc).__name__}: {exc}"
        raise
    else:
        if recorder.failed:
            record.status = RunStatus.failure
        elif record.status == RunStatus.running:
            record.status = RunStatus.success
    finally:
        store = config.store()
        store.save_run(recorder.run)
        stored = store.get_run(recorder.run.id)
        if stored is not None:
            recorder.run = stored
