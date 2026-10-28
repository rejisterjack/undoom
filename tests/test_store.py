import json
import sqlite3

import pytest
from tests.support import failed_order_run

from undoom.errors import SchemaVersionError
from undoom.models import Run, RunStatus
from undoom.store.sqlite import SqliteStore


def test_sqlite_round_trip(tmp_path) -> None:
    store = SqliteStore(tmp_path / "traces.sqlite")
    run = failed_order_run()
    store.save_run(run)
    loaded = store.get_run(run.id)
    assert loaded is not None
    assert loaded.name == "ticket-1042"
    assert loaded.status == RunStatus.failure
    assert loaded.unexpected_tools == ["refund_order"]
    assert len(loaded.steps) == 4
    listed = store.list_runs()
    assert [item.id for item in listed] == [run.id]


def test_sqlite_replaces_an_updated_run(tmp_path) -> None:
    store = SqliteStore(tmp_path / "traces.sqlite")
    run = Run(agent="support", name="open", status=RunStatus.success)
    store.save_run(run)
    run.status = RunStatus.failure
    run.failure_reason = "marked later"
    store.save_run(run)
    loaded = store.get_run(run.id)
    assert loaded is not None
    assert loaded.status == RunStatus.failure
    assert loaded.failure_reason == "marked later"
    assert len(store.list_runs()) == 1


def test_unknown_schema_version_is_rejected(tmp_path) -> None:
    store = SqliteStore(tmp_path / "traces.sqlite")
    run = Run(agent="support", name="open", status=RunStatus.success)
    store.save_run(run)
    connection = sqlite3.connect(tmp_path / "traces.sqlite")
    payload = json.loads(connection.execute("SELECT payload FROM runs").fetchone()[0])
    payload["schema_version"] = 99
    connection.execute("UPDATE runs SET payload = ?", (json.dumps(payload),))
    connection.commit()
    connection.close()
    with pytest.raises(SchemaVersionError):
        store.get_run(run.id)
