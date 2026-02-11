# Agent Box

Personal AI productivity agents running 100% local via Ollama.

```bash
agb text fix          # Fix grammar in clipboard
agb text rewrite      # Rewrite text
findtab search "..."  # Search browser history by meaning
```

## What's Inside

### [agb/](agb/) - CLI Agents
Python package with multiple AI agents. See [agb/README.md](agb/README.md) for details.

**Current agents:**
- Text Agent - Grammar fixes and rewrites
- Find That Tab - Browser history search

### [vscode-prompts/](vscode-prompts/) - GitHub Copilot Prompts
Agent definitions and skills for VS Code. Mount as multi-root workspace to access in any project.

See [vscode-prompts/README.md](vscode-prompts/README.md) for usage.

## Quick Start

```bash
# Prerequisites
brew install ollama
ollama serve
ollama pull llama3.2:3b

# Install CLI
cd agb/
pipx install .

# Or use xbar plugin for menu bar access
./install-xbar.sh
```

## Usage

**CLI:**
```bash
agb text fix          # Copy text, run this, paste result
findtab index         # Index browser history
findtab search "..."  # Search by meaning
```

**Menu bar (xbar):**
1. Copy text (Cmd+C)
2. Click 🤖 → "Fix Grammar"
3. Paste result (Cmd+V)

See [xbar/README.md](xbar/README.md) for setup.

---

Personal project. Not accepting contributions.
