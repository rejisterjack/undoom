"""Stable JSON keys for cassette lookup.

Floats are rounded so 1.0 and 1.0000001 do not look like different tool calls.
Object keys are sorted so argument order does not matter.
"""

from __future__ import annotations

import json
from typing import Any


def normalize(value: Any) -> Any:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(item) for item in value]
    return str(value)


def canonical_json(value: Any) -> str:
    return json.dumps(
        normalize(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
