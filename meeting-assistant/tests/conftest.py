from __future__ import annotations

from datetime import datetime, timezone

from meeting_assistant.models import Provenance, TranscriptSegment


def segment(number: int, text: str = "We need to decide the launch date.") -> TranscriptSegment:
    return TranscriptSegment(
        segment_id=f"segment-{number}",
        start_timestamp=datetime(2026, 9, 2, 10, 0, number, tzinfo=timezone.utc),
        end_timestamp=datetime(2026, 9, 2, 10, 0, number + 1, tzinfo=timezone.utc),
        stream=Provenance.MEETING,
        text=text,
        transcription_model="fake-whisper",
        transcription_backend="fake",
    )

