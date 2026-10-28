"""Persistence for captured runs and replays."""

from __future__ import annotations

from typing import Protocol

from undoom.models import Replay, Run


class Store(Protocol):
    def save_run(self, run: Run) -> None: ...

    def get_run(self, run_id: str) -> Run | None: ...

    def list_runs(self, limit: int = 50) -> list[Run]: ...

    def save_replay(self, replay: Replay) -> None: ...

    def get_replay(self, replay_id: str) -> Replay | None: ...

    def list_replays(self, limit: int = 50, source_run_id: str | None = None) -> list[Replay]: ...
