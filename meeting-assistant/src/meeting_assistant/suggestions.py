"""Incremental suggestion generation and cadence control."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from typing import Any

from .models import Suggestion, SuggestionResult, TranscriptSegment
from .providers import SuggestionProvider, clean_json_response

SYSTEM_RULES = """You are a private real-time meeting question assistant.
Return JSON only with meeting_state and suggestions. Each suggestion must include:
suggestion_id, text, type, rationale, confidence, supporting_segment_ids,
supporting_timestamps, and a stable fingerprint.
Allowed types: clarification, assumption/risk, missing evidence, decision check,
constructive follow-up.
Suppress duplicates and questions that are answered, stale, unsupported, or generic.
Prefer a few concrete, useful prompts over filling a quota. Do not include markdown."""


class SuggestionCoordinator:
    def __init__(
        self,
        provider: SuggestionProvider | None,
        interval_minutes: float = 5,
        enabled: bool = False,
        event_sink: Callable[[dict[str, Any]], None] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.provider = provider
        self.interval_seconds = interval_minutes * 60
        self.enabled = enabled
        self.event_sink = event_sink
        self.clock = clock
        self.next_due = clock() + self.interval_seconds
        self.segments: list[TranscriptSegment] = []
        self.last_call_index = 0
        self.meeting_state = ""
        self.fingerprints: set[str] = set()
        self.failure_count = 0
        self._lock = threading.RLock()

    def add_segment(self, segment: TranscriptSegment) -> None:
        with self._lock:
            self.segments.append(segment)

    def configure(
        self,
        *,
        enabled: bool | None = None,
        interval_minutes: float | None = None,
    ) -> None:
        with self._lock:
            if enabled is not None:
                self.enabled = enabled
            if interval_minutes is not None:
                self.interval_seconds = interval_minutes * 60
                self.next_due = self.clock() + self.interval_seconds

    def tick(self, *, manual: bool = False, now: float | None = None) -> list[Suggestion]:
        current = self.clock() if now is None else now
        with self._lock:
            if not self.enabled:
                return []
            if self.provider is None:
                raise RuntimeError("Suggestions require a configured Ollama or Azure provider.")
            if not manual and current < self.next_due:
                return []
            if self.last_call_index >= len(self.segments):
                if not manual:
                    self.next_due = current + self.interval_seconds
                return []
            if not manual:
                self.next_due = current + self.interval_seconds
            provider = self.provider
            end_index = len(self.segments)
            overlap_start = max(0, self.last_call_index - 2)
            window = list(self.segments[overlap_start:end_index])
            prompt = self._prompt(window)

        try:
            raw = provider.generate(prompt)
            parsed_output = json.loads(clean_json_response(raw))
            result = SuggestionResult.model_validate(parsed_output)
        except Exception:
            if not manual:
                with self._lock:
                    self.failure_count += 1
                    maximum = max(60.0, self.interval_seconds * 4)
                    delay = min(
                        self.interval_seconds * (2**self.failure_count), maximum
                    )
                    self.next_due = self.clock() + delay
            raise

        with self._lock:
            self.failure_count = 0
            accepted = [
                suggestion
                for suggestion in result.suggestions
                if suggestion.fingerprint not in self.fingerprints
                and suggestion.supporting_segment_ids
            ]
            self.fingerprints.update(item.fingerprint for item in accepted)
            self.meeting_state = result.meeting_state
            self.last_call_index = max(self.last_call_index, end_index)
            event_sink = self.event_sink
        if event_sink is not None:
            event_sink(
                {
                    "event": "generation",
                    "provider": provider.name,
                    "model": provider.model,
                    "manual": manual,
                    "input_segment_ids": [segment.segment_id for segment in window],
                    "original_output": parsed_output,
                    "accepted_suggestion_ids": [item.suggestion_id for item in accepted],
                }
            )
        return accepted

    def _prompt(self, window: list[TranscriptSegment]) -> str:
        transcript = "\n".join(
            f"[{segment.start_timestamp.isoformat()}] {segment.stream.value} "
            f"({segment.segment_id}): {segment.text}"
            for segment in window
        )
        return (
            f"{SYSTEM_RULES}\n\nPrior compact meeting state:\n"
            f"{self.meeting_state or '(none yet)'}\n\n"
            f"New transcript with small overlap:\n{transcript}"
        )
