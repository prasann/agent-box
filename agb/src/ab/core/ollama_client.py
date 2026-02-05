"""Shared Ollama API client."""
import requests
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential


class OllamaClient:
    """Client for Ollama API - shared across all agents."""
    
    def __init__(self, model: str = "llama3.2:3b", 
                 base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text with retry logic."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        return response.json()["response"]
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=2)
            return True
        except:
            return False
    
    def list_models(self) -> list[str]:
        """List available models."""
        response = requests.get(f"{self.base_url}/api/tags")
        return [m["name"] for m in response.json()["models"]]
