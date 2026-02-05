"""Simple Ollama API client."""
import requests


class OllamaClient:
    """Minimal Ollama client - no retries, no fancy features."""
    
    def __init__(self, model: str = "qwen3:1.7b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text using Ollama."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Cannot connect to Ollama. Is it running? Try: ollama serve")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")
