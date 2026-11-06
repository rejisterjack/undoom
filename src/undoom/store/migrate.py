"""Minimal schema version bump helper for Undoom stores.

Document payloads already carry `schema_version` (see `undoom.models`).
This helper tracks the on-disk table schema so future additive DDL can bump
without rewriting existing stores. Step migrations are intentionally empty
until a real shape change lands.
"""

from __future__ import annotations

from typing import Any

# Bump when store DDL changes. Keep in sync with models.SCHEMA_VERSION when both move.
SCHEMA_VERSION = 1

_META_DDL = """
CREATE TABLE IF NOT EXISTS undoom_schema (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version INTEGER NOT NULL
)
"""


def ensure_schema_version(execute: Any, *, current: int = SCHEMA_VERSION) -> int:
    """Ensure the meta table exists and return the effective schema version.

    `execute` is a callable like `conn.execute` (sqlite) or a wrapper around
    a DB-API cursor. It must support `execute(sql)` / `execute(sql, params)`
    and return an object with `.fetchone()`.
    """

    execute(_META_DDL)
    row = execute("SELECT version FROM undoom_schema WHERE id = 1").fetchone()
    if row is None:
        execute("INSERT INTO undoom_schema (id, version) VALUES (1, ?)", (current,))
        return current
    version = int(row[0])
    if version < current:
        # Future: run step functions for version+1 .. current here.
        execute("UPDATE undoom_schema SET version = ? WHERE id = 1", (current,))
        return current
    return version


def ensure_schema_version_pg(cur: Any, *, current: int = SCHEMA_VERSION) -> int:
    """Postgres variant using `%s` placeholders."""

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS undoom_schema (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        )
        """
    )
    cur.execute("SELECT version FROM undoom_schema WHERE id = 1")
    row = cur.fetchone()
    if row is None:
        cur.execute("INSERT INTO undoom_schema (id, version) VALUES (1, %s)", (current,))
        return current
    version = int(row[0])
    if version < current:
        cur.execute("UPDATE undoom_schema SET version = %s WHERE id = 1", (current,))
        return current
    return version
