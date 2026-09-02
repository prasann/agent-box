"""Loopback-only FastAPI application and WebSocket event transport."""

from __future__ import annotations

import asyncio
import queue
import secrets
import threading
from contextlib import asynccontextmanager
from importlib.resources import files
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .config import AppConfig
from .models import MeetingOptions, SuggestionAction
from .runtime import MeetingManager


class SuggestionSettings(BaseModel):
    enabled: bool | None = None
    interval_minutes: float | None = Field(default=None, ge=0.25, le=60)


class EventBus:
    def __init__(self) -> None:
        self.subscribers: set[asyncio.Queue] = set()
        self.loop: asyncio.AbstractEventLoop | None = None

    def attach(self) -> None:
        self.loop = asyncio.get_running_loop()

    def publish(self, event: dict[str, Any]) -> None:
        if self.loop is None:
            return

        def send() -> None:
            for subscriber in tuple(self.subscribers):
                subscriber.put_nowait(event)

        self.loop.call_soon_threadsafe(send)


class ScheduledSuggestionWorker:
    """One bounded daemon worker so provider I/O cannot hold server shutdown."""

    def __init__(self, runtime: MeetingManager) -> None:
        self.runtime = runtime
        self._requests: queue.Queue[object | None] = queue.Queue(maxsize=1)
        self._closed = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="meeting-suggestions",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def submit(self) -> None:
        if self._closed.is_set():
            return
        try:
            self._requests.put_nowait(object())
        except queue.Full:
            pass

    def close(self) -> None:
        self._closed.set()
        try:
            self._requests.put_nowait(None)
        except queue.Full:
            pass

    def _run(self) -> None:
        while True:
            request = self._requests.get()
            if request is None or self._closed.is_set():
                return
            self.runtime.scheduled_tick()


def _valid_origin(origin: str | None, host: str | None) -> bool:
    loopback_host = bool(
        host and (host == "127.0.0.1" or host.startswith("127.0.0.1:"))
    )
    return bool(origin and loopback_host and origin == f"http://{host}")


def create_app(
    manager: MeetingManager | None = None, *, access_token: str | None = None
) -> FastAPI:
    bus = EventBus()
    runtime = manager or MeetingManager(event_sink=bus.publish)
    if manager is not None:
        manager.event_sink = bus.publish

    async def cadence_loop() -> None:
        while True:
            await asyncio.sleep(1)
            if runtime.active:
                suggestion_worker.submit()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        bus.attach()
        suggestion_worker.start()
        task = asyncio.create_task(cadence_loop())
        try:
            yield
        finally:
            task.cancel()
            suggestion_worker.close()
            if runtime.active:
                await asyncio.to_thread(runtime.stop)

    suggestion_worker = ScheduledSuggestionWorker(runtime)
    app = FastAPI(
        title="Meeting Assistant",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.manager = runtime
    token = access_token or secrets.token_urlsafe(32)

    @app.middleware("http")
    async def protect_local_api(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            if request.headers.get("x-meeting-token") != token:
                return JSONResponse({"detail": "Invalid access token"}, status_code=403)
            origin = request.headers.get("origin")
            if origin and not _valid_origin(origin, request.headers.get("host")):
                return JSONResponse({"detail": "Invalid origin"}, status_code=403)
        return await call_next(request)

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        if request.query_params.get("token") != token:
            raise HTTPException(403, "Invalid access token")
        return files("meeting_assistant.static").joinpath("index.html").read_text()

    @app.get("/api/health")
    def health():
        return {"ok": True, "host": "127.0.0.1"}

    @app.get("/api/status")
    def status():
        return runtime.status()

    @app.get("/api/config")
    def config():
        settings = AppConfig.from_env()
        return {
            "stt_model": settings.stt_model,
            "ollama_model": settings.ollama_model,
            "azure_model": settings.azure_model,
            "suggestion_interval_minutes": settings.suggestion_interval_minutes,
        }

    @app.get("/api/devices")
    def devices():
        try:
            return {"devices": runtime.list_devices()}
        except RuntimeError as error:
            raise HTTPException(503, str(error)) from error

    @app.post("/api/session/start")
    def start(options: MeetingOptions):
        try:
            return runtime.start(options)
        except (RuntimeError, ValueError) as error:
            raise HTTPException(400, str(error)) from error

    @app.post("/api/session/stop")
    def stop():
        try:
            return runtime.stop()
        except RuntimeError as error:
            raise HTTPException(400, str(error)) from error

    @app.patch("/api/session/suggestions")
    def configure_suggestions(settings: SuggestionSettings):
        try:
            return runtime.set_suggestions(
                enabled=settings.enabled, interval_minutes=settings.interval_minutes
            )
        except RuntimeError as error:
            raise HTTPException(400, str(error)) from error

    @app.post("/api/session/suggestions/generate")
    def generate():
        return {"suggestions": runtime.generate_suggestions()}

    @app.patch("/api/suggestions/{suggestion_id}")
    def suggestion_action(suggestion_id: str, action: SuggestionAction):
        try:
            return runtime.suggestion_action(suggestion_id, action)
        except KeyError as error:
            raise HTTPException(404, "Suggestion not found") from error

    @app.get("/api/meetings")
    def meetings():
        return {"meetings": runtime.history()}

    @app.get("/api/meetings/{directory_name}")
    def meeting(directory_name: str):
        try:
            return runtime.meeting(directory_name)
        except FileNotFoundError as error:
            raise HTTPException(404, "Meeting not found") from error
        except ValueError as error:
            raise HTTPException(400, str(error)) from error

    @app.websocket("/ws")
    async def websocket(websocket: WebSocket):
        if (
            websocket.query_params.get("token") != token
            or not _valid_origin(
                websocket.headers.get("origin"), websocket.headers.get("host")
            )
        ):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        queue: asyncio.Queue = asyncio.Queue()
        bus.subscribers.add(queue)
        await websocket.send_json({"type": "status", "status": runtime.status()})
        try:
            while True:
                await websocket.send_json(await queue.get())
        except WebSocketDisconnect:
            pass
        finally:
            bus.subscribers.discard(queue)

    return app
