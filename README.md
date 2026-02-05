# Agent Box

A personal collection of AI-powered productivity agents and development tools. Built around a unified CLI (`agb`) that brings local AI capabilities to everyday tasks.

## 🚀 What's This?

A single command-line tool that provides multiple AI agents for personal productivity:

```bash
agb text fix          # Fix grammar and typos in clipboard
agb text rewrite      # Rewrite text for clarity
# More agents coming...
```

**Key Features:**
- 🧠 **100% Local AI**: All processing via Ollama (private, fast, no cloud)
- 📦 **Unified Tool**: One installation, multiple agents
- ⚡ **Fast**: 1-2 seconds per request with local models
- 🎯 **Purpose-Built**: Agents designed for my specific workflows

## 📁 Project Structure

### [agb/](agb/) - Unified Agent System
The main implementation - a Python package providing the `agb` CLI with multiple AI agents.

**✅ Currently Implemented:**
- **Text Agent**: Grammar/typo checker and text rewriter
  - `agb text fix` - Minimal corrections preserving style
  - `agb text rewrite` - Full rewrite for clarity and professionalism

**🚧 Coming Soon:**
- Gmail spam classifier
- Additional productivity agents

See [agb/README.md](agb/README.md) for full documentation.

### [vscode-prompts/](vscode-prompts/)
VS Code prompts and GitHub Copilot configurations for development tasks.

See [vscode-prompts/README.md](vscode-prompts/README.md) for available prompts.

### [ideas/](ideas/)
Planning documents and approach notes for future agents.

## 🎯 Quick Start

### Prerequisites

```bash
# Install and start Ollama
brew install ollama
ollama serve

# Pull a model
ollama pull llama3.2:3b
```

### Installation

```bash
# From the agb directory
cd agb/
pipx install .
```

### Usage

```bash
# Fix grammar in clipboard text
# 1. Copy text (Cmd+C)
# 2. Run:
agb text fix
# 3. Paste result (Cmd+V)

# Rewrite text for clarity
agb text rewrite

# Skip preview for speed
agb text fix --no-preview

# Get help
agb --help
agb text --help
```

## 💡 Philosophy

This is my personal productivity toolkit - not a product or open-source project seeking contributions. Built for:

- **My workflows**: Agents designed around how I work
- **Local-first**: Privacy and speed over cloud features
- **Simplicity**: Minimal dependencies, maximum utility
- **Experimentation**: Testing AI capabilities in real workflows

**Note**: Feel free to browse and fork if something here is useful to you, but this repository is maintained exclusively for my personal use cases.

## 📚 Documentation

- **[agb/README.md](agb/README.md)** - Complete CLI documentation, configuration, and development guide
- **[agb/IMPLEMENTATION.md](agb/IMPLEMENTATION.md)** - Technical implementation details
- **[plan.md](plan.md)** - Original planning document

## 🔧 Architecture

```
agb (CLI command)
├── text agent       ✅ Working
│   ├── fix         - Grammar/typo corrections
│   └── rewrite     - Full text rewrite
├── gmail agent      🚧 Planned
└── [more agents]    💡 Ideas
```

Built on shared infrastructure:
- **Ollama Client**: Unified LLM interface with retry logic
- **Configuration**: Environment-based settings with Pydantic
- **Rich Output**: Beautiful terminal UI with previews
- **Extensible**: Add new agents in 3 steps

## 🛠️ Tech Stack

- **Python 3.10+** with modern tooling
- **Ollama** for local LLM inference
- **Click** for CLI framework
- **Rich** for terminal UI
- **Pydantic** for settings and validation

## 📊 Status

- ✅ Core infrastructure implemented
- ✅ Text agent fully working
- ✅ Configuration system in place
- ✅ CLI with help system
- 🚧 Gmail agent in planning
- 💡 More agents being explored

## 🔮 Future Ideas

See [ideas/](ideas/) for agent concepts in various stages:
- Gmail spam classifier with AI-powered categorization
- Additional text processing agents
- Development workflow enhancements

---

*Last Updated: February 2026*
