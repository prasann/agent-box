"""Tests for the Mission Control API."""

from fastapi.testclient import TestClient

from ab.agents.web.app import create_app


def test_agents_are_registry_driven(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ab.agents.web.app._health",
        lambda: {
            "status": "degraded",
            "services": {
                "azure": {"status": "unavailable"},
                "ollama": {"status": "unavailable"},
                "database": {"status": "unavailable"},
            },
        },
    )
    client = TestClient(create_app(library_root=tmp_path, static_dir=tmp_path / "missing"))

    response = client.get("/api/agents")

    assert response.status_code == 200
    assert [agent["id"] for agent in response.json()] == [
        "text",
        "findtab",
        "library",
        "shell",
    ]


def test_library_catalog_and_reader(tmp_path):
    skill_dir = tmp_path / ".github" / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "README.md").write_text("# Internal documentation\n")
    (skill_dir / "SKILL.md").write_text(
        "---\nname: Demo skill\ndescription: A useful demo\n---\n# Demo\n\nHello.\n"
    )
    client = TestClient(create_app(library_root=tmp_path, static_dir=tmp_path / "missing"))

    catalog = client.get("/api/library")
    item = catalog.json()["items"][0]
    detail = client.get(f"/api/library/{item['id']}")

    assert catalog.status_code == 200
    assert len(catalog.json()["items"]) == 1
    assert item["kind"] == "skills"
    assert detail.status_code == 200
    assert detail.json()["content"].startswith("# Demo")


def test_missing_run_returns_not_found(tmp_path):
    client = TestClient(create_app(library_root=tmp_path, static_dir=tmp_path / "missing"))

    response = client.get("/api/runs/unknown")

    assert response.status_code == 404
