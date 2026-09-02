"""Domain models shared by capture, persistence, suggestions, and API layers."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import os
from typing import Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Provenance(str, Enum):
    ME = "Me"
    MEETING = "Meeting"


class TranscriptSegment(BaseModel):
    segment_id: str
    start_timestamp: datetime
    end_timestamp: datetime
    stream: Provenance
    text: str
    transcription_model: str
    transcription_backend: str


class Suggestion(BaseModel):
    suggestion_id: str
    text: str
    type: Literal[
        "clarification",
        "assumption/risk",
        "missing evidence",
        "decision check",
        "constructive follow-up",
    ]
    rationale: str
    confidence: float = Field(ge=0, le=1)
    supporting_segment_ids: list[str]
    supporting_timestamps: list[str]
    fingerprint: str


class SuggestionResult(BaseModel):
    meeting_state: str = Field(max_length=4000)
    suggestions: list[Suggestion]


class MeetingOptions(BaseModel):
    meeting_device_id: int | str
    microphone_device_id: int | str
    stt_model: str = Field(
        default_factory=lambda: os.getenv(
            "MEETING_ASSISTANT_STT_MODEL", "mlx-community/whisper-small-mlx"
        )
    )
    suggestions_enabled: bool = False
    llm_provider: Literal["ollama", "azure"] | None = None
    llm_model: str | None = None
    suggestion_interval_minutes: float = Field(
        default_factory=lambda: float(
            os.getenv("MEETING_ASSISTANT_SUGGESTION_INTERVAL_MINUTES", "5")
        ),
        ge=0.25,
        le=60,
    )


class MeetingMetadata(BaseModel):
    session_id: str
    started_at: datetime
    ended_at: datetime | None = None
    meeting_device_id: int | str
    microphone_device_id: int | str
    app_version: str
    config_version: str = "1"
    stt_model: str
    suggestions_enabled: bool
    llm_provider: str | None
    llm_model: str | None
    suggestion_interval_minutes: float
    prompt_version: str = "1"
    schema_version: str = "1"


class SuggestionAction(BaseModel):
    action: Literal["edit", "copy", "dismiss", "mark-used"]
    text: str | None = None
