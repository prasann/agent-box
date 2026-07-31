"""Azure OpenAI client for LLM inference using Entra ID auth (az login)."""
import os
from typing import Optional


class AzureOpenAIClient:
    """Client for Azure OpenAI chat completions.

    Authenticates via Entra ID using DefaultAzureCredential (e.g. an
    existing `az login` session) - no API key needs to be stored on disk.

    Configure via env vars (or agb .env with AB_ prefix):
        AB_AZURE_OPENAI_ENDPOINT    e.g. https://locus-dev.openai.azure.com
        AB_AZURE_OPENAI_DEPLOYMENT  deployment name, default: gpt-4o
        AB_AZURE_OPENAI_API_VERSION default: 2024-10-21
    """

    TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"
    DEFAULT_API_VERSION = "2024-10-21"
    DEFAULT_DEPLOYMENT = "gpt-4o"

    def __init__(self, endpoint: Optional[str] = None, deployment: Optional[str] = None,
                 api_version: Optional[str] = None):
        self.endpoint = (endpoint or os.getenv("AB_AZURE_OPENAI_ENDPOINT", "")).rstrip("/")
        self.deployment = deployment or os.getenv("AB_AZURE_OPENAI_DEPLOYMENT", self.DEFAULT_DEPLOYMENT)
        self.api_version = api_version or os.getenv("AB_AZURE_OPENAI_API_VERSION", self.DEFAULT_API_VERSION)
        self._credential = None

    @property
    def credential(self):
        """Lazily create the credential (avoids probing auth sources unless needed)."""
        if self._credential is None:
            from azure.identity import DefaultAzureCredential
            self._credential = DefaultAzureCredential()
        return self._credential

    def _url(self) -> str:
        return (f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions"
                f"?api-version={self.api_version}")

    def _token(self) -> str:
        return self.credential.get_token(self.TOKEN_SCOPE).token

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

        if not self.endpoint:
            raise RuntimeError(
                "AB_AZURE_OPENAI_ENDPOINT is not set. "
                "Add it to agb/.env, e.g. AB_AZURE_OPENAI_ENDPOINT=https://locus-dev.openai.azure.com"
            )

        response = requests.post(
            self._url(),
            headers={
                "Authorization": f"Bearer {self._token()}",
                "Content-Type": "application/json",
            },
            json={
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
        """Check if the client is configured and Entra ID auth succeeds."""
        try:
            if not self.endpoint:
                return False
            self._token()
            return True
        except Exception:
            return False
