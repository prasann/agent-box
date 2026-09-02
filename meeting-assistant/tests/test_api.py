from __future__ import annotations

import pytest
import threading
import time
from starlette.websockets import WebSocketDisconnect
from fastapi.testclient import TestClient
from test_runtime import FakeCapture, FakeTranscriber

from meeting_assistant.api import create_app
from meeting_assistant.models import Provenance, TranscriptSegment, utc_now
from meeting_assistant.runtime import MeetingManager

TOKEN = "test-access-token"
AUTH = {"X-Meeting-Token": TOKEN}


def test_api_status_history_and_websocket(tmp_path):
    manager = MeetingManager(
        data_dir=tmp_path,
        capture=FakeCapture(),
        transcriber_factory=lambda model: FakeTranscriber(),
    )
    with TestClient(
        create_app(manager, access_token=TOKEN), base_url="http://127.0.0.1"
    ) as client:
        assert client.get("/api/health").status_code == 403
        assert (
            client.get(
                "/api/health", headers={**AUTH, "Origin": "https://attacker.example"}
            ).status_code
            == 403
        )
        assert client.get("/api/health", headers=AUTH).json()["host"] == "127.0.0.1"
        assert client.get("/api/status", headers=AUTH).json()["recording"] is False
        assert client.get("/api/meetings", headers=AUTH).json() == {"meetings": []}
        assert client.get("/").status_code == 403
        assert "Meeting Assistant" in client.get(f"/?token={TOKEN}").text
        with client.websocket_connect(
            f"/ws?token={TOKEN}",
            headers={"Host": "127.0.0.1", "Origin": "http://127.0.0.1"},
        ) as websocket:
            event = websocket.receive_json()
            assert event["type"] == "status"
            assert event["status"]["recording"] is False
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                f"/ws?token={TOKEN}",
                headers={"Host": "127.0.0.1", "Origin": "https://attacker.example"},
            ) as websocket:
                websocket.receive_json()


def test_api_transcript_only_session_lifecycle(tmp_path):
    manager = MeetingManager(
        data_dir=tmp_path,
        capture=FakeCapture(),
        transcriber_factory=lambda model: FakeTranscriber(),
    )
    payload = {
        "meeting_device_id": 3,
        "microphone_device_id": 4,
        "suggestions_enabled": False,
    }
    with TestClient(
        create_app(manager, access_token=TOKEN),
        base_url="http://127.0.0.1",
        headers=AUTH,
    ) as client:
        assert client.post("/api/session/start", json=payload).status_code == 200
        assert client.get("/api/status").json()["recording"] is True
        assert client.post("/api/session/stop").json()["recording"] is False
        assert len(client.get("/api/meetings").json()["meetings"]) == 1


def test_azure_config_and_request_do_not_use_ollama_model(tmp_path, monkeypatch):
    monkeypatch.setenv("AB_AZURE_OPENAI_DEPLOYMENT", "configured-azure")
    manager = MeetingManager(
        data_dir=tmp_path,
        capture=FakeCapture(),
        transcriber_factory=lambda model: FakeTranscriber(),
    )
    with TestClient(
        create_app(manager, access_token=TOKEN),
        base_url="http://127.0.0.1",
        headers=AUTH,
    ) as client:
        config = client.get("/api/config").json()
        assert config["ollama_model"] == "qwen3:4b"
        assert config["azure_model"] == "configured-azure"
        ui = client.get(f"/?token={TOKEN}").text
        assert 'azure ? (appConfig.azure_model || "")' in ui
        assert '($("model").value.trim() || null)' in ui

    from meeting_assistant.models import MeetingOptions

    options = MeetingOptions(
        meeting_device_id=1,
        microphone_device_id=2,
        suggestions_enabled=True,
        llm_provider="azure",
    )
    assert options.llm_model is None


def test_shutdown_does_not_wait_for_blocked_scheduled_provider(tmp_path):
    entered = threading.Event()
    release = threading.Event()

    class BlockingProvider:
        name = "ollama"
        model = "qwen3:4b"

        def generate(self, prompt):
            entered.set()
            release.wait(timeout=5)
            return '{"meeting_state":"state","suggestions":[]}'

    manager = MeetingManager(
        data_dir=tmp_path,
        capture=FakeCapture(),
        transcriber_factory=lambda model: FakeTranscriber(),
        provider_factory=lambda name, model: BlockingProvider(),
    )
    shutdown_started = None
    try:
        with TestClient(
            create_app(manager, access_token=TOKEN),
            base_url="http://127.0.0.1",
            headers=AUTH,
        ) as client:
            response = client.post(
                "/api/session/start",
                json={
                    "meeting_device_id": 1,
                    "microphone_device_id": 2,
                    "suggestions_enabled": True,
                    "llm_provider": "ollama",
                    "suggestion_interval_minutes": 0.25,
                },
            )
            assert response.status_code == 200
            manager.coordinator.add_segment(
                TranscriptSegment(
                    segment_id="shutdown-segment",
                    start_timestamp=utc_now(),
                    end_timestamp=utc_now(),
                    stream=Provenance.MEETING,
                    text="A decision is pending.",
                    transcription_model="fake",
                    transcription_backend="fake",
                )
            )
            manager.coordinator.next_due = 0
            assert entered.wait(timeout=2)
            shutdown_started = time.monotonic()
        assert time.monotonic() - shutdown_started < 0.5
    finally:
        release.set()
