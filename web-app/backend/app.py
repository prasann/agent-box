"""FastAPI application for the local Mission Control dashboard."""

import asyncio
from pathlib import Path
from typing import Any, Literal

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ab.agents.findtab.database import BookmarkDatabase
from ab.agents.findtab.indexer import BookmarkIndexer
from ab.agents.findtab.search import BookmarkSearcher
from ab.agents.shell.purger import SafePurger
from ab.agents.text.checker import GrammarChecker
from ab.core.azure_openai_client import AzureOpenAIClient
from ab.core.config import get_settings

from .library import default_library_root, get_library_item, list_library
from .registry import AGENT_MANIFESTS
from .runs import RunStore


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=12, ge=1, le=50)
    use_llm: bool = True


class IndexRequest(BaseModel):
    force: bool = False
    hours: int | None = Field(default=None, ge=1, le=24 * 30)


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)
    mode: Literal["fix", "rewrite"]


def _azure_client() -> AzureOpenAIClient:
    settings = get_settings()
    return AzureOpenAIClient(
        settings.azure_openai_endpoint,
        settings.azure_openai_deployment,
        settings.azure_openai_api_version,
    )


def _health() -> dict[str, Any]:
    settings = get_settings()
    db_path = Path(settings.findtab_db_path).expanduser()
    azure_configured = bool(settings.azure_openai_endpoint)
    azure_available = _azure_client().is_available() if azure_configured else False

    try:
        response = requests.get(f"{settings.ollama_url.rstrip('/')}/api/tags", timeout=1)
        ollama_available = response.ok
    except requests.RequestException:
        ollama_available = False

    services = {
        "azure": {
            "status": "healthy" if azure_available else "unavailable",
            "detail": (
                "Azure OpenAI is configured and Entra authentication is ready."
                if azure_available
                else "Azure OpenAI needs an endpoint and a valid Entra sign-in."
            ),
            "remedy": (
                None
                if azure_available
                else "Set AB_AZURE_OPENAI_ENDPOINT in ~/.agb/.env, then run: az login"
            ),
        },
        "ollama": {
            "status": "healthy" if ollama_available else "unavailable",
            "detail": (
                f"Ollama is responding at {settings.ollama_url}."
                if ollama_available
                else f"No Ollama server responded at {settings.ollama_url}."
            ),
            "remedy": None if ollama_available else "Run: ollama serve",
        },
        "database": {
            "status": "healthy" if db_path.exists() else "unavailable",
            "detail": (
                f"FindTab index is available at {db_path}."
                if db_path.exists()
                else f"FindTab index was not found at {db_path}."
            ),
            "remedy": None if db_path.exists() else "Run: agb findtab index",
        },
    }
    return {
        "status": "healthy"
        if all(service["status"] == "healthy" for service in services.values())
        else "degraded",
        "services": services,
    }


def _search_bookmarks(request: SearchRequest) -> list[dict[str, Any]]:
    settings = get_settings()
    db_path = Path(settings.findtab_db_path).expanduser()
    if not db_path.exists():
        raise FileNotFoundError("FindTab has no index yet. Run an index refresh first.")

    db = BookmarkDatabase(str(db_path))
    client = _azure_client() if request.use_llm else None
    if client is not None and not client.is_available():
        client = None
    results = BookmarkSearcher(db, client).search(request.query, limit=request.limit)
    return [result.model_dump(mode="json") | {"time_ago": result.time_ago()} for result in results]


def _run_index(
    request: IndexRequest,
    emit: Any,
) -> dict[str, Any]:
    settings = get_settings()
    client = _azure_client()
    if not client.is_available():
        raise RuntimeError("Azure OpenAI is unavailable. Check the endpoint and `az login`.")

    emit("progress", {"message": "Reading browser history", "percent": 10})
    db = BookmarkDatabase(settings.findtab_db_path)
    indexer = BookmarkIndexer(db, settings, client)
    stats = indexer.run_incremental_index(force_full=request.force, hours_back=request.hours)
    emit("progress", {"message": "Bookmark index refreshed", "percent": 100})
    return {
        "extracted": stats.extracted,
        "already_indexed": stats.already_indexed,
        "saved": stats.enriched,
        "failed": stats.failed,
    }


def _process_text(request: TextRequest) -> str:
    settings = get_settings()
    client = _azure_client()
    if not client.is_available():
        raise RuntimeError("Azure OpenAI is unavailable. Check the endpoint and `az login`.")
    checker = GrammarChecker(client, settings)
    return checker.fix_grammar(request.text) if request.mode == "fix" else checker.rewrite(
        request.text
    )


def create_app(
    library_root: Path | None = None,
    static_dir: Path | None = None,
) -> FastAPI:
    """Create the API, optionally overriding filesystem roots for tests."""
    app = FastAPI(title="Prasanna's Control Center", version="0.1.0")
    app.state.runs = RunStore()
    app.state.library_root = library_root or default_library_root()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/agents")
    async def agents() -> list[dict[str, Any]]:
        health = await asyncio.to_thread(_health)
        statuses = {
            "findtab": health["services"]["database"]["status"],
            "text": health["services"]["azure"]["status"],
            "shell": "healthy" if (Path.home() / ".zsh_history").exists() else "unavailable",
            "library": "healthy" if app.state.library_root.exists() else "unavailable",
        }
        return [manifest | {"status": statuses[manifest["id"]]} for manifest in AGENT_MANIFESTS]

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return await asyncio.to_thread(_health)

    @app.post("/api/findtab/search")
    async def search(request: SearchRequest) -> dict[str, Any]:
        try:
            results = await asyncio.to_thread(_search_bookmarks, request)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"results": results}

    @app.get("/api/findtab/status")
    async def findtab_status() -> dict[str, Any]:
        settings = get_settings()
        db_path = Path(settings.findtab_db_path).expanduser()
        if not db_path.exists():
            return {"exists": False, "db_path": str(db_path)}
        stats = await asyncio.to_thread(BookmarkDatabase(str(db_path)).get_stats)
        return {"exists": True, **stats}

    @app.post("/api/findtab/index", status_code=202)
    async def index(request: IndexRequest) -> dict[str, Any]:
        return app.state.runs.start(
            "findtab",
            "index",
            lambda emit: _run_index(request, emit),
        )

    @app.post("/api/text")
    async def text(request: TextRequest) -> dict[str, str]:
        try:
            result = await asyncio.to_thread(_process_text, request)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {"result": result}

    @app.get("/api/shell/preview")
    async def shell_preview() -> dict[str, Any]:
        try:
            return await asyncio.to_thread(SafePurger().preview_details)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/library")
    async def library() -> dict[str, Any]:
        items = await asyncio.to_thread(list_library, app.state.library_root)
        groups: dict[str, int] = {}
        for item in items:
            groups[item["kind"]] = groups.get(item["kind"], 0) + 1
        return {"items": items, "groups": groups}

    @app.get("/api/library/{item_id}")
    async def library_item(item_id: str) -> dict[str, Any]:
        try:
            return await asyncio.to_thread(
                get_library_item, item_id, app.state.library_root
            )
        except (FileNotFoundError, ValueError):
            raise HTTPException(status_code=404, detail="Library item not found") from None

    @app.get("/api/runs/{run_id}")
    async def run(run_id: str) -> dict[str, Any]:
        try:
            return app.state.runs.get(run_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Run not found") from None

    @app.get("/api/runs/{run_id}/events")
    async def run_events(run_id: str) -> StreamingResponse:
        try:
            app.state.runs.get(run_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Run not found") from None
        return StreamingResponse(
            app.state.runs.stream(run_id),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    assets = static_dir or Path(__file__).resolve().parent / "static"
    if assets.exists():
        app.mount("/", StaticFiles(directory=assets, html=True), name="web")

    return app


app = create_app()
