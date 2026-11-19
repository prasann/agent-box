# agent-box 🧰

**My personal AI engineering toolkit** — a collection of agents, prompts, skills, and hooks I've built to make working with AI coding assistants faster and more opinionated.

This is my Swiss Army knife: CLI tools for local AI tasks, VS Code agents with well-defined roles, reusable skills for common dev workflows, and hooks to stay informed without context switching.

---

## What's Inside

### 🤖 [`agb/`](agb/README.md) — Local CLI Agents
A Python CLI (`agb`) running fully local AI via Ollama. Private, offline, free.

| Command | What it does |
|---|---|
| `agb text fix` | Fix grammar in clipboard |
| `agb text rewrite` | Rewrite text in clipboard |
| `agb shell purge` | Curate shell history with AI |
| `agb reads search "..."` | Recall saved readings with original-text evidence |
| `agb serve` | Open Control Center, including Reads search and collection controls |

### 🧠 [`vscode-prompts/`](vscode-prompts/README.md) — VS Code Copilot Configuration
Custom agents, skills, prompts, and hooks for GitHub Copilot in VS Code.

**Agents** — Specialized roles with distinct behaviors:
- `AGB - Implementer` — executes tasks, validates, marks done
- `AGB - Spec Planner` — turns requirements into spec + plan
- `AGB - Task Generator` — breaks specs into a task checklist
- `AGB - PR Reviewer` — async PR analysis in a worktree

**Skills** — Reusable building blocks invoked by agents:
`branch-setup` · `code-reviewer` · `comment-manager` · `review-session` · `humanizer`

**Hooks** — macOS notifications on agent lifecycle events ([details](vscode-prompts/.github/hooks/README.md)):
- Get notified when an agent finishes and is waiting for your input
- Repo name in every notification — know which project needs attention
- Click to focus VS Code

---

## Quick Start

```bash
# Clone
git clone https://github.com/prasann/agent-box
cd agent-box

# Local CLI (requires Ollama)
brew install ollama && ollama pull llama3.2:3b
pipx install ./agb

# Personal Copilot skills and agents (VS Code Stable, Insiders, and CLI)
# Run from the repository root.
./install-copilot.sh
./install-copilot.sh --check
```

Optional macOS hooks:
```bash
brew install terminal-notifier
./install-copilot.sh --with-hooks
```

Skills and agents are symlinked from this checkout into native user folders.
No multi-root workspace or editor settings required for the modern Copilot
harness. See [setup, migration, and safety details](vscode-prompts/README.md).

---

Built by [@prasann](https://github.com/prasann) · Personal project
