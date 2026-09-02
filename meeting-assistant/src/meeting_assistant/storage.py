"""Crash-conscious append-only meeting persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .models import MeetingMetadata, TranscriptSegment, utc_now


def default_data_dir() -> Path:
    configured = os.getenv("MEETING_ASSISTANT_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".local" / "share" / "meeting-assistant"


class MeetingStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or default_data_dir()
        self.meetings_dir = self.root / "meetings"
        self.meetings_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        os.chmod(self.meetings_dir, 0o700)
        self.session_dir: Path | None = None
        self.metadata: MeetingMetadata | None = None

    def start(self, metadata: MeetingMetadata) -> Path:
        stamp = metadata.started_at.astimezone().strftime("%Y%m%d-%H%M%S")
        self.session_dir = self.meetings_dir / f"{stamp}-{metadata.session_id}"
        self.session_dir.mkdir(parents=False, exist_ok=False, mode=0o700)
        os.chmod(self.session_dir, 0o700)
        self.metadata = metadata
        self._atomic_json(self.session_dir / "metadata.json", metadata.model_dump(mode="json"))
        self._touch_durable(self.session_dir / "transcript.jsonl")
        return self.session_dir

    def append_segment(self, segment: TranscriptSegment) -> None:
        self._require_session()
        self._append_jsonl(self.session_dir / "transcript.jsonl", segment.model_dump(mode="json"))

    def append_suggestion_event(self, event: dict[str, Any]) -> None:
        self._require_session()
        payload = {"recorded_at": utc_now().isoformat(), **event}
        self._append_jsonl(self.session_dir / "suggestions.jsonl", payload)

    def update_metadata(self, **changes: Any) -> MeetingMetadata:
        self._require_session()
        assert self.metadata is not None
        self.metadata = self.metadata.model_copy(update=changes)
        self._atomic_json(
            self.session_dir / "metadata.json", self.metadata.model_dump(mode="json")
        )
        return self.metadata

    def stop(self) -> None:
        self._require_session()
        self.update_metadata(ended_at=utc_now())
        self.rebuild_markdown()

    def rebuild_markdown(self) -> Path:
        self._require_session()
        assert self.metadata is not None
        lines = [
            f"# Meeting {self.metadata.started_at.astimezone().strftime('%Y-%m-%d %H:%M')}",
            "",
        ]
        for item in self.read_jsonl(self.session_dir / "transcript.jsonl"):
            when = str(item["start_timestamp"])[11:19]
            lines.extend([f"**{when} · {item['stream']}**", "", item["text"], ""])
        output = self.session_dir / "transcript.md"
        self._atomic_text(output, "\n".join(lines).rstrip() + "\n")
        return output

    def list_meetings(self) -> list[dict[str, Any]]:
        meetings: list[dict[str, Any]] = []
        for directory in sorted(self.meetings_dir.iterdir(), reverse=True):
            metadata_path = directory / "metadata.json"
            if not directory.is_dir() or not metadata_path.exists():
                continue
            try:
                metadata = json.loads(metadata_path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            meetings.append(
                {
                    **metadata,
                    "directory": directory.name,
                    "segment_count": sum(1 for _ in self.read_jsonl(directory / "transcript.jsonl")),
                    "has_suggestions": (directory / "suggestions.jsonl").exists(),
                }
            )
        return meetings

    def read_meeting(self, directory_name: str) -> dict[str, Any]:
        if Path(directory_name).name != directory_name:
            raise ValueError("Invalid meeting directory")
        directory = self.meetings_dir / directory_name
        if not directory.is_dir():
            raise FileNotFoundError(directory_name)
        return {
            "metadata": json.loads((directory / "metadata.json").read_text()),
            "transcript": list(self.read_jsonl(directory / "transcript.jsonl")),
            "suggestion_events": list(self.read_jsonl(directory / "suggestions.jsonl")),
        }

    @staticmethod
    def read_jsonl(path: Path):
        if not path.exists():
            return
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    def _require_session(self) -> None:
        if self.session_dir is None:
            raise RuntimeError("No active meeting store")

    @staticmethod
    def _touch_durable(path: Path) -> None:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        os.chmod(path, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.flush()
            os.fsync(handle.fileno())

    @staticmethod
    def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        os.chmod(path, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    @classmethod
    def _atomic_json(cls, path: Path, value: dict[str, Any]) -> None:
        cls._atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")

    @staticmethod
    def _atomic_text(path: Path, value: str) -> None:
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            os.chmod(path, 0o600)
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
