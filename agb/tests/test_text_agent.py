"""Tests for text agent."""
import pytest
from ab.agents.text.checker import GrammarChecker
from ab.core import OllamaClient, Settings


def test_grammar_checker_init():
    """Test GrammarChecker initialization."""
    ollama = OllamaClient()
    settings = Settings()
    checker = GrammarChecker(ollama, settings)
    
    assert checker.ollama is not None
    assert checker.settings is not None


# Add more tests here as needed
