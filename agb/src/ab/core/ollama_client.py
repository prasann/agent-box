"""Shared Ollama API client."""
import requests
import json
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential


class OllamaClient:
    """Client for Ollama API - shared across all agents."""
    
    def __init__(self, model: str = "llama3.2:3b", 
                 base_url: str = "http://localhost:11434",
                 embed_model: str = "nomic-embed-text"):
        self.model = model
        self.base_url = base_url
        self.embed_model = embed_model
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """Generate text with retry logic."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        return response.json()["response"]
    
    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.embed_model, "prompt": text},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception:
            return []
    
    def expand_query(self, query: str) -> dict:
        """Expand query into keywords and intent using LLM."""
        prompt = f"""Extract key search terms (3-5 words) and intent from this query.

Query: "{query}"

Respond in JSON:
{{"keywords": ["word1", "word2"], "intent": "what they're looking for"}}"""
        
        try:
            result = self.generate(prompt, temperature=0.1, max_tokens=100).strip()
            parsed = json.loads(result)
            return {
                "keywords": parsed.get("keywords", [query]),
                "intent": parsed.get("intent", query),
                "original": query,
            }
        except (json.JSONDecodeError, Exception):
            return {"keywords": [query], "intent": query, "original": query}
    
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
    
    def has_model(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        try:
            models = self.list_models()
            return any(model_name in m for m in models)
        except:
            return False

