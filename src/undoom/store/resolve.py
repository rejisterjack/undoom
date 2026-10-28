"""Choose a trace store from a path or a URL."""

from __future__ import annotations

import os
from pathlib import Path

from undoom.store.base import Store
from undoom.store.sqlite import SqliteStore

DEFAULT_STORE = ".undoom/traces.sqlite"


def resolve_store(spec: str | Path | None = None) -> Store:
    if spec is None or spec == "":
        spec = os.environ.get("UNDOOM_STORE", DEFAULT_STORE)
    text = str(spec)
    if text.startswith("postgresql://") or text.startswith("postgres://"):
        from undoom.store.postgres import PostgresStore

        return PostgresStore(text)
    if text.startswith("sqlite:"):
        return SqliteStore(_sqlite_path(text))
    return SqliteStore(Path(text))


def _sqlite_path(url: str) -> Path:
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        raise ValueError(
            "SQLite URLs must look like sqlite:///relative.sqlite or sqlite:////tmp/a.sqlite"
        )
    return Path(url[len(prefix) :])
