# PR Review Agent

> **Simple AI-powered PR review in < 900 lines of code**

A standalone Python CLI agent that helps you understand, analyze, and review GitHub pull requests through natural conversation with AI.

## Status
✅ **Simplified & Ready** - Version 1.0

## Quick Start

```bash
# Install
cd agents/pr-review
pip install -e .

# Review any PR
pr-agent 123
```

That's it! The agent will:
1. Auto-analyze the PR with AI
2. Start a natural conversation
3. Let you refine and post the review

## Key Features

- ✅ **LLM-Driven**: Copilot handles all analysis
- ✅ **Simple Commands**: Just `/post`, `/comment`, `/exit`
- ✅ **Auto-Analysis**: Immediate PR analysis on start
- ✅ **Natural Conversation**: Type questions naturally
- ✅ **State Persistence**: Resume sessions anytime
- ✅ **Zero Config**: No repo setup needed

## Example Session

```bash
$ pr-agent 123
🤖 PR Review Agent

Analyzing PR... 

# Summary
This PR adds authentication middleware...
[detailed analysis]

Commands:
  Type naturally or use /post, /comment, /exit

pr-123> Can you check the error handling in auth.py?

Thinking...

Looking at auth.py, the error handling could be improved...

pr-123> /post

✓ Review posted to GitHub!

pr-123> /exit
✓ Session saved
```

## Architecture

**6 Simple Files (~835 lines total):**
- `cli.py` (32 lines) - Entry point
- `gh_utils.py` (85 lines) - GitHub CLI wrapper
- `state.py` (125 lines) - JSON state management
- `prompts.py` (147 lines) - AI prompts
- `analyzer.py` (123 lines) - PR analysis
- `repl.py` (195 lines) - Conversation loop
- `git_utils.py` (111 lines) - Git utilities

## Documentation

- [SIMPLE_QUICKSTART.md](SIMPLE_QUICKSTART.md) - Quick start guide
- [SIMPLIFICATION_SUMMARY.md](SIMPLIFICATION_SUMMARY.md) - What changed
- [docs/simplified_architecture.md](docs/simplified_architecture.md) - Architecture details
- [docs/implementation_plan.md](docs/implementation_plan.md) - Original plan
- [docs/agentic_architecture_proposal.md](docs/agentic_architecture_proposal.md) - Design rationale

## Requirements

- macOS (or Linux)
- Python 3.13+
- `gh` CLI (authenticated): `brew install gh && gh auth login`
- GitHub Copilot CLI: `gh extension install github/gh-copilot`
- GitHub Copilot license

## Philosophy

> "Make it work, make it simple, make it obvious"

- Let the LLM do the work
- Minimal code, maximal clarity
- Natural conversation over commands
- Simple JSON state
- `gh CLI` for all GitHub operations
