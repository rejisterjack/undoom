"""Postgres trace log for a shared team history.

SQLite remains the default. Set UNDOOM_STORE to a postgresql:// URL to use this.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, TypeVar

from undoom.models import Replay, Run

T = TypeVar("T")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    agent TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    failure_reason TEXT,
    payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent);
CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at);

CREATE TABLE IF NOT EXISTS replays (
    id TEXT PRIMARY KEY,
    source_run_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_replays_source ON replays(source_run_id);
CREATE INDEX IF NOT EXISTS idx_replays_created ON replays(created_at);
"""


class PostgresStore:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        statements = [part.strip() for part in _SCHEMA.split(";") if part.strip()]

        def init(cur: Any) -> None:
            for statement in statements:
                cur.execute(statement)

        self._exec(init)

    def save_run(self, run: Run) -> None:
        payload = run.model_dump(mode="json")
        status = run.status.value if hasattr(run.status, "value") else str(run.status)

        def write(cur: Any) -> None:
            cur.execute(
                """
                INSERT INTO runs (id, agent, status, created_at, failure_reason, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    agent = EXCLUDED.agent,
                    status = EXCLUDED.status,
                    created_at = EXCLUDED.created_at,
                    failure_reason = EXCLUDED.failure_reason,
                    payload = EXCLUDED.payload
                """,
                (
                    run.id,
                    run.agent,
                    status,
                    payload["created_at"],
                    run.failure_reason,
                    _json(payload),
                ),
            )

        self._exec(write)

    def get_run(self, run_id: str) -> Run | None:
        row = self._exec(
            lambda cur: cur.execute("SELECT payload FROM runs WHERE id = %s", (run_id,)).fetchone()
        )
        if row is None:
            return None
        return Run.model_validate(_payload(row[0]))

    def list_runs(self, limit: int = 50) -> list[Run]:
        rows = self._exec(
            lambda cur: cur.execute(
                "SELECT payload FROM runs ORDER BY created_at DESC LIMIT %s",
                (limit,),
            ).fetchall()
        )
        return [Run.model_validate(_payload(row[0])) for row in rows]

    def save_replay(self, replay: Replay) -> None:
        payload = replay.model_dump(mode="json")

        def write(cur: Any) -> None:
            cur.execute(
                """
                INSERT INTO replays (id, source_run_id, created_at, payload)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    source_run_id = EXCLUDED.source_run_id,
                    created_at = EXCLUDED.created_at,
                    payload = EXCLUDED.payload
                """,
                (replay.id, replay.source_run_id, payload["created_at"], _json(payload)),
            )

        self._exec(write)

    def get_replay(self, replay_id: str) -> Replay | None:
        row = self._exec(
            lambda cur: cur.execute(
                "SELECT payload FROM replays WHERE id = %s",
                (replay_id,),
            ).fetchone()
        )
        if row is None:
            return None
        return Replay.model_validate(_payload(row[0]))

    def list_replays(self, limit: int = 50, source_run_id: str | None = None) -> list[Replay]:
        def read(cur: Any) -> list[Any]:
            if source_run_id is None:
                return list(
                    cur.execute(
                        "SELECT payload FROM replays ORDER BY created_at DESC LIMIT %s",
                        (limit,),
                    ).fetchall()
                )
            return list(
                cur.execute(
                    """
                    SELECT payload FROM replays
                    WHERE source_run_id = %s
                    ORDER BY created_at DESC LIMIT %s
                    """,
                    (source_run_id, limit),
                ).fetchall()
            )

        rows = self._exec(read)
        return [Replay.model_validate(_payload(row[0])) for row in rows]

    def clear(self) -> None:
        def wipe(cur: Any) -> None:
            cur.execute("DELETE FROM replays")
            cur.execute("DELETE FROM runs")

        self._exec(wipe)

    def _exec(self, fn: Callable[[Any], T]) -> T:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "Postgres support is not installed. Install it with: pip install 'undoom[postgres]'"
            ) from exc
        with psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                return fn(cur)


def _json(payload: dict[str, Any]) -> Any:
    from psycopg.types.json import Jsonb

    return Jsonb(payload)


def _payload(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value
