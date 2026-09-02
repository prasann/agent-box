from __future__ import annotations

import json

import pytest
from conftest import segment

from meeting_assistant.suggestions import SuggestionCoordinator


class FakeProvider:
    name = "ollama"
    model = "qwen3:4b"

    def __init__(self):
        self.calls = []

    def generate(self, prompt: str) -> str:
        self.calls.append(prompt)
        return json.dumps(
            {
                "meeting_state": "Launch timing is undecided.",
                "suggestions": [
                    {
                        "suggestion_id": f"s-{len(self.calls)}",
                        "text": "What evidence supports the proposed date?",
                        "type": "missing evidence",
                        "rationale": "No supporting data was stated.",
                        "confidence": 0.9,
                        "supporting_segment_ids": ["segment-1"],
                        "supporting_timestamps": ["2026-09-02T10:00:01Z"],
                        "fingerprint": "launch-date-evidence",
                    }
                ],
            }
        )


def test_disabled_and_empty_windows_make_zero_calls():
    provider = FakeProvider()
    coordinator = SuggestionCoordinator(provider, enabled=False, clock=lambda: 0)
    coordinator.add_segment(segment(1))

    assert coordinator.tick(now=999) == []
    coordinator.configure(enabled=True)
    assert coordinator.tick(now=10) == []
    assert provider.calls == []


def test_cadence_manual_skip_and_duplicate_suppression():
    provider = FakeProvider()
    events = []
    coordinator = SuggestionCoordinator(
        provider, enabled=True, interval_minutes=5, event_sink=events.append, clock=lambda: 0
    )
    coordinator.add_segment(segment(1))

    assert coordinator.tick(now=299) == []
    first = coordinator.tick(now=300)
    assert len(first) == 1
    assert coordinator.tick(manual=True, now=301) == []
    assert coordinator.next_due == 600

    coordinator.add_segment(segment(2, "The same launch question remains open."))
    assert coordinator.tick(manual=True, now=302) == []
    assert len(provider.calls) == 2
    assert len(events) == 2
    assert "Prior compact meeting state" in provider.calls[1]
    assert "segment-1" in provider.calls[1]
    assert "segment-2" in provider.calls[1]
    assert coordinator.tick(now=600) == []
    assert coordinator.next_due == 900

    coordinator.configure(enabled=False)
    coordinator.add_segment(segment(3, "A new decision is pending."))
    assert coordinator.tick(now=999) == []
    assert len(provider.calls) == 2


def test_fenced_structured_output_is_parsed():
    provider = FakeProvider()
    original = provider.generate
    provider.generate = lambda prompt: f"```json\n{original(prompt)}\n```"
    coordinator = SuggestionCoordinator(provider, enabled=True, clock=lambda: 0)
    coordinator.add_segment(segment(1))

    assert coordinator.tick(manual=True)[0].fingerprint == "launch-date-evidence"


def test_scheduled_failure_advances_due_time_with_bounded_backoff():
    current_time = [0.0]

    class FailingProvider(FakeProvider):
        def generate(self, prompt: str) -> str:
            self.calls.append(prompt)
            current_time[0] += 500
            raise RuntimeError("provider unavailable")

    provider = FailingProvider()
    coordinator = SuggestionCoordinator(
        provider, enabled=True, interval_minutes=1, clock=lambda: current_time[0]
    )
    coordinator.add_segment(segment(1))

    with pytest.raises(RuntimeError):
        coordinator.tick(now=60)
    assert coordinator.next_due == 620
    assert coordinator.tick(now=619) == []
    assert len(provider.calls) == 1

    with pytest.raises(RuntimeError):
        coordinator.tick(now=620)
    assert coordinator.next_due == 1240
