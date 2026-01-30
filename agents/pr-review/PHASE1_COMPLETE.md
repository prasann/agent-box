# PR Review Agent - Phase 1 Complete! 🎉

An AI-powered PR review assistant using GitHub Copilot that provides interactive code review sessions.

## ✅ Phase 1 Deliverables (COMPLETE)

All Phase 1 tasks from the implementation plan have been completed:

### 1.1 Project Scaffolding ✓
- ✅ Created `pyproject.toml` with uv configuration
- ✅ Set up package structure (`src/pr_agent/`)
- ✅ Created entry point with click CLI
- ✅ Added installation script
- ✅ Verified `pr-agent` command works

### 1.2 Basic CLI Commands ✓
- ✅ Implemented `pr-agent review <number>` command
- ✅ Automatic git repository detection
- ✅ GitHub remote URL parsing (owner/repo)
- ✅ Error handling for non-repo directories

### 1.3 PR Fetching ✓
- ✅ Created PR data fetcher using `gh` CLI
- ✅ Fetch PR metadata (title, author, files, stats)
- ✅ Fetch PR diff
- ✅ Pydantic models for type-safe data
- ✅ Cached to session directory

### 1.4 Session Management ✓
- ✅ Session storage system (`~/.config/pr-agent/sessions/`)
- ✅ Save PR metadata and diff to disk
- ✅ Conversation history persistence
- ✅ Feedback storage structure

### 1.5 Copilot SDK Integration ✓
- ✅ Installed GitHub Copilot SDK
- ✅ Created async wrapper client
- ✅ Chat and streaming support
- ✅ Session management with Copilot CLI

### 1.6 Basic Chat REPL ✓
- ✅ Interactive prompt with history
- ✅ Command parsing (`/help`, `/status`, `/files`, `/exit`)
- ✅ Rich terminal formatting
- ✅ Keyboard interrupt handling

### 1.7 Simple Q&A Flow ✓
- ✅ Send questions + PR context to Copilot
- ✅ Display AI responses with markdown
- ✅ Save conversation history
- ✅ Error handling

## Installation

```bash
cd agents/pr-review

# Install dependencies and CLI
bash scripts/install.sh

# Or manually with uv
uv sync
uv pip install -e .
```

## Prerequisites

1. **GitHub CLI (`gh`)**: Must be installed and authenticated
   ```bash
   brew install gh
   gh auth login
   ```

2. **GitHub Copilot CLI**: Required for AI functionality
   ```bash
   gh extension install github/gh-copilot
   ```

3. **Python 3.13+**: Required for the agent
   ```bash
   brew install python@3.13
   ```

4. **uv**: Modern Python package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Usage

```bash
# Navigate to a git repository with PRs
cd ~/my-project

# Start reviewing a PR
pr-agent review 123
```

### Example Session

```
🔍 Fetching PR #123...
✓ Loaded 8 files changed

╭─────────────────── PR #123 ───────────────────╮
│ Add new authentication feature                │
│                                                │
│ By: @octocat | 8 files                        │
│ Files: 8 | +245 -89                           │
╰────────────────────────────────────────────────╯

┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ File                   ┃ Changes┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ src/auth/login.ts      │ +123 -45│
│ src/auth/logout.ts     │ +45 -12 │
│ ...                    │         │
└────────────────────────┴─────────┘

✓ Ready to review!

Type your questions about the PR or commands:
  /help    - Show available commands
  /exit    - Exit the session

pr-123> what are the main changes in this PR?

Thinking...

The main changes in this PR introduce a new authentication 
system:

1. **New Login Flow** (`src/auth/login.ts`):
   - Implements OAuth2 authentication
   - Adds token refresh logic
   - Better error handling

2. **Logout Functionality** (`src/auth/logout.ts`):
   - Clears session data
   - Revokes tokens properly

pr-123> are there any security concerns?

Thinking...

Yes, there are a few security considerations:

1. **Token Storage**: The tokens are stored in localStorage 
   which could be vulnerable to XSS attacks. Consider using 
   httpOnly cookies instead.

2. **Error Messages**: Line 45 in login.ts exposes detailed 
   error messages that could leak sensitive information.

pr-123> /exit

✓ Session saved
```

## Commands

While in the interactive session:

- **Type any question** - Ask about the PR
- `/help` - Show available commands
- `/status` - Show session information
- `/files` - List changed files
- `/exit` or `exit` - Exit and save session

## Project Structure

```
agents/pr-review/
├── src/pr_agent/
│   ├── cli.py              # CLI entry point
│   ├── git_utils.py        # Git repository detection
│   ├── models/             # Pydantic data models
│   │   └── pr.py
│   ├── context/            # PR data fetching
│   │   └── pr_fetcher.py
│   ├── state/              # Session management
│   │   ├── session.py
│   │   └── storage.py
│   ├── copilot/            # Copilot SDK integration
│   │   └── client.py
│   └── chat/               # Interactive REPL
│       └── repl.py
├── scripts/
│   └── install.sh          # Installation script
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Session Storage

Sessions are saved in `~/.config/pr-agent/sessions/{owner}/{repo}/pr-{number}/`:

```
~/.config/pr-agent/sessions/
└── octocat/
    └── my-repo/
        └── pr-123/
            ├── metadata.json      # PR metadata
            ├── diff.txt           # PR diff
            ├── conversation.json  # Chat history
            ├── feedback.json      # Review feedback
            └── session_info.json  # Session info
```

## What's Next?

Phase 1 provides the foundation. Next phases will add:

- **Phase 2**: Smart context gathering (git history, file reading)
- **Phase 3**: Feedback management and review commands
- **Phase 4**: Review generation and posting to GitHub
- **Phase 5**: Polish, configuration, and documentation

## Troubleshooting

### "gh CLI is not authenticated"
```bash
gh auth login
```

### "Copilot CLI not found"
```bash
gh extension install github/gh-copilot
```

### "Not in a git repository"
Make sure you're running the command from within a git repository with a GitHub remote.

### "PR #X not found"
Verify the PR exists and you have access to it:
```bash
gh pr view 123
```

## Development

```bash
# Run in development mode
cd agents/pr-review
uv run pr-agent review 123

# Format code
uv run ruff check src/

# Type checking
uv run mypy src/
```

## License

MIT

## Contributing

This is a Phase 1 implementation. Contributions are welcome as we build out Phases 2-5!
