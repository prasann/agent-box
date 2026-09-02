"""Shared Ollama API client."""

import json

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


class OllamaClient:
    """Client for Ollama API - shared across all agents."""
    
    def __init__(self, model: str = "qwen3:1.7b", 
                 base_url: str = "http://localhost:11434",
                 embed_model: str = "nomic-embed-text"):
        self.model = model
        self.base_url = base_url
        self.embed_model = embed_model
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        timeout: int = 120,
        think: bool | None = None,
    ) -> str:
        """Generate text with retry logic."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }

        if think is not None:
            payload["think"] = think
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                available_models = self.list_models()
                error_msg = f"Model '{self.model}' not found. Available models: {', '.join(available_models)}"
                if not available_models:
                    error_msg += "\nNo models installed. Run 'ollama pull <model>' to install a model."
                raise RuntimeError(error_msg) from e
            raise
    
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
        except (requests.RequestException, KeyError, TypeError, ValueError):
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
        except (
            json.JSONDecodeError,
            requests.RequestException,
            KeyError,
            TypeError,
            ValueError,
        ):
            return {"keywords": [query], "intent": query, "original": query}
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            response.raise_for_status()
            return True
        except requests.RequestException:
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
        except (requests.RequestException, KeyError, TypeError, ValueError):
            return False
