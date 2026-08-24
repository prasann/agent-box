"""Shared configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pathlib import Path

# Keep the checkout-local file as a fallback for existing installations. The
# shared file is loaded last so it wins consistently across xbar and worktrees.
_LEGACY_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"
_SHARED_ENV_FILE = Path.home() / ".agb" / ".env"


class Settings(BaseSettings):
    """Global settings for all agents."""
    
    # Base data directory for all agents
    agb_data_dir: str = "~/.agb"
    
    # Ollama (shared)
    ollama_model: str = "qwen3:1.7b"
    ollama_url: str = "http://localhost:11434"
    
    # Azure OpenAI (shared, Entra ID auth via az login)
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-10-21"
    
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
    findtab_rules_path: str = "~/.agb/findtab/rules.yaml"
    
    # Logging
    log_level: str = "INFO"
    log_file: Path = Path.home() / ".agb" / "logs" / "ab.log"
    
    class Config:
        env_file = (_LEGACY_ENV_FILE, _SHARED_ENV_FILE)
        env_prefix = "AB_"


# Singleton
_settings = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
