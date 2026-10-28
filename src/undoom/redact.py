"""Strip credential-shaped strings before a run is written to disk."""

from __future__ import annotations

import re
from typing import Any

from undoom.models import Replay, Run

REDACTED = "[REDACTED]"

SECRET_KEYS = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "api-key",
    "api_key",
    "apikey",
    "secret",
    "password",
    "access_token",
}

DEFAULT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_\-]{8,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(
        r"(?i)\b(api[_-]?key|authorization|access[_-]?token)"
        r"(\s*[:=]\s*['\"]?)([^'\"\s,]+)"
    ),
)


def redact(value: Any, extra: list[re.Pattern[str]] | None = None) -> Any:
    patterns = [*DEFAULT_PATTERNS, *(extra or [])]
    return _walk(value, patterns)


def redact_run(run: Run, extra: list[re.Pattern[str]] | None = None) -> Run:
    return Run.model_validate(redact(run.model_dump(mode="json"), extra))


def redact_replay(replay: Replay, extra: list[re.Pattern[str]] | None = None) -> Replay:
    return Replay.model_validate(redact(replay.model_dump(mode="json"), extra))


def _walk(value: Any, patterns: list[re.Pattern[str]]) -> Any:
    if isinstance(value, dict):
        cleaned: dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and key.lower() in SECRET_KEYS:
                cleaned[key] = REDACTED
            else:
                cleaned[key] = _walk(item, patterns)
        return cleaned
    if isinstance(value, list):
        return [_walk(item, patterns) for item in value]
    if isinstance(value, str):
        text = value
        for pattern in patterns:
            text = pattern.sub(_replacement, text)
        return text
    return value


def _replacement(match: re.Match[str]) -> str:
    if match.lastindex and match.lastindex >= 3:
        return f"{match.group(1)}{match.group(2)}{REDACTED}"
    return REDACTED
