# Agent Box

A collection of standalone AI agents for macOS that run locally and leverage GitHub Copilot for reasoning.

## Current Agents

### [PR Review Agent](agents/pr-review/) (In Development)
Autonomous PR review agent that helps understand, analyze, and review GitHub pull requests through an interactive chat interface.

**Status**: Planning Phase  
**Docs**: [MVP Spec](agents/pr-review/docs/mvp_spec.md) | [Approach](agents/pr-review/docs/approach.md)

## Philosophy

- **Standalone**: Agents run independently without repo pollution
- **Local-first**: All state managed in `~/.config/`, not in repositories
- **Copilot-powered**: Leverage GitHub Copilot SDK for AI reasoning
- **Simple**: Start simple, iterate based on real usage
- **Extensible**: Foundation for multiple specialized agents
- **Personal**: My use-case, my design, my choice!

## Requirements

- macOS
- Python 3.10+
- `gh` CLI (authenticated)
- `git`
- GitHub Copilot license

## Future Agents

- Code quality analyzer
- Security scanner
- Test generator
- Documentation updater

---

**Status**: Planning & Design Phase
