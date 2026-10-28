"""Process-wide capture settings."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from undoom.models import Replay, Run
from undoom.redact import redact_replay, redact_run
from undoom.store.base import Store
from undoom.store.resolve import resolve_store


@dataclass
class _Memory(Store):
    """Store wrapper that redacts credentials on every write."""

    inner: Store
    patterns: list[re.Pattern[str]]

    def save_run(self, run: Run) -> None:
        self.inner.save_run(redact_run(run, self.patterns))

    def get_run(self, run_id: str) -> Run | None:
        return self.inner.get_run(run_id)

    def list_runs(self, limit: int = 50) -> list[Run]:
        return self.inner.list_runs(limit)

    def save_replay(self, replay: Replay) -> None:
        self.inner.save_replay(redact_replay(replay, self.patterns))

    def get_replay(self, replay_id: str) -> Replay | None:
        return self.inner.get_replay(replay_id)

    def list_replays(self, limit: int = 50, source_run_id: str | None = None) -> list[Replay]:
        return self.inner.list_replays(limit, source_run_id)


@dataclass
class Config:
    store_spec: str | Path | None = None
    agent: str = "default"
    redact_patterns: list[re.Pattern[str]] = field(default_factory=list)
    _store: Store | None = field(default=None, repr=False)

    def store(self) -> Store:
        if self._store is None:
            self._store = _Memory(resolve_store(self.store_spec), self.redact_patterns)
        return self._store


_config: Config | None = None


def configure(
    store: str | Path | None = None,
    agent: str | None = None,
    redact_patterns: list[str] | None = None,
) -> None:
    """Set the trace store, default agent name, and extra redaction regexes."""

    global _config
    compiled = [re.compile(pattern) for pattern in (redact_patterns or [])]
    _config = Config(
        store_spec=store,
        agent=agent or "default",
        redact_patterns=compiled,
    )


def get_config() -> Config:
    global _config
    if _config is None:
        configure()
    assert _config is not None
    return _config


def reset_config() -> None:
    global _config
    _config = None
