"""Azure OpenAI client for LLM inference using Entra ID auth."""

from __future__ import annotations

import os


class AzureOpenAIClient:
    """Client for Azure OpenAI chat completions using DefaultAzureCredential."""

    TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"
    DEFAULT_API_VERSION = "2024-10-21"
    DEFAULT_DEPLOYMENT = "gpt-4o"

    def __init__(
        self,
        endpoint: str | None = None,
        deployment: str | None = None,
        api_version: str | None = None,
    ):
        self.endpoint = (
            endpoint or os.getenv("AB_AZURE_OPENAI_ENDPOINT", "")
        ).rstrip("/")
        self.deployment = deployment or os.getenv(
            "AB_AZURE_OPENAI_DEPLOYMENT", self.DEFAULT_DEPLOYMENT
        )
        self.api_version = api_version or os.getenv(
            "AB_AZURE_OPENAI_API_VERSION", self.DEFAULT_API_VERSION
        )
        self._credential = None

    @property
    def credential(self):
        """Create the credential lazily so transcript-only mode never probes auth."""
        if self._credential is None:
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
        return self._credential

    def _url(self) -> str:
        return (
            f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions"
            f"?api-version={self.api_version}"
        )

    def _token(self) -> str:
        return self.credential.get_token(self.TOKEN_SCOPE).token

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> str:
        """Send a chat completion request with a fresh Entra bearer token."""
        import requests

        if not self.endpoint:
            raise RuntimeError(
                "AB_AZURE_OPENAI_ENDPOINT is not set. Add it to ~/.agb/.env, "
                "for example AB_AZURE_OPENAI_ENDPOINT=https://RESOURCE.openai.azure.com"
            )

        response = requests.post(
            self._url(),
            headers={
                "Authorization": "Bearer " + self._token(),
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
        return response.json()["choices"][0]["message"]["content"]

    def generate(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> str:
        return self.chat(
            [{"role": "user", "content": prompt}],
            temperature,
            max_tokens,
        )

    def is_available(self) -> bool:
        try:
            if not self.endpoint:
                return False
            self._token()
            return True
        except Exception:
            return False
