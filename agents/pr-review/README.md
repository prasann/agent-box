# PR Review Agent

> **AI-powered PR review with modern Streamlit UI**

A standalone Python agent that helps you understand, analyze, and review GitHub pull requests through an interactive web-based interface with 2-panel layout for efficient code review.

## Quick Start

**Simple way:**
```bash
# 1. Navigate to a git repo you want to review
cd ~/my-project

# 2. Run from the pr-agent directory
cd /path/to/agent-box/agents/pr-review
uv run pr-agent
```

**Even simpler - create an alias in `~/.zshrc`:**
```bash
alias pr-agent='cd ~/path/to/agent-box/agents/pr-review && uv run pr-agent'
```

Then from any repo:
```bash
cd ~/my-project
pr-agent  # Opens at http://localhost:8501
```

The app will:
1. Open a beautiful web UI in your browser
2. Check for uncommitted changes (will halt if found)
3. Ask for the PR number in the sidebar
4. Checkout the PR branch
5. Auto-analyze the PR with full codebase access
6. Display summary and findings in left panel
7. Enable natural conversation in right panel
8. Extract and track comments for posting
9. Restore your original branch when done

**Important:** Make sure you have no uncommitted changes before starting.

## Key Features

### Streamlit UI (Default)
- ✅ **2-Panel Layout**: Review summary (left) + Chat (right)
- ✅ **Persistent Comments**: Accumulate and review all comments before posting
- ✅ **Comment Management**: Edit, delete, export comments
- ✅ **Structured Display**: File/line references with code snippets
- ✅ **2-Panel Layout**: Review summary (left) + Chat (right)
- ✅ **Persistent Comments**: Accumulate and review all comments before posting
- ✅ **Comment Management**: Edit, delete, export comments
- ✅ **Structured Display**: File/line references with code snippets
- ✅ **GitHub Integration**: Post comments directly to PR
- ✅ **Full Codebase Access**: Reviews PR changes in context of entire repository**: Auto-checkout PR, restore original branch after
- ✅ **State Persistence**: Session state saved to `~/.pr-agent/`
- ✅ **Zero Config**: No repo setup needed

## Example Usage

### Streamlit UI
1. **Start the app:** `uv run pr-agent`
2. **Enter PR number** in sidebar and click "Analyze"
3. **Review summary and findings** in left panel
4. **Chat naturally** in right panel:
   - "Can you check the error handling?"
   - "What security concerns do you see?"
   - "Explain the changes in auth.py"
1. **Start the app:** `uv run pr-agent`
2. **Enter PR number** in sidebar and click "Analyze"
3. **Review summary and findings** in left panel
4. **Chat naturally** in right panel:
   - "Can you check the error handling?"
   - "What security concerns do you see?"
   - "Explain the changes in auth.py"
5. **Review comments** in left panel before posting
6. **Post to GitHub** when readyit UI (alternative)
├── src/
│   ├── analyzer.py          # PR analysis with Copilot
│   ├── comment_store.py     # Comment management
│   ├── comment_extractor.py # Extract comments from LLM
│   ├── state.py             # Session state
│   ├── gh_utils.py          # GitHub CLI wrapper
│   ├── repo_utils.py        # Git operations
│   ├── cli.py               # CLI entry point
│   └── ui/                  # Streamlit UI components
│       ├── sidebar.py
│       ├── review_panel.py
│       └── chat_panel.py
└── prompts/                 # AI prompts
├── src/
│   ├── analyzer.py          # PR analysis with Copilot
│   ├── comment_store.py     # Comment management
│   ├── comment_extractor.py # Extract comments from LLM
│   ├── state.py             # Session state
│   ├── gh_utils.py          # GitHub CLI wrapper
│   ├── repo_utils.py        # Git operations
│   ├── cli.py               # CLI entry point
│   └── ui/                  #
8. Posts to GitHub when ready
9. Restores your original branch

**State Storage:** `~/.pr-agent/pr-{number}-*.json`

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
echo "alias pr-agent='cd ~/path/to/agent-box/agents/pr-review && uv run pr-agent'" >> ~/.zshrc
source ~/.zshrc
```

## CLI Options

```bash
# Streamlit UI (default)
pr-agent
pr-agent --port 8501

# Chainlit UI
pr-agent --ui chainlit --port 8000

# Custom port
pr-agent --port 9000
```
Default (port 8501)
pr-agent Chainlit)
- Let the LLM do the work
- Minimal code, maximal clarity
- Natural conversation over commands
- Simple JSON state
- `gh CLI` for all GitHub operations

## Documentation

- [MIGRATION_PLAN.md](MIGRATION_PLAN.md) - Streamlit migration details
- [docs/simplified_architecture.md](docs/simplified_architecture.md) - Architecture details
- [IMPLEMENTATION_NOTES.md](IMOTES.md) - Implementation notes

