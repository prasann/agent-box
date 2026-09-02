"""Runtime orchestration while keeping capture, STT, storage, and LLMs decoupled."""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, wait
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from . import __version__
from .audio import AudioCapture, SoundDeviceCapture
from .models import (
    MeetingMetadata,
    MeetingOptions,
    Provenance,
    SuggestionAction,
    TranscriptSegment,
    utc_now,
)
from .providers import create_provider
from .storage import MeetingStore
from .suggestions import SuggestionCoordinator
from .transcription import MlxWhisperTranscriber, Transcriber

LOGGER = logging.getLogger(__name__)


class MeetingManager:
    def __init__(
        self,
        *,
        data_dir: Path | None = None,
        capture: AudioCapture | None = None,
        transcriber_factory: Callable[[str], Transcriber] | None = None,
        provider_factory: Callable[[str | None, str | None], Any] = create_provider,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.data_dir = data_dir
        self.capture = capture or SoundDeviceCapture()
        self.transcriber_factory = transcriber_factory or MlxWhisperTranscriber
        self.provider_factory = provider_factory
        self.event_sink = event_sink or (lambda event: None)
        self.store: MeetingStore | None = None
        self.transcriber: Transcriber | None = None
        self.coordinator: SuggestionCoordinator | None = None
        self.options: MeetingOptions | None = None
        self.active = False
        self._stopping = False
        self.errors: list[str] = []
        self.segments: list[TranscriptSegment] = []
        self.suggestions: dict[str, dict[str, Any]] = {}
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="meeting-stt")
        self._futures: set[Future] = set()
        self._lock = threading.RLock()
        self._generation_lock = threading.Lock()
        self._submission_sequence = 0
        self._commit_sequence = 0
        self._pending_transcriptions: dict[int, TranscriptSegment | None] = {}

    def list_devices(self) -> list[dict[str, Any]]:
        return [device.to_dict() for device in self.capture.list_devices()]

    def start(self, options: MeetingOptions) -> dict[str, Any]:
        with self._lock:
            if self.active or self._stopping:
                raise RuntimeError("A meeting is already recording or stopping")
            provider = (
                self.provider_factory(options.llm_provider, options.llm_model)
                if options.suggestions_enabled
                else None
            )
            self.options = options
            self.transcriber = self.transcriber_factory(options.stt_model)
            self.store = MeetingStore(self.data_dir)
            session_id = uuid.uuid4().hex[:12]
            metadata = MeetingMetadata(
                session_id=session_id,
                started_at=utc_now(),
                meeting_device_id=options.meeting_device_id,
                microphone_device_id=options.microphone_device_id,
                app_version=__version__,
                stt_model=options.stt_model,
                suggestions_enabled=options.suggestions_enabled,
                llm_provider=options.llm_provider,
                llm_model=options.llm_model
                or (getattr(provider, "model", None) if provider is not None else None),
                suggestion_interval_minutes=options.suggestion_interval_minutes,
            )
            self.store.start(metadata)
            self.coordinator = SuggestionCoordinator(
                provider,
                interval_minutes=options.suggestion_interval_minutes,
                enabled=options.suggestions_enabled,
                event_sink=self.store.append_suggestion_event,
            )
            self.errors.clear()
            self.segments.clear()
            self.suggestions.clear()
            self._submission_sequence = 0
            self._commit_sequence = 0
            self._pending_transcriptions.clear()
            self.active = True
            try:
                self.capture.start(
                    options.meeting_device_id,
                    options.microphone_device_id,
                    self._submit_chunk,
                    self._record_error,
                )
            except Exception:
                self.active = False
                try:
                    self.capture.stop()
                except Exception:  # noqa: BLE001 - preserve the original startup error
                    LOGGER.exception("Failed to clean up partially started audio capture")
                self.store.stop()
                self.store = None
                self.coordinator = None
                raise
        self._emit({"type": "status", "status": self.status()})
        return self.status()

    def stop(self) -> dict[str, Any]:
        with self._lock:
            if not self.active or self._stopping:
                raise RuntimeError("No meeting is recording")
            self._stopping = True
        try:
            try:
                self.capture.stop()
            except Exception as error:  # noqa: BLE001 - still finalize persisted data
                self._record_error(f"Audio shutdown failed: {error}")
            with self._lock:
                self.active = False
                futures = list(self._futures)
            if futures:
                wait(futures)
            with self._lock:
                assert self.store is not None
                self.store.stop()
        finally:
            with self._lock:
                self._stopping = False
        status = self.status()
        self._emit({"type": "status", "status": status})
        return status

    def set_suggestions(
        self, *, enabled: bool | None = None, interval_minutes: float | None = None
    ) -> dict[str, Any]:
        with self._lock:
            if (
                not self.active
                or self.coordinator is None
                or self.options is None
                or self.store is None
            ):
                raise RuntimeError("No active meeting")
            if enabled and self.coordinator.provider is None:
                self.coordinator.provider = self.provider_factory(
                    self.options.llm_provider, self.options.llm_model
                )
                if self.coordinator.provider is None:
                    raise RuntimeError("Select an LLM provider before enabling suggestions")
            self.coordinator.configure(enabled=enabled, interval_minutes=interval_minutes)
            changes: dict[str, Any] = {}
            if enabled is not None:
                changes["suggestions_enabled"] = enabled
                self.options.suggestions_enabled = enabled
            if interval_minutes is not None:
                changes["suggestion_interval_minutes"] = interval_minutes
                self.options.suggestion_interval_minutes = interval_minutes
            self.store.update_metadata(**changes)
            return self.status()

    def generate_suggestions(self, *, manual: bool = True) -> list[dict[str, Any]]:
        with self._generation_lock:
            with self._lock:
                if not self.active or self.coordinator is None:
                    return []
                coordinator = self.coordinator
            try:
                generated = coordinator.tick(manual=manual)
            except Exception as error:  # noqa: BLE001 - provider failures must not stop capture
                with self._lock:
                    relevant = self.active and self.coordinator is coordinator
                if relevant:
                    self._record_error(f"Suggestion generation failed: {error}")
                else:
                    LOGGER.error("Discarded suggestion failure after meeting stop: %s", error)
                return []
            with self._lock:
                if not self.active or self.coordinator is not coordinator:
                    return []
                values = []
                for item in generated:
                    value = item.model_dump(mode="json")
                    value["status"] = "active"
                    self.suggestions[item.suggestion_id] = value
                    values.append(value)
        if values:
            self._emit({"type": "suggestions", "suggestions": values})
        return values

    def scheduled_tick(self) -> list[dict[str, Any]]:
        return self.generate_suggestions(manual=False)

    def suggestion_action(self, suggestion_id: str, action: SuggestionAction) -> dict[str, Any]:
        with self._lock:
            if suggestion_id not in self.suggestions or self.store is None:
                raise KeyError(suggestion_id)
            item = self.suggestions[suggestion_id]
            if action.action == "edit" and action.text:
                item["text"] = action.text
            elif action.action != "copy":
                item["status"] = action.action
            self.store.append_suggestion_event(
                {
                    "event": "action",
                    "suggestion_id": suggestion_id,
                    "action": action.action,
                    "text": action.text,
                }
            )
            result = dict(item)
        self._emit({"type": "suggestion-action", "suggestion": result})
        return result

    def status(self) -> dict[str, Any]:
        metadata = self.store.metadata if self.store is not None else None
        return {
            "recording": self.active,
            "stopping": self._stopping,
            "session_id": metadata.session_id if metadata else None,
            "session_directory": (
                self.store.session_dir.name
                if self.store is not None and self.store.session_dir is not None
                else None
            ),
            "started_at": metadata.started_at.isoformat() if metadata else None,
            "segment_count": len(self.segments),
            "suggestion_count": len(self.suggestions),
            "suggestions_enabled": (
                self.coordinator.enabled if self.coordinator is not None else False
            ),
            "suggestion_interval_minutes": (
                self.coordinator.interval_seconds / 60
                if self.coordinator is not None
                else 5
            ),
            "errors": self.errors[-10:],
        }

    def history(self) -> list[dict[str, Any]]:
        return MeetingStore(self.data_dir).list_meetings()

    def meeting(self, directory_name: str) -> dict[str, Any]:
        return MeetingStore(self.data_dir).read_meeting(directory_name)

    def _submit_chunk(self, provenance: Provenance, samples: list[float]) -> None:
        with self._lock:
            if not self.active:
                return
            sequence = self._submission_sequence
            self._submission_sequence += 1
            ended = utc_now()
            started = ended - timedelta(seconds=len(samples) / 16_000)
            future = self._executor.submit(
                self._transcribe_chunk,
                sequence,
                provenance,
                samples,
                started,
                ended,
            )
            self._futures.add(future)
            future.add_done_callback(self._discard_future)

    def _transcribe_chunk(
        self,
        sequence: int,
        provenance: Provenance,
        samples: list[float],
        started: datetime,
        ended: datetime,
    ) -> None:
        segment: TranscriptSegment | None = None
        try:
            assert self.transcriber is not None
            text = self.transcriber.transcribe(samples).strip()
            if not text:
                return
            segment = TranscriptSegment(
                segment_id=uuid.uuid4().hex,
                start_timestamp=started,
                end_timestamp=ended,
                stream=provenance,
                text=text,
                transcription_model=self.transcriber.model,
                transcription_backend=self.transcriber.backend,
            )
        except Exception as error:  # noqa: BLE001 - isolate backend failures from capture
            self._record_error(f"Transcription failed: {error}")
        finally:
            self._complete_transcription(sequence, segment)

    def _complete_transcription(
        self, sequence: int, segment: TranscriptSegment | None
    ) -> None:
        committed: list[TranscriptSegment] = []
        with self._lock:
            self._pending_transcriptions[sequence] = segment
            while self._commit_sequence in self._pending_transcriptions:
                current = self._pending_transcriptions.pop(self._commit_sequence)
                self._commit_sequence += 1
                if current is None or self.store is None or self.coordinator is None:
                    continue
                self.store.append_segment(current)
                self.segments.append(current)
                self.coordinator.add_segment(current)
                committed.append(current)
        for current in committed:
            self._emit(
                {"type": "segment", "segment": current.model_dump(mode="json")}
            )

    def _discard_future(self, future: Future) -> None:
        with self._lock:
            self._futures.discard(future)

    def _record_error(self, message: str) -> None:
        LOGGER.error(message)
        with self._lock:
            self.errors.append(message)
        self._emit({"type": "error", "message": message})

    def _emit(self, event: dict[str, Any]) -> None:
        try:
            self.event_sink(event)
        except Exception:
            LOGGER.exception("Meeting event sink failed")
