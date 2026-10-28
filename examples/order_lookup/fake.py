"""Deterministic model for the order-lookup story. No network."""

from __future__ import annotations

from typing import Any

from examples.order_lookup.prompts import FIXED_MARK, ORDER_ID
from undoom.models import ModelResponse, ToolCall


class OrderLookupModel:
    """Refunds unless the system prompt contains the fixed-policy sentence."""

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float,
    ) -> ModelResponse:
        del model, tools, temperature
        if _has_tool_result(messages):
            if _is_fixed(messages):
                return ModelResponse(text=f"Order {ORDER_ID} has shipped.", tool_calls=[])
            return ModelResponse(text=f"I refunded order {ORDER_ID}.", tool_calls=[])
        tool_calls = [
            ToolCall(
                id="lookup_order_1",
                name="lookup_order",
                arguments={"order_id": ORDER_ID},
            )
        ]
        if not _is_fixed(messages):
            tool_calls.append(
                ToolCall(
                    id="refund_order_1",
                    name="refund_order",
                    arguments={"order_id": ORDER_ID},
                )
            )
        return ModelResponse(text=None, tool_calls=tool_calls)


def provider() -> OrderLookupModel:
    return OrderLookupModel()


def _is_fixed(messages: list[dict[str, Any]]) -> bool:
    for message in messages:
        if message.get("role") == "system" and FIXED_MARK in str(message.get("content") or ""):
            return True
    return False


def _has_tool_result(messages: list[dict[str, Any]]) -> bool:
    return any(message.get("role") == "tool" for message in messages)
