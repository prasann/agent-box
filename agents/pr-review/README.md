# PR Review Agent

> **AI-powered PR review with beautiful Chainlit UI**

A standalone Python agent that helps you understand, analyze, and review GitHub pull requests through an interactive web-based chat interface.

## Status
✅ **Chainlit UI Version** - Clean, modern interface

## Quick Start

**Simple way:**
```bash
# 1. Navigate to a git repo you want to review
cd ~/my-project

# 2. Run from the pr-agent directory
cd /path/to/agent-box/agents/pr-review
uv run python -m chainlit run app.py
```

**Even simpler - create an alias in `~/.zshrc`:**
```bash
alias pr-agent='cd ~/path/to/agent-box/agents/pr-review && uv run python -m chainlit run app.py'
```

Then from any repo:
```bash
cd ~/my-project
pr-agent  # Opens UI at http://localhost:8000
```

The app will:
1. Open a beautiful web UI in your browser
2. Check for uncommitted changes (will halt if found)
3. Ask for the PR number
4. Checkout the PR branch
5. Auto-analyze the PR with full codebase access
6. Enable natural conversation about the PR
7. Restore your original branch when done

**Important:** Make sure you have no uncommitted changes before starting.

## Key Features

- ✅ **Beautiful Chainlit UI**: Modern chat interface
- ✅ **LLM-Driven**: GitHub Copilot handles all analysis
- ✅ **Full Codebase Access**: Reviews PR changes in context of entire repository
- ✅ **Automatic Exploration**: LLM reads related files and checks consistency
- ✅ **Natural Conversation**: Chat naturally about the PR
- ✅ **Auto-Analysis**: Immediate PR analysis with metadata
- ✅ **Safe Branch Management**: Auto-checkout PR, restore original branch after
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
   - "Are there any other files that use this function?"
   - "Show me similar patterns in the codebase"

## Architecture

**Simple Structure:**
- `app.py` - Chainlit UI entry point
- `src/cli.py` - CLI launcher (auto-opens browser)
- `src/analyzer.py` - PR analysis with Copilot + codebase access
- `src/state.py` - JSON state management  
- `src/gh_utils.py` - GitHub CLI wrapper
- `src/repo_utils.py` - Repository operations (checkout, branch management)
- `src/prompts.py` - AI prompts

**How It Works:**
1. Checks repo is clean (no uncommitted changes)
2. Remembers your current branch
3. Checks out the PR branch
4. Creates Copilot session with `working_directory` set to repo root
5. LLM can now read any file, search codebase, check patterns
6. After review, restores your original branch

**State Storage:** `~/.pr-agent/pr-{number}.json`

## Requirements

- macOS (or Linux)
- Python 3.13+
- `gh` CLI (authenticated): `brew install gh && gh auth login`
- GitHub Copilot CLI: `gh extension install github/gh-copilot`
- GitHub Copilot license

## Installation

```bash
# Clone and install dependencies
cd agents/pr-review
uv sync

# Create an alias for easy access (optional)
echo "alias pr-agent='cd ~/path/to/agent-box/agents/pr-review && uv run python -m chainlit run app.py'" >> ~/.zshrc
source ~/.zshrc
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

