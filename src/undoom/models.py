"""Versioned documents for runs, replays, and regression cases."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from undoom.errors import SchemaVersionError

SCHEMA_VERSION = 1


def new_id() -> str:
    return uuid4().hex


def utc_now() -> datetime:
    return datetime.now(UTC)


class SchemaModel(BaseModel):
    """JSON document stamped with the schema generation this build understands."""

    schema_version: int = SCHEMA_VERSION

    def model_post_init(self, context: Any) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise SchemaVersionError(
                f"unsupported schema_version {self.schema_version}; "
                f"this build supports {SCHEMA_VERSION}"
            )


class RunStatus(StrEnum):
    running = "running"
    success = "success"
    failure = "failure"
    error = "error"


class Verdict(StrEnum):
    fixed = "fixed"
    still_failing = "still_failing"
    diverged = "diverged"
    error = "error"


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class ModelStep(BaseModel):
    kind: Literal["model"] = "model"
    model: str
    messages: list[dict[str, Any]]
    params: dict[str, Any] = Field(default_factory=dict)
    response_text: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: dict[str, Any] | None = None


class ToolStep(BaseModel):
    kind: Literal["tool"] = "tool"
    call_id: str
    name: str
    arguments: dict[str, Any]
    result: Any = None
    error: str | None = None


Step = Annotated[ModelStep | ToolStep, Field(discriminator="kind")]


class Run(SchemaModel):
    id: str = Field(default_factory=new_id)
    agent: str
    name: str
    status: RunStatus = RunStatus.running
    failure_reason: str | None = None
    unexpected_tools: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    steps: list[Step] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    text: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)


class Changeset(BaseModel):
    """Exactly one of prompt, model, or tool implementation."""

    kind: Literal["prompt", "model", "tool"]
    prompt_text: str | None = None
    prompt_file: str | None = None
    model: str | None = None
    tool_name: str | None = None
    tool_entrypoint: str | None = None

    def check(self) -> None:
        if self.kind == "prompt":
            self._reject_other(model=True, tool=True)
            has_text = self.prompt_text is not None
            has_file = self.prompt_file is not None
            if has_text and has_file:
                raise ValueError("a prompt change takes prompt text or a prompt file, not both")
            if not has_text and not has_file:
                raise ValueError("a prompt change needs prompt text or a prompt file")
        elif self.kind == "model":
            self._reject_other(prompt=True, tool=True)
            if not self.model:
                raise ValueError("a model change needs a model id")
        elif self.kind == "tool":
            self._reject_other(prompt=True, model=True)
            if not self.tool_name or not self.tool_entrypoint:
                raise ValueError("a tool change needs a tool name and an entrypoint")
        else:
            raise ValueError(f"unknown change {self.kind}")

    def _reject_other(
        self, *, prompt: bool = False, model: bool = False, tool: bool = False
    ) -> None:
        if prompt and (self.prompt_text is not None or self.prompt_file is not None):
            raise ValueError("this change cannot also set a prompt")
        if model and self.model:
            raise ValueError("this change cannot also set a model")
        if tool and (self.tool_name or self.tool_entrypoint):
            raise ValueError("this change cannot also set a tool")


class StepDiff(BaseModel):
    op: Literal["same", "added", "removed", "changed"]
    detail: str
    source_tool: str | None = None
    replay_tool: str | None = None


class TrajectoryDiff(BaseModel):
    tool_diffs: list[StepDiff] = Field(default_factory=list)
    source_tools: list[str] = Field(default_factory=list)
    replay_tools: list[str] = Field(default_factory=list)
    final_text_source: str | None = None
    final_text_replay: str | None = None


class Replay(SchemaModel):
    id: str = Field(default_factory=new_id)
    source_run_id: str
    created_at: datetime = Field(default_factory=utc_now)
    changeset: Changeset
    run: Run
    diff: TrajectoryDiff
    verdict: Verdict
    notes: list[str] = Field(default_factory=list)


class CassetteEntry(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: Any = None
    error: str | None = None


class Expectation(BaseModel):
    failure_reason: str | None = None
    absent_tools: list[str] = Field(default_factory=list)
    absent_tool_errors: list[str] = Field(default_factory=list)
    required_tool_sequence: list[str] | None = None


class Case(SchemaModel):
    name: str
    source_failure_id: str
    replay_id: str
    created_at: datetime = Field(default_factory=utc_now)
    messages: list[dict[str, Any]]
    model: str
    tools_schema: list[dict[str, Any]] = Field(default_factory=list)
    cassette: list[CassetteEntry]
    changeset: Changeset
    expectation: Expectation


class CaseResult(BaseModel):
    name: str
    status: Literal["passed", "failed", "error"]
    message: str = ""


class SuiteReport(BaseModel):
    cases: list[CaseResult] = Field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for case in self.cases if case.status == "passed")

    @property
    def failed(self) -> int:
        return sum(1 for case in self.cases if case.status != "passed")
