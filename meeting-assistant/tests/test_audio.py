import pytest

from meeting_assistant.audio import (
    TARGET_SAMPLE_RATE,
    SoundDeviceCapture,
    VoiceChunker,
    resample_mono,
)
from meeting_assistant.models import Provenance


def test_resample_to_16khz_and_preserve_shape():
    values = resample_mono([0.0, 1.0, 0.0, -1.0] * 8_000, 32_000)
    assert len(values) == TARGET_SAMPLE_RATE
    assert max(values) <= 1
    assert min(values) >= -1


def test_voice_chunker_emits_after_silence():
    chunker = VoiceChunker(
        sample_rate=100, silence_seconds=0.2, minimum_seconds=0.2, maximum_seconds=10
    )
    assert chunker.push([0.1] * 30) == []
    emitted = chunker.push([0.0] * 20)
    assert len(emitted) == 1
    assert len(emitted[0]) == 50


def test_stop_cleans_every_stream_and_flushes_tails_after_failure():
    class Stream:
        def __init__(self, fail_stop=False):
            self.fail_stop = fail_stop
            self.stopped = False
            self.closed = False

        def stop(self):
            self.stopped = True
            if self.fail_stop:
                raise RuntimeError("device disappeared")

        def close(self):
            self.closed = True

    failed = Stream(fail_stop=True)
    healthy = Stream()
    capture = SoundDeviceCapture()
    capture._streams = [failed, healthy]
    captured = []
    capture._on_chunk = lambda provenance, chunk: captured.append((provenance, chunk))
    for chunker in capture._chunkers.values():
        chunker.active = True
        chunker.buffer = [0.1] * chunker.minimum_samples

    with pytest.raises(RuntimeError, match="device disappeared"):
        capture.stop()

    assert failed.stopped and failed.closed
    assert healthy.stopped and healthy.closed
    assert capture._streams == []
    assert [item[0] for item in captured] == [Provenance.MEETING, Provenance.ME]


def test_start_failure_closes_allocated_and_previously_started_streams(monkeypatch):
    class Stream:
        def __init__(self, fail_start=False):
            self.fail_start = fail_start
            self.closed = False

        def start(self):
            if self.fail_start:
                raise RuntimeError("start failed")

        def stop(self):
            return None

        def close(self):
            self.closed = True

    streams = [Stream(), Stream(fail_start=True)]

    class SoundDevice:
        def query_devices(self, device, kind):
            return {"default_samplerate": 48_000, "max_input_channels": 1}

        def InputStream(self, **kwargs):
            return streams.pop(0)

    capture = SoundDeviceCapture()
    created = []
    original_input_stream = SoundDevice().InputStream

    class TrackingSoundDevice(SoundDevice):
        def InputStream(self, **kwargs):
            stream = original_input_stream(**kwargs)
            created.append(stream)
            return stream

    monkeypatch.setattr(capture, "_sounddevice", lambda: TrackingSoundDevice())

    with pytest.raises(RuntimeError, match="start failed"):
        capture.start(1, 2, lambda provenance, chunk: None, lambda message: None)

    assert len(created) == 2
    assert all(stream.closed for stream in created)
    assert capture._streams == []
