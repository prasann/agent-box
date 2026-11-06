"""Exercise Reads HTTP contracts without live providers or browser data."""

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(library_root=tmp_path, reads_db=tmp_path / "reads.db"))


SNAPSHOT = {
    "source_id": "synthetic", "profile_id": "test-profile", "folder_id": "folder-42",
    "complete": True, "revision": 1,
    "items": [{"item_id": "bookmark", "url": "https://example.org/read", "title": "Latency numbers"}],
}
HEADERS = {"X-Reads-Request": "1"}


def test_snapshot_preview_accept_search_and_policy(client):
    preview = client.post("/api/reads/snapshots", json=SNAPSHOT, headers=HEADERS)
    assert preview.status_code == 200
    assert client.get("/api/reads/status").json()["total"] == 0
    accepted = client.post("/api/reads/snapshots?dry_run=false", json=SNAPSHOT, headers=HEADERS)
    assert accepted.status_code == 200
    status = client.get("/api/reads/status").json()
    assert status["total"] == 1
    assert status["captured"] == 0
    document = status["documents"][0]
    assert document["cloud_allowed"] == 0
    result = client.post("/api/reads/search", json={"query": "Latency"}, headers=HEADERS).json()
    assert result["results"][0]["category"] == "metadata-only"
    assert result["results"][0]["excerpt"] is None
    assert "diagnostics" not in result
    assert client.patch(f'/api/reads/documents/{document["id"]}', json={"note": "My note", "cloud_allowed": False}, headers=HEADERS).status_code == 200
    assert client.get(f'/api/reads/documents/{document["id"]}').json()["note"] == "My note"


def test_mutations_reject_cross_origin_and_unmarked_requests(client):
    assert client.post("/api/reads/snapshots", json=SNAPSHOT).status_code == 403
    assert client.post("/api/reads/snapshots", json=SNAPSHOT, headers=HEADERS | {"Origin": "https://evil.example"}).status_code == 403
    assert client.post("/api/reads/search", json={"query": "x"}, headers=HEADERS | {"Origin": "https://evil.example"}).status_code == 403


def test_incomplete_sync_and_unknown_documents_are_visible_failures(client):
    assert client.post("/api/reads/snapshots?dry_run=false", json=SNAPSHOT | {"complete": False}, headers=HEADERS).status_code == 409
    assert client.post("/api/reads/capture", json={"document": "missing"}, headers=HEADERS).status_code == 404
    assert client.get("/api/reads/documents/missing").status_code == 404