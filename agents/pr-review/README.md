# PR Review Agent

Autonomous PR review agent that helps understand, analyze, and review GitHub pull requests through an interactive chat interface.

## Status
🚧 **In Development** - Planning Phase

## Overview

A standalone Python CLI agent that:
- Fetches PR data from GitHub
- Reads repository context from disk + git
- Uses GitHub Copilot SDK for AI reasoning
- Provides interactive chat interface for PR review
- Accumulates feedback and generates review comments
- Posts reviews to GitHub

## Key Features

- **Interactive Chat**: Natural conversation about the PR
- **Context-Aware**: Reads files, git history, and PR diff
- **Autonomous Analysis**: Initial PR summary and concern detection
- **Feedback Management**: Accumulate and organize review comments
- **Session Persistence**: Resume reviews later
- **No Repo Pollution**: All state in `~/.config/pr-agent/`

## Documentation

- [MVP Specification](docs/mvp_spec.md) - Original requirements and goals
- [Implementation Approach](docs/approach.md) - Detailed architecture and plan

## Quick Start (Future)

```bash
# Start reviewing a PR
pr-agent review 123

# Chat with the agent about the PR
pr-123> what are the main changes?
pr-123> are there security concerns?
pr-123> /feedback src/auth.ts:45-60 "Need null check"
pr-123> /generate
pr-123> /post --request-changes
```

## Architecture

```
PR Review Agent (Python CLI)
    ↓
Copilot SDK (AI Reasoning)
    ↓
GitHub API + Local Filesystem
```

## Development Plan

- **Phase 1**: Foundation - Basic chat interface + PR fetching
- **Phase 2**: Context Enhancement - Smart context gathering
- **Phase 3**: Feedback & Commands - Review comment management
- **Phase 4**: Review Generation & Posting
- **Phase 5**: Polish & Extensibility

## Requirements

- macOS
- Python 3.10+
- `gh` CLI (authenticated)
- `git`
- GitHub Copilot license
