"""SQLite trace log. The default store for a local install."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from undoom.models import Replay, Run

T = TypeVar("T")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    failure_reason TEXT,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at);

CREATE TABLE IF NOT EXISTS replays (
    id TEXT PRIMARY KEY,
    source_run_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_replays_source ON replays(source_run_id);
CREATE INDEX IF NOT EXISTS idx_replays_created ON replays(created_at);
"""


class SqliteStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._exec(lambda conn: conn.executescript(_SCHEMA))

    def save_run(self, run: Run) -> None:
        payload = run.model_dump(mode="json")

        def write(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO runs (id, agent, status, created_at, failure_reason, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    agent = excluded.agent,
                    status = excluded.status,
                    created_at = excluded.created_at,
                    failure_reason = excluded.failure_reason,
                    payload = excluded.payload
                """,
                (
                    run.id,
                    run.agent,
                    _status(run),
                    payload["created_at"],
                    run.failure_reason,
                    json.dumps(payload),
                ),
            )

        self._exec(write)

    def get_run(self, run_id: str) -> Run | None:
        row = self._exec(
            lambda conn: conn.execute("SELECT payload FROM runs WHERE id = ?", (run_id,)).fetchone()
        )
        if row is None:
            return None
        return Run.model_validate(json.loads(row[0]))

    def list_runs(self, limit: int = 50) -> list[Run]:
        rows = self._exec(
            lambda conn: conn.execute(
                "SELECT payload FROM runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        )
        return [Run.model_validate(json.loads(row[0])) for row in rows]

    def save_replay(self, replay: Replay) -> None:
        payload = replay.model_dump(mode="json")

        def write(conn: sqlite3.Connection) -> None:
            conn.execute(
                """
                INSERT INTO replays (id, source_run_id, created_at, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    source_run_id = excluded.source_run_id,
                    created_at = excluded.created_at,
                    payload = excluded.payload
                """,
                (replay.id, replay.source_run_id, payload["created_at"], json.dumps(payload)),
            )

        self._exec(write)

    def get_replay(self, replay_id: str) -> Replay | None:
        row = self._exec(
            lambda conn: conn.execute(
                "SELECT payload FROM replays WHERE id = ?",
                (replay_id,),
            ).fetchone()
        )
        if row is None:
            return None
        return Replay.model_validate(json.loads(row[0]))

    def list_replays(self, limit: int = 50, source_run_id: str | None = None) -> list[Replay]:
        def read(conn: sqlite3.Connection) -> list[sqlite3.Row]:
            if source_run_id is None:
                return list(
                    conn.execute(
                        "SELECT payload FROM replays ORDER BY created_at DESC LIMIT ?",
                        (limit,),
                    ).fetchall()
                )
            return list(
                conn.execute(
                    """
                    SELECT payload FROM replays
                    WHERE source_run_id = ?
                    ORDER BY created_at DESC LIMIT ?
                    """,
                    (source_run_id, limit),
                ).fetchall()
            )

        rows = self._exec(read)
        return [Replay.model_validate(json.loads(row[0])) for row in rows]

    def clear(self) -> None:
        def wipe(conn: sqlite3.Connection) -> None:
            conn.execute("DELETE FROM replays")
            conn.execute("DELETE FROM runs")

        self._exec(wipe)

    def _exec(self, fn: Callable[[sqlite3.Connection], T]) -> T:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            result = fn(conn)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _status(run: Run) -> str:
    status = run.status
    return status.value if hasattr(status, "value") else str(status)
