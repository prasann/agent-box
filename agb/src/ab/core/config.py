"""Shared configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Global settings for all agents."""
    
    # Ollama (shared)
    ollama_model: str = "llama3.2:3b"
    ollama_url: str = "http://localhost:11434"
    
    # Gmail agent (future)
    gmail_batch_size: int = 100
    gmail_max_emails_per_run: int = 1000
    gmail_label_name: str = "NeedsReview/Spam"
    gmail_mark_as_read: bool = False
    gmail_credentials_file: Path = Path("data/credentials.json")
    gmail_token_file: Path = Path("data/token.json")
    gmail_state_file: Path = Path("data/processed_emails.json")
    
    # Text agent
    text_show_preview: bool = True
    
    # Find That Tab agent
    findtab_index_path: str = "~/.findtab/index.db"
    findtab_skip_domains: list[str] = [
        "google.com/search",
        "mail.google.com",
        "bing.com",
        "localhost",
        "127.0.0.1",
        "chrome://",
        "about:",
    ]
    
    # Logging
    log_level: str = "INFO"
    log_file: Path = Path("data/logs/ab.log")
    
    class Config:
        env_file = ".env"
        env_prefix = "AB_"


# Singleton
_settings = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
