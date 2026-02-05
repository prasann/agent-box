"""Tests for core Ollama client."""
import pytest
from ab.core import OllamaClient


def test_ollama_client_init():
    """Test OllamaClient initialization."""
    ollama = OllamaClient()
    
    assert ollama.model == "llama3.2:3b"
    assert ollama.base_url == "http://localhost:11434"


def test_ollama_client_custom_model():
    """Test OllamaClient with custom model."""
    ollama = OllamaClient(model="mistral")
    
    assert ollama.model == "mistral"


# Add more tests here as needed
