"""Ollama client for LLM and embedding operations."""
import requests
import json
from typing import Optional
from .models import Settings


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, settings: Settings):
        """Initialize Ollama client.
        
        Args:
            settings: Configuration settings
        """
        self.base_url = settings.ollama_url
        self.model = settings.ollama_model
        self.embed_model = "nomic-embed-text"
    
    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embed_model,
                    "prompt": text,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            print(f"Warning: Failed to generate embedding: {e}")
            return []
    
    def expand_query(self, query: str) -> dict:
        """Expand query into keywords and intent using LLM.
        
        Args:
            query: Natural language query
            
        Returns:
            Dict with keywords, intent, and original query
        """
        prompt = f"""Analyze this search query and extract:
1. Key search terms (3-5 important words)
2. The user's intent (what they're looking for)

Query: "{query}"

Respond in JSON format:
{{
  "keywords": ["word1", "word2", "word3"],
  "intent": "one sentence describing what they want"
}}

JSON:"""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 100,
                    }
                },
                timeout=30,
            )
            response.raise_for_status()
            
            # Extract JSON from response
            result = response.json()["response"].strip()
            
            # Try to parse JSON
            try:
                parsed = json.loads(result)
                return {
                    "keywords": parsed.get("keywords", [query]),
                    "intent": parsed.get("intent", query),
                    "original": query,
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "keywords": [query],
                    "intent": query,
                    "original": query,
                }
        except Exception as e:
            print(f"Warning: Query expansion failed: {e}")
            return {
                "keywords": [query],
                "intent": query,
                "original": query,
            }
    
    def check_availability(self) -> bool:
        """Check if Ollama is available and has required models.
        
        Returns:
            True if available and ready
        """
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Check for embedding model
            has_embed = any(self.embed_model in name for name in model_names)
            if not has_embed:
                print(f"⚠️  Embedding model '{self.embed_model}' not found.")
                print(f"   Run: ollama pull {self.embed_model}")
                return False
            
            # Check for LLM model
            has_llm = any(self.model in name for name in model_names)
            if not has_llm:
                print(f"⚠️  Model '{self.model}' not found.")
                print(f"   Run: ollama pull {self.model}")
                return False
            
            return True
            
        except requests.exceptions.RequestException:
            print("⚠️  Ollama is not running.")
            print("   Start with: ollama serve")
            return False
