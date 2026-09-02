"""Environment-backed defaults owned by the meeting application."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .storage import default_data_dir


@dataclass(frozen=True)
class AppConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    data_dir: Path = field(default_factory=default_data_dir)
    stt_model: str = "mlx-community/whisper-small-mlx"
    ollama_model: str = "qwen3:4b"
    ollama_url: str = "http://localhost:11434"
    azure_model: str | None = None
    suggestion_interval_minutes: float = 5

    @classmethod
    def from_env(cls) -> AppConfig:
        return cls(
            port=int(os.getenv("MEETING_ASSISTANT_PORT", "8765")),
            data_dir=Path(
                os.getenv("MEETING_ASSISTANT_DATA_DIR", str(default_data_dir()))
            ).expanduser(),
            stt_model=os.getenv(
                "MEETING_ASSISTANT_STT_MODEL", "mlx-community/whisper-small-mlx"
            ),
            ollama_model=os.getenv("MEETING_ASSISTANT_OLLAMA_MODEL", "qwen3:4b"),
            ollama_url=os.getenv(
                "MEETING_ASSISTANT_OLLAMA_URL", "http://localhost:11434"
            ),
            azure_model=os.getenv("AB_AZURE_OPENAI_DEPLOYMENT") or None,
            suggestion_interval_minutes=float(
                os.getenv("MEETING_ASSISTANT_SUGGESTION_INTERVAL_MINUTES", "5")
            ),
        )
