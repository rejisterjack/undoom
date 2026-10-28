from fastapi.testclient import TestClient
from tests.support import failed_order_run

from examples.order_lookup.prompts import FIXED
from undoom.api import create_app
from undoom.store.sqlite import SqliteStore


def test_api_reads_runs_and_rejects_demo_writes(tmp_path) -> None:
    store = SqliteStore(tmp_path / "traces.sqlite")
    source = failed_order_run()
    store.save_run(source)
    cases = tmp_path / "cases"
    demo = TestClient(create_app(store, cases, demo=True))
    listing = demo.get("/api/runs")
    assert listing.status_code == 200
    assert listing.json()["runs"][0]["id"] == source.id
    refused = demo.post("/api/replay", json={"run_id": source.id, "prompt_text": FIXED})
    assert refused.status_code == 403
    meta = demo.get("/api/meta")
    assert meta.json()["demo"] is True


def test_api_replay_and_promote(tmp_path) -> None:
    store = SqliteStore(tmp_path / "traces.sqlite")
    source = failed_order_run()
    store.save_run(source)
    cases = tmp_path / "cases"
    client = TestClient(create_app(store, cases, demo=False))
    replayed = client.post(
        "/api/replay",
        json={
            "run_id": source.id,
            "prompt_text": FIXED,
            "provider": "examples.order_lookup.fake:provider",
        },
    )
    assert replayed.status_code == 200, replayed.text
    body = replayed.json()
    assert body["verdict"] == "fixed"
    assert any(item["op"] == "removed" for item in body["diff"]["tool_diffs"])
    promoted = client.post(
        "/api/promote",
        json={"replay_id": body["id"], "name": "no-unsolicited-refund"},
    )
    assert promoted.status_code == 200, promoted.text
    listed = client.get("/api/cases")
    assert listed.json()["cases"][0]["name"] == "no-unsolicited-refund"
    missing = client.get("/api/runs/missing")
    assert missing.status_code == 404


def test_cors_allows_local_ui_ports(tmp_path) -> None:
    store = SqliteStore(tmp_path / "traces.sqlite")
    client = TestClient(create_app(store, tmp_path / "cases", demo=False))
    response = client.options(
        "/api/replay",
        headers={
            "Origin": "http://127.0.0.1:3010",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3010"
