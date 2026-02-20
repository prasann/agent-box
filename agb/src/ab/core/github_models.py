"""GitHub Models API client for LLM inference."""
import os
import subprocess
from typing import Optional


class GitHubModelsClient:
    """Client for GitHub Models API (Azure-hosted).
    
    Uses your GitHub token (via gh auth) for authentication.
    Set GITHUB_MODEL env var to change model (default: gpt-4o).
    """
    
    API_URL = "https://models.inference.ai.azure.com/chat/completions"
    DEFAULT_MODEL = "gpt-4o"
    
    def __init__(self, model: Optional[str] = None):
        """Initialize client.
        
        Args:
            model: Model to use. Defaults to GITHUB_MODEL env var or gpt-4o.
        """
        self.model = model or os.getenv("GITHUB_MODEL", self.DEFAULT_MODEL)
        self._token: Optional[str] = None
    
    @property
    def token(self) -> str:
        """Get GitHub token from gh CLI."""
        if self._token is None:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("Failed to get GitHub token. Run 'gh auth login' first.")
            self._token = result.stdout.strip()
        return self._token
    
    def chat(self, messages: list[dict], temperature: float = 0.1, 
             max_tokens: int = 1000) -> str:
        """Send chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            
        Returns:
            Assistant's response text
        """
        import requests
        
        response = requests.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        
        response.raise_for_status()
        data = response.json()
        
        return data["choices"][0]["message"]["content"]
    
    def generate(self, prompt: str, temperature: float = 0.1, 
                 max_tokens: int = 1000) -> str:
        """Simple generate interface (wraps chat).
        
        Args:
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, temperature, max_tokens)
    
    def is_available(self) -> bool:
        """Check if API is accessible."""
        try:
            _ = self.token
            return True
        except Exception:
            return False
