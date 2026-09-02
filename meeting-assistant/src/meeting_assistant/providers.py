"""App-local adapters over Agent Box provider clients."""

from __future__ import annotations

import json
import os
from typing import Protocol


class SuggestionProvider(Protocol):
    name: str
    model: str

    def generate(self, prompt: str) -> str: ...


class OllamaProvider:
    name = "ollama"

    def __init__(self, model: str = "qwen3:4b", base_url: str | None = None):
        try:
            from ab.core.ollama_client import OllamaClient
        except ImportError as error:
            raise RuntimeError(
                "Agent Box provider support is not installed. Run this app through "
                "the repository install: `uv sync --project agb`."
            ) from error
        self.model = model
        self._client = OllamaClient(
            model=model,
            base_url=base_url
            or os.getenv("MEETING_ASSISTANT_OLLAMA_URL", "http://localhost:11434"),
        )

    def generate(self, prompt: str) -> str:
        return self._client.generate(
            prompt,
            temperature=0.1,
            max_tokens=1800,
            timeout=120,
            think=False,
        )


class AzureProvider:
    name = "azure"

    def __init__(self, model: str | None = None):
        try:
            from ab.core.azure_openai_client import AzureOpenAIClient
        except ImportError as error:
            raise RuntimeError(
                "Agent Box provider support is not installed. Run this app through "
                "the repository install: `uv sync --project agb`."
            ) from error
        self._client = AzureOpenAIClient(deployment=model)
        self.model = self._client.deployment

    def generate(self, prompt: str) -> str:
        return self._client.generate(prompt, temperature=0.1, max_tokens=1800)


def clean_json_response(response: str) -> str:
    value = response.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines)
    json.loads(value)
    return value


def create_provider(name: str | None, model: str | None) -> SuggestionProvider | None:
    if name is None:
        return None
    if name == "ollama":
        return OllamaProvider(
            model or os.getenv("MEETING_ASSISTANT_OLLAMA_MODEL", "qwen3:4b")
        )
    if name == "azure":
        return AzureProvider(model)
    raise ValueError(f"Unsupported provider: {name}")
