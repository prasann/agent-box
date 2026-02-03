# Agent Box - Unified Multi-Agent System

## Overview
Single Python package that provides multiple AI agents as subcommands. Install once, get all agents.

## User Experience

**Install once**:
```bash
pipx install agent-box
```

**Use all agents**:
```bash
# Gmail spam cleaner
agents gmail clean --from-date 2026-02-01
agents gmail clean --dry-run

# Grammar/typo checker
agents text fix
agents text rewrite

# Future agents...
agents <domain> <action> [options]
```

## Architecture

```
┌─────────────────────────────────────┐
│         Agent Box CLI               │
│  (Single entry point: "agents")     │
└──────────────┬──────────────────────┘
               │
    ┏━━━━━━━━━━┻━━━━━━━━━━┓
    ┃                      ┃
    ▼                      ▼
┌─────────┐          ┌──────────┐
│  Gmail  │          │   Text   │
│  Agent  │          │  Agent   │
└────┬────┘          └────┬─────┘
     │                    │
     ▼                    ▼
┌──────────────────────────────┐
│   Shared Infrastructure      │
│  - Ollama Client             │
│  - Config Management         │
│  - Logging                   │
│  - Error Handling            │
└──────────────────────────────┘
```

## Project Structure

```
agent-box/
├── README.md
├── pyproject.toml              # Single package definition
├── .gitignore
├── .env.example
├── src/
│   └── agent_box/
│       ├── __init__.py
│       ├── __main__.py         # Main CLI entry point
│       │
│       ├── core/               # Shared infrastructure
│       │   ├── __init__.py
│       │   ├── ollama_client.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   └── exceptions.py
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   │
│       │   ├── gmail/          # Gmail spam cleaner
│       │   │   ├── __init__.py
│       │   │   ├── agent.py
│       │   │   ├── gmail_client.py
│       │   │   ├── models.py
│       │   │   └── commands.py   # CLI subcommands
│       │   │
│       │   └── text/           # Text grammar checker
│       │       ├── __init__.py
│       │       ├── checker.py
│       │       ├── clipboard.py
│       │       ├── models.py
│       │       └── commands.py   # CLI subcommands
│       │
│       └── cli/                # CLI infrastructure
│           ├── __init__.py
│           └── main.py         # Command routing
│
├── data/                       # Runtime data (gitignored)
│   ├── credentials.json        # Gmail OAuth
│   ├── token.json             # Gmail token
│   └── processed_emails.json  # State
│
└── tests/
    ├── test_gmail_agent.py
    └── test_text_agent.py
```

## Package Definition (pyproject.toml)

```toml
[project]
name = "agent-box"
version = "0.1.0"
description = "Collection of AI agents for personal productivity"
requires-python = ">=3.10"

dependencies = [
    # Gmail agent deps
    "google-auth>=2.0.0",
    "google-auth-oauthlib>=1.0.0",
    "google-auth-httplib2>=0.1.0",
    "google-api-python-client>=2.0.0",
    
    # Text agent deps
    "requests>=2.31.0",
    
    # Shared deps
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0.0",
    "rich>=13.0.0",          # Nice terminal output
    "click>=8.1.0",          # Better CLI than argparse
    "tenacity>=8.0.0",       # Retry logic
]

[project.scripts]
agents = "agent_box.__main__:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## CLI Architecture (Using Click)

### Main Entry Point: `__main__.py`

```python
"""Main CLI entry point."""
import click
from agent_box.agents.gmail.commands import gmail_group
from agent_box.agents.text.commands import text_group

@click.group()
@click.version_option()
def main():
    """Agent Box - Personal AI agents for productivity."""
    pass

# Register agent command groups
main.add_command(gmail_group)
main.add_command(text_group)

if __name__ == "__main__":
    main()
```

### Gmail Commands: `agents/gmail/commands.py`

```python
"""Gmail agent CLI commands."""
import click
from datetime import datetime
from agent_box.core.ollama_client import OllamaClient
from agent_box.core.config import Settings
from .agent import GmailSpamCleaner
from .gmail_client import GmailClient

@click.group(name="gmail")
def gmail_group():
    """Gmail spam cleaner agent."""
    pass

@gmail_group.command(name="clean")
@click.option("--from-date", type=click.DateTime(formats=["%Y-%m-%d"]),
              help="Start date (YYYY-MM-DD)")
@click.option("--to-date", type=click.DateTime(formats=["%Y-%m-%d"]),
              help="End date (YYYY-MM-DD)")
@click.option("--max-emails", type=int, default=1000,
              help="Maximum emails to process")
@click.option("--dry-run", is_flag=True,
              help="Test without applying labels")
@click.option("--verbose", "-v", is_flag=True,
              help="Verbose logging")
def clean(from_date, to_date, max_emails, dry_run, verbose):
    """Classify and tag spam/promotional emails."""
    settings = Settings()
    
    # Initialize clients
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url
    )
    gmail = GmailClient(settings)
    
    # Run agent
    agent = GmailSpamCleaner(gmail, ollama, settings)
    agent.process_emails(
        from_date=from_date,
        to_date=to_date,
        max_emails=max_emails,
        dry_run=dry_run
    )
```

### Text Commands: `agents/text/commands.py`

```python
"""Text agent CLI commands."""
import click
from agent_box.core.ollama_client import OllamaClient
from agent_box.core.config import Settings
from .checker import GrammarChecker

@click.group(name="text")
def text_group():
    """Text grammar and typo checker."""
    pass

@text_group.command(name="fix")
@click.option("--no-preview", is_flag=True,
              help="Don't show preview")
def fix(no_preview):
    """Fix typos and grammar in clipboard."""
    settings = Settings()
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url
    )
    checker = GrammarChecker(ollama, settings)
    checker.process_clipboard(mode="fix", show_preview=not no_preview)

@text_group.command(name="rewrite")
@click.option("--no-preview", is_flag=True,
              help="Don't show preview")
def rewrite(no_preview):
    """Rewrite text in clipboard for clarity."""
    settings = Settings()
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url
    )
    checker = GrammarChecker(ollama, settings)
    checker.process_clipboard(mode="rewrite", show_preview=not no_preview)
```

## Shared Infrastructure

### Ollama Client: `core/ollama_client.py`

```python
"""Shared Ollama API client."""
import requests
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

class OllamaClient:
    """Client for Ollama API - shared across all agents."""
    
    def __init__(self, model: str = "llama3.2:3b", 
                 base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    @retry(stop=stop_after_attempt(3), 
           wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text with retry logic."""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        return response.json()["response"]
    
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
```

### Configuration: `core/config.py`

```python
"""Shared configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Global settings for all agents."""
    
    # Ollama (shared)
    ollama_model: str = "llama3.2:3b"
    ollama_url: str = "http://localhost:11434"
    
    # Gmail agent
    gmail_batch_size: int = 100
    gmail_max_emails_per_run: int = 1000
    gmail_label_name: str = "NeedsReview/Spam"
    gmail_mark_as_read: bool = False
    gmail_credentials_file: Path = Path("data/credentials.json")
    gmail_token_file: Path = Path("data/token.json")
    gmail_state_file: Path = Path("data/processed_emails.json")
    
    # Text agent
    text_show_preview: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: Path = Path("data/logs/agent-box.log")
    
    class Config:
        env_file = ".env"
        env_prefix = "AGENT_BOX_"

# Singleton
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

### Logging: `core/logging.py`

```python
"""Shared logging configuration."""
import logging
from pathlib import Path
from rich.logging import RichHandler

def setup_logging(log_level: str = "INFO", log_file: Path = None):
    """Configure logging for all agents."""
    
    handlers = [RichHandler(rich_tracebacks=True)]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=handlers
    )
```

## Installation & Setup

### 1. Install Package
```bash
# Clone repo
git clone https://github.com/prasann/agent-box.git
cd agent-box

# Install with pipx (isolated environment)
pipx install .

# Or install in development mode
pipx install -e .
```

### 2. Initial Setup
```bash
# Pull Ollama model (shared by all agents)
ollama pull llama3.2:3b

# For Gmail agent: Set up OAuth
# 1. Download credentials.json from Google Cloud Console
# 2. Place in data/credentials.json
# 3. First run will open browser for OAuth
agents gmail clean --dry-run
```

### 3. Configuration (Optional)
```bash
# Create .env file in project root
cat > .env << EOF
AGENT_BOX_OLLAMA_MODEL=llama3.2:3b
AGENT_BOX_OLLAMA_URL=http://localhost:11434
AGENT_BOX_LOG_LEVEL=INFO
EOF
```

## Usage Examples

```bash
# Gmail Agent
# ------------
# Test without changes
agents gmail clean --dry-run

# Clean inbox (process new emails)
agents gmail clean

# Process specific date range
agents gmail clean --from-date 2026-01-01 --to-date 2026-01-31

# Limit processing
agents gmail clean --max-emails 500

# Verbose logging
agents gmail clean -v


# Text Agent
# -----------
# Fix grammar (copy text first)
agents text fix

# Rewrite text (copy text first)
agents text rewrite

# No preview (just clipboard)
agents text fix --no-preview


# Help
# ----
# Top-level help
agents --help

# Agent-specific help
agents gmail --help
agents gmail clean --help
agents text --help
```

## Adding New Agents

Simple 3-step process:

### 1. Create Agent Directory
```
src/agent_box/agents/new_agent/
├── __init__.py
├── agent.py       # Core logic
├── models.py      # Pydantic models
└── commands.py    # CLI commands
```

### 2. Implement Commands
```python
# commands.py
import click

@click.group(name="newagent")
def newagent_group():
    """New agent description."""
    pass

@newagent_group.command(name="action")
@click.option("--option", help="Some option")
def action(option):
    """Do something."""
    # Use shared OllamaClient, Settings, etc.
    pass
```

### 3. Register in Main CLI
```python
# __main__.py
from agent_box.agents.new_agent.commands import newagent_group

main.add_command(newagent_group)
```

Done! Now `agents newagent action` works.

## CLI Help System

```bash
$ agents --help
Usage: agents [OPTIONS] COMMAND [ARGS]...

  Agent Box - Personal AI agents for productivity.

Options:
  --version  Show version
  --help     Show this message

Commands:
  gmail  Gmail spam cleaner agent
  text   Text grammar and typo checker

$ agents gmail --help
Usage: agents gmail [OPTIONS] COMMAND [ARGS]...

  Gmail spam cleaner agent.

Commands:
  clean  Classify and tag spam/promotional emails

$ agents gmail clean --help
Usage: agents gmail clean [OPTIONS]

  Classify and tag spam/promotional emails.

Options:
  --from-date [%Y-%m-%d]  Start date (YYYY-MM-DD)
  --to-date [%Y-%m-%d]    End date (YYYY-MM-DD)
  --max-emails INTEGER    Maximum emails to process
  --dry-run              Test without applying labels
  -v, --verbose          Verbose logging
  --help                 Show this message
```

## Scheduling Agents

### Gmail Agent (Cron)
```bash
# Add to crontab
crontab -e

# Run every 6 hours
0 */6 * * * /Users/you/.local/bin/agents gmail clean >> ~/logs/agent-box.log 2>&1
```

### Text Agent (Always Available)
Just type `agents text fix` in terminal whenever needed.

## Configuration Management

### Environment Variables
```bash
# Global settings
export AGENT_BOX_OLLAMA_MODEL="llama3.2:3b"
export AGENT_BOX_OLLAMA_URL="http://localhost:11434"

# Gmail-specific
export AGENT_BOX_GMAIL_LABEL_NAME="Spam/NeedsReview"
export AGENT_BOX_GMAIL_MAX_EMAILS_PER_RUN=500

# Text-specific
export AGENT_BOX_TEXT_SHOW_PREVIEW=false
```

### .env File
```bash
# .env (in project root)
AGENT_BOX_OLLAMA_MODEL=llama3.2:3b
AGENT_BOX_OLLAMA_URL=http://localhost:11434
AGENT_BOX_LOG_LEVEL=INFO

# Gmail
AGENT_BOX_GMAIL_LABEL_NAME=NeedsReview/Spam
AGENT_BOX_GMAIL_MAX_EMAILS_PER_RUN=1000

# Text
AGENT_BOX_TEXT_SHOW_PREVIEW=true
```

### Per-Command Options
```bash
# Override via CLI flags
agents gmail clean --max-emails 100
agents text fix --no-preview
```

## Testing Strategy

```python
# tests/test_gmail_agent.py
import pytest
from agent_box.agents.gmail.agent import GmailSpamCleaner

def test_gmail_classification():
    # Mock Ollama, test classification logic
    pass

# tests/test_text_agent.py
from agent_box.agents.text.checker import GrammarChecker

def test_grammar_fix():
    # Mock Ollama, test fix logic
    pass

# tests/test_ollama_client.py
from agent_box.core.ollama_client import OllamaClient

def test_ollama_retry():
    # Test retry logic
    pass
```

Run tests:
```bash
pytest
pytest --cov=agent_box
```

## Future Agent Ideas

Easy to add new agents following the same pattern:

```bash
# Calendar agent
agents calendar summarize --tomorrow
agents calendar find-conflicts

# File organizer agent
agents files organize ~/Downloads --by-date
agents files dedupe ~/Documents

# Code review agent
agents code review --file src/main.py
agents code explain --function process_data

# Notes agent
agents notes summarize ~/notes/daily/*.md
agents notes search "project ideas"
```

## Why This Architecture Works

✅ **Single install**: One `pipx install`, all agents available  
✅ **Unified CLI**: Consistent command structure  
✅ **Shared code**: No duplication (Ollama client, config, logging)  
✅ **Easy to extend**: Add new agents in 3 steps  
✅ **Proper packaging**: Professional Python project structure  
✅ **Type-safe**: Pydantic models for everything  
✅ **Good UX**: Rich terminal output, help system  
✅ **Testable**: Clean separation, easy to mock  
✅ **Configurable**: Env vars, .env, CLI flags  
✅ **Maintainable**: Clear structure, not a complex monorepo  

## Comparison to Separate Packages

| Aspect | Separate Packages | Unified Agent Box |
|--------|------------------|-------------------|
| **Installation** | Multiple `pipx install` | Single `pipx install` ✅ |
| **Updates** | Update each separately | One update for all ✅ |
| **Shared code** | Duplicate/copy | Reuse ✅ |
| **CLI consistency** | Different patterns | Unified ✅ |
| **Configuration** | Multiple .env files | Single config ✅ |
| **Adding agents** | New repo/package | Add folder ✅ |
| **Discoverability** | Find each package | `agents --help` ✅ |

## Development Time Estimate

- Project setup: 1 hour
- Shared infrastructure (Ollama, config, logging): 2 hours
- CLI framework (Click integration): 1 hour
- Migrate Gmail agent: 2 hours
- Migrate Text agent: 1 hour
- Testing: 2 hours
- Documentation: 1 hour

**Total**: ~10 hours for full unified system

## Dependencies Summary

**Core** (shared):
- `click` - Modern CLI framework
- `rich` - Beautiful terminal output
- `pydantic` + `pydantic-settings` - Config & models
- `tenacity` - Retry logic
- `requests` - HTTP client

**Gmail agent**:
- `google-auth*` - OAuth
- `google-api-python-client` - Gmail API

**Text agent**:
- No additional deps (uses macOS `pbpaste`/`pbcopy`)

**Total size**: ~50MB including all dependencies

## Deployment Options

### Local Development
```bash
pipx install -e .  # Editable mode
```

### Personal Use
```bash
pipx install git+https://github.com/prasann/agent-box.git
```

### Future: PyPI
```bash
pipx install agent-box  # If published
```

## Security Considerations

- **Gmail OAuth**: Tokens stored in `data/` (gitignored)
- **File permissions**: Set 600 on sensitive files
- **API keys**: Never in code, only env vars
- **Ollama**: Local only (no external API calls with sensitive data)
- **Clipboard**: Text stays local (not sent to cloud)

## Monitoring & Logging

All agents log to:
- **Console**: Rich formatted output
- **File**: `data/logs/agent-box.log` (optional)

Log format:
```
2026-02-03 10:30:00 - agent_box.agents.gmail - INFO - Processing 150 emails
2026-02-03 10:30:15 - agent_box.agents.gmail - INFO - Tagged 12 spam, 8 promotional
```

## Known Limitations

- **macOS only**: Text agent uses `pbpaste`/`pbcopy`
- **Local Ollama**: Requires Ollama running
- **Gmail OAuth**: One-time browser auth needed
- **Single user**: Not designed for multi-user

## Migration from Separate Packages

If you already built separate packages:

1. Create unified structure (see above)
2. Move Gmail agent to `agents/gmail/`
3. Move Text agent to `agents/text/`
4. Extract shared code to `core/`
5. Create CLI commands for each
6. Test both agents work
7. Uninstall old packages: `pipx uninstall gmail-spam-cleaner mac-grammar-checker`
8. Install unified: `pipx install .`

Takes ~2-3 hours to migrate properly.
