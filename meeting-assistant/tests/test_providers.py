import sys
from types import ModuleType

from meeting_assistant.providers import OllamaProvider


def test_ollama_adapter_uses_shared_client_and_disables_thinking(monkeypatch):
    calls = []

    class FakeClient:
        def __init__(self, model, base_url):
            assert model == "qwen3:4b"
            assert base_url == "http://localhost:11434"

        def generate(self, prompt, **options):
            calls.append((prompt, options))
            return "{}"

    ab_module = ModuleType("ab")
    ab_module.__path__ = []
    core_module = ModuleType("ab.core")
    core_module.__path__ = []
    client_module = ModuleType("ab.core.ollama_client")
    client_module.OllamaClient = FakeClient
    monkeypatch.setitem(sys.modules, "ab", ab_module)
    monkeypatch.setitem(sys.modules, "ab.core", core_module)
    monkeypatch.setitem(sys.modules, "ab.core.ollama_client", client_module)
    provider = OllamaProvider()

    assert provider.generate("prompt") == "{}"
    assert calls == [
        (
            "prompt",
            {
                "temperature": 0.1,
                "max_tokens": 1800,
                "timeout": 120,
                "think": False,
            },
        )
    ]
