from __future__ import annotations

import threading
import time

from conftest import segment

from meeting_assistant.models import MeetingOptions, Provenance
from meeting_assistant.runtime import MeetingManager


class FakeCapture:
    def __init__(self):
        self.callback = None

    def list_devices(self):
        return []

    def start(self, meeting_device_id, microphone_device_id, on_chunk, on_error):
        self.callback = on_chunk

    def emit(self, provenance, samples):
        self.callback(provenance, samples)

    def stop(self):
        return None


class FakeTranscriber:
    model = "fake-whisper"
    backend = "fake"

    def transcribe(self, samples, sample_rate=16_000):
        return "finalized local transcript"


def test_transcript_only_mode_never_constructs_provider(tmp_path):
    capture = FakeCapture()

    def forbidden_provider(name, model):
        raise AssertionError("provider factory must not run")

    manager = MeetingManager(
        data_dir=tmp_path,
        capture=capture,
        transcriber_factory=lambda model: FakeTranscriber(),
        provider_factory=forbidden_provider,
    )
    manager.start(
        MeetingOptions(
            meeting_device_id=4,
            microphone_device_id=2,
            suggestions_enabled=False,
        )
    )
    capture.emit(Provenance.MEETING, [0.2] * 16_000)
    for _ in range(100):
        if manager.segments:
            break
        time.sleep(0.01)
    status = manager.stop()

    assert status["segment_count"] == 1
    assert manager.store is not None
    assert not (manager.store.session_dir / "suggestions.jsonl").exists()
    assert (manager.store.session_dir / "transcript.md").exists()


def test_new_session_cannot_start_while_previous_transcription_is_finalizing(tmp_path):
    capture = FakeCapture()
    transcribing = threading.Event()
    release = threading.Event()

    class SlowTranscriber(FakeTranscriber):
        def transcribe(self, samples, sample_rate=16_000):
            transcribing.set()
            release.wait(timeout=2)
            return "old meeting transcript"

    manager = MeetingManager(
        data_dir=tmp_path,
        capture=capture,
        transcriber_factory=lambda model: SlowTranscriber(),
    )
    options = MeetingOptions(meeting_device_id=4, microphone_device_id=2)
    manager.start(options)
    old_directory = manager.store.session_dir
    capture.emit(Provenance.MEETING, [0.2] * 16_000)
    assert transcribing.wait(timeout=1)

    stop_thread = threading.Thread(target=manager.stop)
    stop_thread.start()
    for _ in range(100):
        if manager.status()["stopping"]:
            break
        time.sleep(0.01)

    try:
        manager.start(options)
    except RuntimeError as error:
        assert "stopping" in str(error)
    else:
        raise AssertionError("start must be rejected while the prior meeting is stopping")

    release.set()
    stop_thread.join(timeout=2)
    assert not stop_thread.is_alive()
    assert (old_directory / "transcript.md").exists()
    assert "old meeting transcript" in (old_directory / "transcript.md").read_text()


def test_stop_persists_audio_tail_flushed_by_capture(tmp_path):
    class TailCapture(FakeCapture):
        def stop(self):
            self.callback(Provenance.ME, [0.2] * 16_000)

    manager = MeetingManager(
        data_dir=tmp_path,
        capture=TailCapture(),
        transcriber_factory=lambda model: FakeTranscriber(),
    )
    manager.start(MeetingOptions(meeting_device_id=4, microphone_device_id=2))

    status = manager.stop()

    assert status["segment_count"] == 1
    assert manager.segments[0].stream is Provenance.ME
    assert "finalized local transcript" in (
        manager.store.session_dir / "transcript.md"
    ).read_text()


def test_stop_does_not_wait_for_slow_provider_generation(tmp_path):
    entered = threading.Event()
    release = threading.Event()

    class SlowProvider:
        name = "ollama"
        model = "qwen3:4b"

        def generate(self, prompt):
            entered.set()
            release.wait(timeout=2)
            return (
                '{"meeting_state":"state","suggestions":[]}'
            )

    manager = MeetingManager(
        data_dir=tmp_path,
        capture=FakeCapture(),
        transcriber_factory=lambda model: FakeTranscriber(),
        provider_factory=lambda name, model: SlowProvider(),
    )
    manager.start(
        MeetingOptions(
            meeting_device_id=4,
            microphone_device_id=2,
            suggestions_enabled=True,
            llm_provider="ollama",
        )
    )
    manager.coordinator.add_segment(segment(1))
    generation = threading.Thread(target=manager.generate_suggestions)
    generation.start()
    assert entered.wait(timeout=1)

    started = time.monotonic()
    manager.stop()
    elapsed = time.monotonic() - started

    assert elapsed < 0.5
    assert generation.is_alive()
    release.set()
    generation.join(timeout=2)
    assert not generation.is_alive()
    assert manager.suggestions == {}


def test_transcriptions_commit_in_submission_order(tmp_path):
    first_release = threading.Event()
    second_finished = threading.Event()

    class OutOfOrderTranscriber(FakeTranscriber):
        def transcribe(self, samples, sample_rate=16_000):
            if samples[0] == 0.1:
                first_release.wait(timeout=2)
                return "first"
            second_finished.set()
            return "second"

    capture = FakeCapture()
    manager = MeetingManager(
        data_dir=tmp_path,
        capture=capture,
        transcriber_factory=lambda model: OutOfOrderTranscriber(),
    )
    manager.start(MeetingOptions(meeting_device_id=4, microphone_device_id=2))
    capture.emit(Provenance.MEETING, [0.1] * 8_000)
    capture.emit(Provenance.ME, [0.2] * 8_000)
    assert second_finished.wait(timeout=1)
    assert manager.segments == []

    first_release.set()
    manager.stop()

    assert [item.text for item in manager.segments] == ["first", "second"]


def test_failed_transcription_does_not_stall_later_commits(tmp_path):
    first_release = threading.Event()
    second_finished = threading.Event()

    class FirstFailsTranscriber(FakeTranscriber):
        def transcribe(self, samples, sample_rate=16_000):
            if samples[0] == 0.1:
                first_release.wait(timeout=2)
                raise RuntimeError("bad chunk")
            second_finished.set()
            return "survives"

    capture = FakeCapture()
    manager = MeetingManager(
        data_dir=tmp_path,
        capture=capture,
        transcriber_factory=lambda model: FirstFailsTranscriber(),
    )
    manager.start(MeetingOptions(meeting_device_id=4, microphone_device_id=2))
    capture.emit(Provenance.MEETING, [0.1] * 8_000)
    capture.emit(Provenance.ME, [0.2] * 8_000)
    assert second_finished.wait(timeout=1)
    first_release.set()
    manager.stop()

    assert [item.text for item in manager.segments] == ["survives"]
