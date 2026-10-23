"""Regression checks for the remaining Control Center integrations."""
import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from backend.app import _health, create_app


class ControlCenterTests(unittest.TestCase):
    def test_retired_routes_are_removed(self):
        app = create_app()
        paths = {route.path for route in app.routes}
        self.assertIn("/api/text", paths)
        self.assertIn("/api/shell/preview", paths)
        self.assertIn("/api/library", paths)
        self.assertFalse(any("findtab" in path for path in paths))

    def test_registry_contains_only_remaining_agents(self):
        with TemporaryDirectory() as directory:
            app = create_app(library_root=Path(directory))
            endpoint = next(
                route.endpoint for route in app.routes if route.path == "/api/agents"
            )
            with patch("backend.app._health", return_value={
                "services": {"azure": {"status": "healthy"}}
            }):
                agents = asyncio.run(endpoint())
        self.assertEqual({agent["id"] for agent in agents}, {"text", "shell", "library"})

    def test_health_does_not_require_retired_database_settings(self):
        settings = SimpleNamespace(
            azure_openai_endpoint="",
            ollama_url="http://127.0.0.1:11434",
        )
        with patch("backend.app.get_settings", return_value=settings), patch(
            "backend.app.requests.get", return_value=Mock(ok=True)
        ):
            health = _health()
        self.assertEqual(set(health["services"]), {"azure", "ollama"})