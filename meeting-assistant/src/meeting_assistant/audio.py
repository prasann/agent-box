"""Separate-stream audio capture, resampling, VAD, and chunking."""

from __future__ import annotations

import math
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Protocol

from .models import Provenance

TARGET_SAMPLE_RATE = 16_000


@dataclass(frozen=True)
class AudioDevice:
    id: int
    name: str
    input_channels: int
    default_sample_rate: float

    def to_dict(self) -> dict:
        return asdict(self)


class AudioCapture(Protocol):
    def list_devices(self) -> list[AudioDevice]: ...

    def start(
        self,
        meeting_device_id: int | str,
        microphone_device_id: int | str,
        on_chunk: Callable[[Provenance, list[float]], None],
        on_error: Callable[[str], None],
    ) -> None: ...

    def stop(self) -> None: ...


class VoiceChunker:
    def __init__(
        self,
        sample_rate: int = TARGET_SAMPLE_RATE,
        energy_threshold: float = 0.008,
        silence_seconds: float = 0.7,
        minimum_seconds: float = 0.6,
        maximum_seconds: float = 20,
    ) -> None:
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_samples = int(silence_seconds * sample_rate)
        self.minimum_samples = int(minimum_seconds * sample_rate)
        self.maximum_samples = int(maximum_seconds * sample_rate)
        self.buffer: list[float] = []
        self.silent_samples = 0
        self.active = False

    def push(self, samples: list[float]) -> list[list[float]]:
        if not samples:
            return []
        rms = math.sqrt(sum(value * value for value in samples) / len(samples))
        speech = rms >= self.energy_threshold
        if speech:
            self.active = True
            self.silent_samples = 0
        elif self.active:
            self.silent_samples += len(samples)
        if self.active:
            self.buffer.extend(samples)
        should_flush = (
            len(self.buffer) >= self.maximum_samples
            or self.silent_samples >= self.silence_samples
        )
        if not should_flush:
            return []
        chunk = self.buffer
        self.buffer = []
        self.silent_samples = 0
        self.active = False
        return [chunk] if len(chunk) >= self.minimum_samples else []

    def flush(self) -> list[list[float]]:
        chunk = self.buffer
        self.buffer = []
        self.silent_samples = 0
        self.active = False
        return [chunk] if len(chunk) >= self.minimum_samples else []


def resample_mono(samples: list[float], source_rate: float) -> list[float]:
    if int(source_rate) == TARGET_SAMPLE_RATE:
        return samples
    if not samples or source_rate <= 0:
        return []
    output_length = max(1, round(len(samples) * TARGET_SAMPLE_RATE / source_rate))
    scale = (len(samples) - 1) / max(1, output_length - 1)
    output: list[float] = []
    for index in range(output_length):
        position = index * scale
        left = int(position)
        right = min(left + 1, len(samples) - 1)
        fraction = position - left
        output.append(samples[left] * (1 - fraction) + samples[right] * fraction)
    return output


class SoundDeviceCapture:
    def __init__(self) -> None:
        self._streams: list[object] = []
        self._chunkers = {
            Provenance.MEETING: VoiceChunker(),
            Provenance.ME: VoiceChunker(),
        }
        self._lock = threading.Lock()
        self._on_chunk: Callable[[Provenance, list[float]], None] | None = None

    def _sounddevice(self):
        try:
            import sounddevice
        except ImportError as error:
            raise RuntimeError(
                "Audio capture is unavailable. Install PortAudio (`brew install portaudio`) "
                "then `uv sync --project meeting-assistant --extra audio`."
            ) from error
        return sounddevice

    def list_devices(self) -> list[AudioDevice]:
        sounddevice = self._sounddevice()
        return [
            AudioDevice(
                id=index,
                name=str(item["name"]),
                input_channels=int(item["max_input_channels"]),
                default_sample_rate=float(item["default_samplerate"]),
            )
            for index, item in enumerate(sounddevice.query_devices())
            if int(item["max_input_channels"]) > 0
        ]

    def start(
        self,
        meeting_device_id: int | str,
        microphone_device_id: int | str,
        on_chunk: Callable[[Provenance, list[float]], None],
        on_error: Callable[[str], None],
    ) -> None:
        sounddevice = self._sounddevice()
        self._on_chunk = on_chunk
        try:
            for provenance, device in (
                (Provenance.MEETING, meeting_device_id),
                (Provenance.ME, microphone_device_id),
            ):
                info = sounddevice.query_devices(device, "input")
                source_rate = float(info["default_samplerate"])

                def callback(
                    indata,
                    frames,
                    time_info,
                    status,
                    *,
                    source=provenance,
                    rate=source_rate,
                ):
                    if status:
                        on_error(f"{source.value} audio: {status}")
                    mono = indata.mean(axis=1).tolist()
                    chunks = self._chunkers[source].push(resample_mono(mono, rate))
                    for chunk in chunks:
                        if self._on_chunk is not None:
                            self._on_chunk(source, chunk)

                stream = sounddevice.InputStream(
                    device=device,
                    channels=min(2, int(info["max_input_channels"])),
                    samplerate=source_rate,
                    callback=callback,
                    blocksize=max(256, int(source_rate * 0.1)),
                )
                self._streams.append(stream)
                stream.start()
        except Exception as start_error:
            try:
                self.stop()
            except RuntimeError as cleanup_error:
                raise RuntimeError(
                    f"Audio start failed: {start_error}; cleanup also failed: {cleanup_error}"
                ) from start_error
            raise

    def stop(self) -> None:
        errors: list[str] = []
        try:
            for index, stream in enumerate(self._streams):
                try:
                    stream.stop()
                except Exception as error:  # noqa: BLE001 - continue cleaning other streams
                    errors.append(f"stream {index} stop failed: {error}")
                try:
                    stream.close()
                except Exception as error:  # noqa: BLE001 - continue cleaning other streams
                    errors.append(f"stream {index} close failed: {error}")
        finally:
            self._streams.clear()
            callback = self._on_chunk
            self._on_chunk = None
            if callback is not None:
                for provenance, chunker in self._chunkers.items():
                    for chunk in chunker.flush():
                        try:
                            callback(provenance, chunk)
                        except Exception as error:  # noqa: BLE001 - flush every provenance
                            errors.append(f"{provenance.value} tail flush failed: {error}")
        if errors:
            raise RuntimeError("; ".join(errors))
