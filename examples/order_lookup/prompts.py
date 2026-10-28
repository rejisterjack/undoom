"""Scripted order-lookup agent used by the offline demo and the test suite."""

from __future__ import annotations

FIXED_MARK = "Only refund when the user explicitly asks for a refund."

BUGGY = (
    "You are a support agent. Look up the order the user mentions. "
    "Always refund that order after you look it up."
)

FIXED = (
    "You are a support agent. Look up the order the user mentions. "
    "Only refund when the user explicitly asks for a refund."
)

USER_MESSAGE = "Where is order 1042?"

ORDER_ID = "1042"

TOOLS_SCHEMA: list[dict[str, object]] = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order by id.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "refund_order",
            "description": "Refund an order by id.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
]
