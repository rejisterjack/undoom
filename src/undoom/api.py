"""Local HTTP API for the diff UI.

The demo deployment does not use this process. It reads committed fixtures.
Writes are refused when `demo` is set.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from undoom.errors import PromoteError, ReplayError, UndoomError
from undoom.replay.changeset import build_changeset
from undoom.replay.engine import replay_run
from undoom.replay.providers import resolve_provider
from undoom.store.base import Store
from undoom.suite.files import load_cases, write_case
from undoom.suite.promote import promote_replay


class ReplayIn(BaseModel):
    run_id: str
    prompt_text: str | None = None
    prompt_file: str | None = None
    model: str | None = None
    tool_name: str | None = None
    tool_entrypoint: str | None = None
    provider: str | None = None


class PromoteIn(BaseModel):
    replay_id: str
    name: str
    expect_tools: bool = False


def create_app(store: Store, cases_dir: Path, *, demo: bool = False) -> FastAPI:
    application = FastAPI(title="undoom", docs_url=None, redoc_url=None)
    application.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/api/meta")
    def meta() -> dict[str, Any]:
        return {"demo": demo, "product": "undoom"}

    @application.get("/api/runs")
    def list_runs() -> dict[str, Any]:
        runs = store.list_runs(limit=200)
        return {"runs": [run.model_dump(mode="json") for run in runs]}

    @application.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> dict[str, Any]:
        run = store.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        return run.model_dump(mode="json")

    @application.get("/api/replays")
    def list_replays(source_run_id: str | None = None) -> dict[str, Any]:
        replays = store.list_replays(limit=200, source_run_id=source_run_id)
        return {"replays": [replay.model_dump(mode="json") for replay in replays]}

    @application.get("/api/replays/{replay_id}")
    def get_replay(replay_id: str) -> dict[str, Any]:
        replay = store.get_replay(replay_id)
        if replay is None:
            raise HTTPException(status_code=404, detail="replay not found")
        return replay.model_dump(mode="json")

    @application.get("/api/cases")
    def get_cases() -> dict[str, Any]:
        cases = load_cases(cases_dir)
        return {"cases": [case.model_dump(mode="json") for case in cases]}

    @application.post("/api/replay")
    def post_replay(body: ReplayIn) -> dict[str, Any]:
        _require_write()
        try:
            changeset = build_changeset(
                prompt_text=body.prompt_text,
                prompt_file=body.prompt_file,
                model=body.model,
                tool_name=body.tool_name,
                tool_entrypoint=body.tool_entrypoint,
            )
            source = store.get_run(body.run_id)
            if source is None:
                raise HTTPException(status_code=404, detail="run not found")
            replay = replay_run(source, changeset, provider=resolve_provider(body.provider))
            store.save_replay(replay)
        except HTTPException:
            raise
        except (ReplayError, UndoomError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return replay.model_dump(mode="json")

    @application.post("/api/promote")
    def post_promote(body: PromoteIn) -> dict[str, Any]:
        _require_write()
        try:
            replay = store.get_replay(body.replay_id)
            if replay is None:
                raise HTTPException(status_code=404, detail="replay not found")
            source = store.get_run(replay.source_run_id)
            if source is None:
                raise HTTPException(status_code=404, detail="source run not found")
            case = promote_replay(replay, source, name=body.name, expect_tools=body.expect_tools)
            path = write_case(case, cases_dir)
        except HTTPException:
            raise
        except (PromoteError, ReplayError, UndoomError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"path": str(path), "case": case.model_dump(mode="json")}

    def _require_write() -> None:
        if demo:
            raise HTTPException(status_code=403, detail="demo mode does not accept writes")

    return application
