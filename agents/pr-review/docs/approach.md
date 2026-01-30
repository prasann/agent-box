# PR Review Agent - Implementation Approach

## Overview
A standalone Python agent that performs autonomous PR reviews by reading repository context from disk and git, using GitHub Copilot SDK for reasoning.

## Architecture Decision

### Chosen Approach: Standalone Python Agent with Disk + Git Context

```
┌─────────────────────────────────────┐
│   PR Review Agent (Python CLI)     │
│   - Autonomous reasoning            │
│   - Uses Copilot SDK                │
│   - Manages local state             │
└─────────────────────────────────────┘
         ↓              ↓
    GitHub API    Filesystem + Git
    (gh CLI)      (repo on disk)
         ↓              ↓
    PR metadata   File contents
    PR diff       Git history
                  Repo structure
         ↓
    ┌─────────────────────┐
    │  Copilot SDK        │
    │  (AI Reasoning)     │
    └─────────────────────┘
         ↓
    Analysis & Review
```

### Why This Approach?

**Advantages:**
- ✅ Fully standalone - no VSCode dependency required
- ✅ Simple to build and debug
- ✅ Portable - runs anywhere (terminal, SSH, containers)
- ✅ Transparent - explicit context gathering
- ✅ Foundation for multiple agents
- ✅ No repository pollution (state stored in ~/.config)
- ✅ Can iterate quickly

**Trade-offs:**
- ⚠️ No pre-indexed semantic search (but Copilot SDK provides this)
- ⚠️ Manual context selection (but gives us control)
- ⚠️ Must read files from disk (but this is actually fine for PRs)

## Technology Stack

### Core
- **Language:** Python 3.10+
- **AI Reasoning:** GitHub Copilot SDK (Python client)
- **GitHub Integration:** `gh` CLI (for PR data) + `git` CLI (for repo context)
- **State Management:** JSON files in `~/.config/pr-agent/`

### Dependencies
```
github-copilot-sdk  # AI reasoning
click              # CLI interface
prompt_toolkit     # Interactive chat REPL
gitpython          # Git operations (alternative to subprocess)
rich               # Terminal UI/formatting
pydantic           # Data models & validation
```

## Context Gathering Strategy

### What Agent Can Access from Disk + Git

**PR Context (via gh CLI):**
```bash
gh pr view 123 --json title,body,author,files,commits
gh pr diff 123
```

**Repository Context (via filesystem):**
- Changed file contents (read from disk)
- Related files (imports, test files)
- Directory structure
- Configuration files (package.json, pyproject.toml, etc.)
- Documentation (README, CONTRIBUTING)

**Git Context (via git CLI):**
```bash
git log --oneline -20 <file>           # Recent history
git blame <file>                       # Line attribution
git log --all --pretty=format: --name-only --diff-filter=A | grep <file>  # File creation
git log --follow <file>                # File history including renames
```

### Smart Context Selection

**For Small PRs (< 10 files):**
- Send full diff + all changed file contents
- Include related test files
- Add recent git history for changed files

**For Medium PRs (10-30 files):**
- Group changes by logical module/directory
- Send diff + changed files + immediate dependencies
- Prioritize core logic over config changes

**For Large PRs (30+ files):**
- Process in chunks (by module/feature)
- Analyze each chunk separately
- Synthesize findings at the end
- Use multi-pass analysis

## Project Structure

```
pr-review-agent/
├── pyproject.toml              # Project config & dependencies
├── README.md
├── src/
│   ├── pr_agent/
│   │   ├── __init__.py
│   │   ├── chat/
│   │   │   ├── __init__.py
│   │   │   ├── repl.py         # Interactive chat loop
│   │   │   ├── commands.py     # Chat command handlers (/feedback, /generate, etc.)
│   │   │   └── formatter.py    # Chat output formatting
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── reviewer.py     # Main PR review orchestration
│   │   │   ├── analyzer.py     # Code analysis logic
│   │   │   ├── conversation.py # Manages multi-turn chat with Copilot
│   │   │   └── prompts.py      # Prompt templates for Copilot
│   │   ├── context/
│   │   │   ├── __init__.py
│   │   │   ├── pr_fetcher.py   # Fetch PR data via gh CLI
│   │   │   ├── repo_reader.py  # Read files from disk
│   │   │   ├── git_context.py  # Git history/blame operations
│   │   │   └── context_builder.py  # Smart context selection
│   │   ├── copilot/
│   │   │   ├── __init__.py
│   │   │   ├── client.py       # Copilot SDK wrapper
│   │   │   └── auth.py         # Authentication handling
│   │   ├── state/
│   │   │   ├── __init__.py
│   │   │   ├── session.py      # Session management
│   │   │   └── storage.py      # File storage (~/.config/pr-agent)
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── pr.py           # PR data models
│   │       ├── review.py       # Review/feedback models
│   │       └── session.py      # Session state models
├── tests/
│   ├── test_reviewer.py
│   ├── test_context.py
│   ├── test_chaer.py
│   ├── test_context.py
│   └── fixtures/
└── examples/
    └── sample_review.md
```

## State Management

### Storage Location
```
~/.config/pr-agent/
├── config.json                 # Global config
└── sessions/conversation.json  # Full chat history (questions + answers)
    └── <repo-owner>/<repo-name>/
        └── pr-<number>/
            ├── metadata.json   # PR info, status
            ├── diff.patch      # Full PR diff
            ├── context.json    # Gathered repo context
            ├── analysis.md     # Initial analysis
            ├── qa.log          # Q&A history
            ├── feedback.json   # Accumulated review comments
            └── review.md       # Final review draft
```

### Session Lifecycle
1. `pr-agent review 123` → Creates session directory, enters chat
2. Fetches and caches PR data
3. Runs initial analysis, shows summary
4. Interactive chat loop:
   - User asks questions (conversation persisted to qa.log)
   - User adds feedback via `/feedback` command (saved to feedback.json)
   - Multi-turn conversation maintained in memory
5. User runs `/generate` → Creates review.md from feedback
6. User runs `/preview` → Reviews draft
7. User runs `/post` → Posts to GitHub
8. User exits chat → Session saved for later resume
9. `pr-agent resume 123` → Re-enter chat with full history

## CLI Interface

### Primary Mode: Interactive Chat

The main interface is an **interactive chat session** focused on a single PR:

```bash
$ pr-agent review 123

🔍 Fetching PR #123...
📦 Found 8 files changed
🤖 Analyzing with Copilot...

━━━━━━━━━━━━━━━━━━━━━━━━━━━
PR #123: Refactor authentication system
By: @developer | 8 files | +245 -189

Summary:
Authentication refactor - moves from JWT to session-based auth
Main changes in src/auth/, tests updated

Entering review chat. Type 'help' for commands, 'exit' to quit.
━━━━━━━━━━━━━━━━━━━━━━━━━━━

pr-123> what does the session storage implementation look like?

[Agent analyzes and responds with context from the PR...]

pr-123> are there any security concerns?

[Agent responds...]

pr-123> /feedback src/auth/session.ts:45-60 "Need to add session timeout handling"

✓ Feedback added

pr-123> /generate

✓ Review generated. Use '/preview' to see it.

pr-123> /preview

[Shows review draft...]

pr-123> /post --request-changes

✓ Review posted to GitHub

pr-123> exit

Session saved. Use 'pr-agent resume 123' to continue.
```

### Chat Commands

Within the chat session:

**Questions (natural language):**
- Just type your question: `what does this change?`
- `why was this approach chosen?`
- `are there any breaking changes?`

**Special Commands (prefixed with `/`):**
- `/feedback <file>:<lines> "<comment>"` - Add review feedback
- `/feedback list` - View accumulated feedback
- `/feedback delete <id>` - Remove a feedback item
- `/generate` - Generate review from feedback
- `/preview` - Preview review draft
- `/post [--approve|--request-changes|--comment]` - Post to GitHub
- `/status` - Show session status
- `/context` - Show what context the agent has loaded
- `/help` - Show available commands
- `/exit` or `exit` - Exit chat (session saved)

### Alternative: Command Mode (Optional)

For scripting or quick operations, also support one-off commands:

```bash
# Quick review without entering chat
pr-agent review 123 --summary-only

# Ask a single question (uses existing session)
pr-agent ask 123 "what does this auth change do?"

# Add feedback from command line
pr-agent feedback 123 add --file src/auth.ts --lines 45-60 --comment "Need null check"

# Generate and post (for automation)
pr-agent generate 123
pr-agent post 123 --comment

# Resume existing session
pr-agent resume 123

# View session status
pr-agent status 123

# Clean up old sessions
pr-agent cleanup
```chat interface

**Deliverables:**
- ✅ Project structure setup
- ✅ CLI skeleton with `review` command
- ✅ Interactive chat REPL (using prompt_toolkit)
- ✅ PR fetcher (via gh CLI)
- ✅ Basic file reader from disk
- ✅ Copilot SDK integration
- ✅ Multi-turn conversation management
- ✅ Simple prompt: "Analyze this PR"
- ✅ Terminal output formatting with rich

**Test:** `pr-agent review 123` enters chat, can ask questions, exit and resume
- ✅ PR fetcher (via gh CLI)
- ✅ Basic file reader from disk
- ✅ Copilot SDK integration
- ✅ Simple prompt: "Analyze this PR"
- ✅ Terminal output formatting

**Test:** `pr-agent review 123` produces a summary

### Phase 2: Context Enhancement
**Goal:** Smarter context gathering

**Deliverables:**
- ✅ Git context integration (history, blame)
- ✅ Smart file selection (related files, tests)
- ✅ Context size management (chunking)
- ✅ Improved prompts with structured context

**Test:** RevFeedback & Commands
**Goal:** Review feedback accumulation and chat commands

**Deliverables:**
- ✅ Chat commands: `/feedback`, `/generate`, `/preview`, `/post`
- ✅ Feedback management (add, list, delete)
- ✅ Persistent conversation.json and feedback.json
- ✅ Session resume functionality

**Test:** Full interactive review workflow in chat

**Test:** Full interactive review workflow

### Phase 4: Review Generation & Posting
**Goal:** Generate and post reviews

**Deliverables:**
- ✅ Review synthesis from feedback
- ✅ `generate` command
- ✅ `post` command (via gh CLI)
- ✅ Preview and edit support

**Test:** Complete end-to-end review posted to GitHub

### Phase 5: Polish & Extensibility
**Goal:** Production-ready & reusable patterns

**Deliverables:**
- ✅ Error handling & retry logic
- ✅ Command mode (optional - one-off commands for scripting)
- ✅ Configuration file support
- ✅ Logging and debugging
- ✅ Documentation
- ✅ Shared agent utilities (for future agents)

**Test:** Robust, well-documented, ready for more agents

## Copilot SDK Integration

### Authentication
- Use existing GitHub Copilot license
- Token management via GitHub CLI auth
- Fallback to environment variables

### Usage Pattern
```python
from copilot_sdk import CopilotClient
Multi-turn conversation (for chat mode)
messages = [
    {"role": "system", "content": "You are a PR reviewer. Context: [PR diff here]"},
    {"role": "user", "content": "What are the main changes?"},
    {"role": "assistant", "content": "The main changes are..."},
    {"role": "user", "content": "Are there security concerns?"}
]
response = client.chat(messages)

# Streaming for real-time responses in chat
for chunk in client.chat_stream(messages):
    print(chunk.content, end='', flush=True)
```

**Key Pattern for Chat:**
- Maintain conversation history in memory during session
- Each question adds to the messages array
- Context (PR diff, files) injected in system message
- Persist full conversation to `conversation.json` on exittreaming for long analysis
for chunk in client.chat_stream(messages):
    print(chunk.content, end='')
```

### Prompt Strategy
- **System prompt:** Define reviewer persona and guidelines
- **Context injection:** Structured context (diff, files, history)
- **Task-specific prompts:** Different prompts for analysis vs Q&A vs synthesis
- **Chain-of-thought:** Ask Copilot to explain reasoning

## Error Handling & Fallbacks

### Missing Dependencies
- Check for `gh` CLI → Clear error message + install instructions
- Check for git → Error with instructions
- Check Copilot auth → Guide user through authentication

### API Failures
- Copilot SDK timeout → Retry with exponential backoff
- GitHub API rate limit → Inform user, suggest waiting
- Network issues → Cache what we can, degrade gracefully

### Context Too Large
- Truncate diff intelligently (focus on core changes)
- Chunk large PRs automatically
- Warn user about incomplete context

## Future Extensibility

### Design for Multiple Agents
- Extract common patterns into `shared/` module
- Reusable: Copilot client, state management, CLI patterns
- Each agent can have its own subdirectory

### Potential Future Agents
```
agents/
├── pr_review/          # This MVP
├── code_quality/       # Linting + best practices
├── security_scan/      # Security review
├── test_generator/     # Generate missing tests
└── docs_updater/       # Update docs for code changes
```

### MCP Integration (Future)
- Add MCP server wrapper around agents
- VSCode can invoke agents via MCP
- Agents remain standalone, MCP is just an interface

## Success Metrics (MVP)

- [ ] Can review a typical PR (10-20 files) end-to-end
- [ ] Produces actionable feedback
- [ ] Takes < 2 minutes for initial analysis
- [ ] Interactive Q&A works smoothly
- [ ] Successfully posts review to GitHub
- [ ] Zero config needed (besides gh auth)
- [ ] Clear error messages for common issues

## Next Steps

1. Set up Python project structure
2. Implement Phase 1 (Foundation)
3. Test with real PRs from your repos
4. Iterate based on actual usage
5. Expand to Phases 2-4

---

**Key Principle:** Start simple, validate with real usage, layer complexity as needed.
