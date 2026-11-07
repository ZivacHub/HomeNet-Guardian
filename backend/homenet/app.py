"""The web app: creates the FastAPI server and the simulated-day runtime."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable

from fastapi import FastAPI

from . import db
from .runtime import Runtime

APP_NAME = "HomeNet Guardian"
DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "homenet.db"
TICK_SECONDS = 5

log = logging.getLogger("homenet")


def _make_runtime(app: FastAPI) -> Runtime:
    path = app.state.db_path
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    rt = Runtime(db.connect(path), clock=app.state.clock or datetime.now)
    app.state.runtime = rt
    return rt


async def _tick_loop(rt: Runtime) -> None:
    while True:
        await asyncio.sleep(TICK_SECONDS)
        try:
            await asyncio.to_thread(rt.tick)
        except Exception:       # keep the loop alive; the next tick tries again
            log.exception("simulation tick failed")


def create_app(db_path: str = str(DEFAULT_DB), clock: Callable[[], datetime] | None = None,
               background: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        rt = app.state.runtime or _make_runtime(app)
        await asyncio.to_thread(rt.start)
        await asyncio.to_thread(rt.tick)
        task = asyncio.create_task(_tick_loop(rt)) if background else None
        try:
            yield
        finally:
            if task:
                task.cancel()
            await asyncio.to_thread(rt.close)
            app.state.runtime = None

    app = FastAPI(title=APP_NAME, lifespan=lifespan)
    app.state.db_path = str(db_path)
    app.state.clock = clock
    app.state.runtime = None
    if str(db_path) == ":memory:":       # cheap; real files are opened in the lifespan
        _make_runtime(app)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "name": APP_NAME}

    from .api import router
    from .auth import router as auth_router
    app.include_router(auth_router)
    app.include_router(router)
    return app


app = create_app()
