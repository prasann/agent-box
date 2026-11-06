"""Reads endpoints share the CLI's storage and search core."""

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ab.agents.reads.assessment import configured
from ab.agents.reads.capture import capture_pending
from ab.agents.reads.models import Snapshot
from ab.agents.reads.search import search
from ab.agents.reads.store import ReadsStore
from ab.core.config import get_settings

router = APIRouter(prefix="/api/reads")


def collection(request: Request) -> ReadsStore:
    return ReadsStore(request.app.state.reads_db or Path(get_settings().reads_db))


def local_mutation(request: Request):
    origin = request.headers.get("origin")
    allowed = {f"{request.url.scheme}://{request.url.netloc}",
               "http://127.0.0.1:5173", "http://localhost:5173"}
    if request.headers.get("x-reads-request") != "1" or (origin and origin not in allowed):
        raise HTTPException(403, "Reads mutations require a same-origin Control Center request")


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    constraints: str = Field(default="", max_length=2000)
    provider: Literal["lexical", "llm", "decision"] = "lexical"
    local_only: bool = True
    limit: int = Field(default=5, ge=1, le=20)


class CaptureRequest(BaseModel):
    document: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class PolicyRequest(BaseModel):
    note: str = Field(default="", max_length=10_000)
    cloud_allowed: bool = False


@router.get("/status")
def status(store: ReadsStore = Depends(collection)):
    result = store.status()
    settings = get_settings()
    result["providers"] = {"lexical": True, "llm": configured(settings, "llm"),
                           "decision": configured(settings, "decision")}
    return result


@router.post("/search", dependencies=[Depends(local_mutation)])
def search_readings(body: SearchRequest, store: ReadsStore = Depends(collection)):
    try:
        result = search(store, get_settings(), **body.model_dump())
        result.pop("diagnostics", None)
        return result
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/snapshots", dependencies=[Depends(local_mutation)])
def accept_snapshot(body: Snapshot, dry_run: bool = True, store: ReadsStore = Depends(collection)):
    try:
        return store.ingest(body, dry_run)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/capture", dependencies=[Depends(local_mutation)])
def capture(body: CaptureRequest, store: ReadsStore = Depends(collection)):
    try:
        return capture_pending(store, body.document, body.limit)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.get("/documents/{document}")
def document_detail(document: str, store: ReadsStore = Depends(collection)):
    item = next((item for item in store.documents() if item["id"] == document), None)
    if item is None:
        raise HTTPException(404, "Reading not found in the active collection")
    return item | {"passages": store.passages(document)}


@router.patch("/documents/{document}", dependencies=[Depends(local_mutation)])
def policy(document: str, body: PolicyRequest, store: ReadsStore = Depends(collection)):
    if not any(item["id"] == document for item in store.documents()):
        raise HTTPException(404, "Reading not found in the active collection")
    store.update_policy(document, body.note, body.cloud_allowed)
    return {"document": document, **body.model_dump()}