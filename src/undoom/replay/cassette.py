"""Recorded tool results, keyed by name and canonical arguments."""

from __future__ import annotations

from typing import Any

from undoom.canonical import canonical_json
from undoom.models import CassetteEntry, Run, ToolStep


class Cassette:
    def __init__(self, entries: list[CassetteEntry]) -> None:
        self._queues: dict[tuple[str, str], list[CassetteEntry]] = {}
        for entry in entries:
            key = (entry.name, canonical_json(entry.arguments))
            self._queues.setdefault(key, []).append(entry)

    def lookup(self, name: str, arguments: dict[str, Any]) -> CassetteEntry | None:
        queue = self._queues.get((name, canonical_json(arguments)))
        if not queue:
            return None
        return queue.pop(0)


def entries_from_run(run: Run) -> list[CassetteEntry]:
    entries: list[CassetteEntry] = []
    for step in run.steps:
        if isinstance(step, ToolStep):
            entries.append(
                CassetteEntry(
                    name=step.name,
                    arguments=step.arguments,
                    result=step.result,
                    error=step.error,
                )
            )
    return entries
