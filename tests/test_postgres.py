import os

import pytest
from tests.support import failed_order_run

from undoom.models import Run, RunStatus
from undoom.store.postgres import PostgresStore


@pytest.mark.postgres
def test_postgres_round_trip() -> None:
    dsn = os.environ.get("UNDOOM_TEST_POSTGRES")
    if not dsn:
        pytest.skip("set UNDOOM_TEST_POSTGRES to run the Postgres store test")
    store = PostgresStore(dsn)
    store.clear()
    run = failed_order_run()
    store.save_run(run)
    loaded = store.get_run(run.id)
    assert loaded is not None
    assert loaded.failure_reason == run.failure_reason
    assert len(loaded.steps) == 4
    replay_run = Run(agent="support", name="other", status=RunStatus.success)
    store.save_run(replay_run)
    assert {item.id for item in store.list_runs()} == {run.id, replay_run.id}
    store.clear()
