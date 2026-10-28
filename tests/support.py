"""Helpers shared by replay and CLI tests."""

from __future__ import annotations

from typing import Any

from examples.order_lookup.prompts import BUGGY, TOOLS_SCHEMA, USER_MESSAGE
from undoom.models import ModelResponse, ModelStep, Run, RunStatus, ToolCall, ToolStep

lost_calls: list[str] = []


def lookup_lost(order_id: str) -> dict[str, str]:
    lost_calls.append(order_id)
    return {"order_id": order_id, "status": "lost"}


class Scripted:
    def __init__(self, responses: list[ModelResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float,
    ) -> ModelResponse:
        self.calls.append(
            {
                "model": model,
                "messages": messages,
                "tools": tools,
                "temperature": temperature,
            }
        )
        if not self.responses:
            return ModelResponse(text="done", tool_calls=[])
        return self.responses.pop(0)


def failed_order_run() -> Run:
    messages = [
        {"role": "system", "content": BUGGY},
        {"role": "user", "content": USER_MESSAGE},
    ]
    return Run(
        agent="support",
        name="ticket-1042",
        status=RunStatus.failure,
        failure_reason="refunded without an explicit request",
        unexpected_tools=["refund_order"],
        steps=[
            ModelStep(
                model="fake-order",
                messages=messages,
                params={"tools": TOOLS_SCHEMA, "temperature": 0},
                tool_calls=[
                    ToolCall(id="1", name="lookup_order", arguments={"order_id": "1042"}),
                    ToolCall(id="2", name="refund_order", arguments={"order_id": "1042"}),
                ],
            ),
            ToolStep(
                call_id="1",
                name="lookup_order",
                arguments={"order_id": "1042"},
                result={"order_id": "1042", "status": "shipped"},
            ),
            ToolStep(
                call_id="2",
                name="refund_order",
                arguments={"order_id": "1042"},
                result={"order_id": "1042", "status": "refunded"},
            ),
            ModelStep(
                model="fake-order",
                messages=messages,
                response_text="I refunded order 1042.",
                tool_calls=[],
            ),
        ],
    )
