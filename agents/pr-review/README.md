# PR Review Agent

> **AI-powered PR review with beautiful Chainlit UI**

A standalone Python agent that helps you understand, analyze, and review GitHub pull requests through an interactive web-based chat interface.

## Status
✅ **Chainlit UI Version** - Clean, modern interface

## Quick Start

```bash
# Install dependencies
cd agents/pr-review
uv sync

# Run the app
uv run chainlit run app.py

# Or use the CLI (launches browser automatically)
uv run python -m src.cli 123
```

The agent will:
1. Open a beautiful web UI in your browser
2. Ask for the PR number
3. Auto-analyze the PR with AI
4. Enable natural conversation about the PR

## Key Features

- ✅ **Beautiful Chainlit UI**: Modern chat interface
- ✅ **LLM-Driven**: GitHub Copilot handles all analysis
- ✅ **Natural Conversation**: Chat naturally about the PR
- ✅ **Auto-Analysis**: Immediate PR analysis with metadata
- ✅ **State Persistence**: Session state saved to `~/.pr-agent/`
- ✅ **Zero Config**: No repo setup needed

## Example Usage

1. **Start the app:**
   ```bash
   uv run chainlit run app.py
   ```

2. **Enter PR number** when prompted

3. **Chat naturally:**
   - "Can you check the error handling?"
   - "What security concerns do you see?"
   - "Explain the changes in auth.py"

## Architecture

**Simple Structure:**
- `app.py` - Chainlit UI entry point
- `src/cli.py` - CLI launcher (auto-opens browser)
- `src/analyzer.py` - PR analysis with Copilot
- `src/state.py` - JSON state management  
- `src/gh_utils.py` - GitHub CLI wrapper
- `src/prompts.py` - AI prompts

**State Storage:** `~/.pr-agent/pr-{number}.json`

## Requirements

- macOS (or Linux)
- Python 3.13+
- `gh` CLI (authenticated): `brew install gh && gh auth login`
- GitHub Copilot CLI: `gh extension install github/gh-copilot`
- GitHub Copilot license

## Installation

```bash
# Clone and install
cd agents/pr-review
uv sync

# Optional: Install globally
uv tool install .  # Requires Python 3.13

# Or run directly
uv run chainlit run app.py
```

## Philosophy

> "Beautiful UI, simple code, powerful AI"

- Modern web UI with Chainlit
- Let the LLM do the work
- Minimal code, maximal clarity
- Natural conversation over commands
- Simple JSON state
- `gh CLI` for all GitHub operations

## Documentation

- [docs/simplified_architecture.md](docs/simplified_architecture.md) - Architecture details
- [docs/implementation_plan.md](docs/implementation_plan.md) - Original plan

