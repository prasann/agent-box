from __future__ import annotations

import json
import stat
from datetime import datetime, timezone

from conftest import segment

from meeting_assistant.models import MeetingMetadata
from meeting_assistant.storage import MeetingStore


def metadata() -> MeetingMetadata:
    return MeetingMetadata(
        session_id="abc123",
        started_at=datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
        meeting_device_id=4,
        microphone_device_id=2,
        app_version="0.1.0",
        stt_model="fake-whisper",
        suggestions_enabled=False,
        llm_provider=None,
        llm_model=None,
        suggestion_interval_minutes=5,
    )


def test_storage_creates_durable_canonical_files_and_markdown(tmp_path):
    store = MeetingStore(tmp_path)
    directory = store.start(metadata())
    store.append_segment(segment(1))

    lines = (directory / "transcript.jsonl").read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["stream"] == "Meeting"
    assert not (directory / "suggestions.jsonl").exists()
    assert list(directory.glob(".metadata.json.*")) == []

    store.stop()

    saved_metadata = json.loads((directory / "metadata.json").read_text())
    assert saved_metadata["ended_at"] is not None
    assert "**10:00:01 · Meeting**" in (directory / "transcript.md").read_text()
    assert stat.S_IMODE(store.root.stat().st_mode) == 0o700
    assert stat.S_IMODE(store.meetings_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    for filename in ("metadata.json", "transcript.jsonl", "transcript.md"):
        assert stat.S_IMODE((directory / filename).stat().st_mode) == 0o600

    store.append_suggestion_event({"event": "generation"})
    assert stat.S_IMODE((directory / "suggestions.jsonl").stat().st_mode) == 0o600


def test_history_skips_corrupt_directories_but_keeps_valid_sessions(tmp_path):
    store = MeetingStore(tmp_path)
    directory = store.start(metadata())
    (store.meetings_dir / "broken").mkdir()
    (store.meetings_dir / "broken" / "metadata.json").write_text("{")

    meetings = store.list_meetings()

    assert [item["directory"] for item in meetings] == [directory.name]
