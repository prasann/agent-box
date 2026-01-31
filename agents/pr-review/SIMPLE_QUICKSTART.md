# PR Review Agent - Quick Start

> **Simple AI-powered PR review in < 900 lines of code**

## Install

```bash
cd agents/pr-review
pip install -e .
```

## Prerequisites

- GitHub CLI: `brew install gh` (or your package manager)
- GitHub Copilot CLI extension: `gh extension install github/gh-copilot`
- Authenticate: `gh auth login`

## Usage

**Review a PR:**
```bash
pr-agent 123
```

That's it! The agent will:
1. Fetch the PR diff using `gh CLI`
2. Automatically analyze it with Copilot
3. Start a conversation where you can refine the review
4. Post the review to GitHub when you're ready

## Commands

In the conversation:
- Just type naturally to ask questions or refine the review
- `/post` - Post as a full review
- `/comment` - Post as a simple comment
- `/exit` - Save and exit

## Example Session

```bash
$ pr-agent 123
🤖 PR Review Agent

Analyzing PR... This may take a moment.

# Summary of changes
This PR adds authentication middleware...

[detailed analysis follows]

Commands:
  Type your questions naturally
  /post    - Post review to GitHub
  /comment - Post as a comment only
  /exit    - Exit session

pr-123> Can you check the error handling in auth.py?

Thinking...

Looking at auth.py, the error handling could be improved...

pr-123> /post

Generating review summary...

Review to be posted:
[formatted review]

Post this as a review? (y/N): y

✓ Review posted successfully!

pr-123> /exit

✓ Session saved
```

## Architecture

6 simple files (< 900 lines total):
- `cli.py` - Entry point (~30 lines)
- `gh_utils.py` - GitHub CLI wrapper (~85 lines)
- `state.py` - JSON state management (~125 lines)
- `prompts.py` - Review prompts (~150 lines)
- `analyzer.py` - PR analysis logic (~125 lines)
- `repl.py` - Conversation loop (~195 lines)
- `git_utils.py` - Git utilities (~110 lines)

## How It Works

1. **Fetch**: Uses `gh CLI` to get PR data and diff
2. **Analyze**: Sends to Copilot with structured prompts
3. **Converse**: Natural language refinement loop
4. **Post**: Formats and posts via `gh CLI`

All state is stored in `~/.pr-agent/pr-{number}.json`

## Key Features

- ✅ LLM-driven analysis (no hardcoded rules)
- ✅ Natural conversation (no complex commands)
- ✅ Stateful sessions (resume anytime)
- ✅ Simple & maintainable (< 900 LOC)

See [implementation_plan.md](docs/implementation_plan.md) for architecture details.
