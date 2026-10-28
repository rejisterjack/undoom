"""Order tools. Replay must not call these unless a case overrides one of them."""

from __future__ import annotations

calls = {"lookup_order": 0, "refund_order": 0}


def reset() -> None:
    calls["lookup_order"] = 0
    calls["refund_order"] = 0


def lookup_order(order_id: str) -> dict[str, str]:
    calls["lookup_order"] += 1
    return {"order_id": order_id, "status": "shipped"}


def refund_order(order_id: str) -> dict[str, str]:
    calls["refund_order"] += 1
    return {"order_id": order_id, "status": "refunded"}
