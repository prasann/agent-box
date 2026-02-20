"""Shared configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Global settings for all agents."""
    
    # Base data directory for all agents
    agb_data_dir: str = "~/.agb"
    
    # Ollama (shared)
    ollama_model: str = "qwen3:1.7b"
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
    findtab_db_path: str = "~/.agb/findtab/bookmarks.db"
    findtab_classifier_batch_size: int = 30
    findtab_enricher_batch_size: int = 15
    findtab_bootstrap_days: int = 7  # Days to look back on first run
    
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
