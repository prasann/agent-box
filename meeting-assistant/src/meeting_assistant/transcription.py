"""Replaceable local speech-to-text adapters."""

from __future__ import annotations

from typing import Protocol


class Transcriber(Protocol):
    model: str
    backend: str

    def transcribe(self, samples: list[float], sample_rate: int = 16_000) -> str: ...


class MlxWhisperTranscriber:
    backend = "mlx-whisper"

    def __init__(self, model: str = "mlx-community/whisper-small-mlx") -> None:
        self.model = model

    def transcribe(self, samples: list[float], sample_rate: int = 16_000) -> str:
        if sample_rate != 16_000:
            raise ValueError("MLX Whisper adapter requires 16 kHz audio")
        try:
            import mlx_whisper
            import numpy
        except ImportError as error:
            raise RuntimeError(
                "Local transcription is unavailable. Install with "
                "`uv sync --project meeting-assistant --extra audio --extra stt`."
            ) from error
        result = mlx_whisper.transcribe(
            numpy.asarray(samples, dtype=numpy.float32),
            path_or_hf_repo=self.model,
            language=None,
            fp16=True,
        )
        return str(result.get("text", "")).strip()

