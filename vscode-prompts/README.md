# VS Code Prompts

My personal collection of VS Code prompt configurations and GitHub Copilot agent definitions.

> **Note**: These prompts are tailored to my specific workflows and not designed for general use.

## Current Prompts

### PR Review Prompts
Located in `.github/` directory:

#### Agents
- **[pr-reviewer.agent.md](.github/agents/pr-reviewer.agent.md)** - PR review agent configuration

#### Skills
- **[comment-manager.skill.md](.github/skills/comment-manager.skill.md)** - Managing PR review comments
- **[review-session.skill.md](.github/skills/review-session.skill.md)** - Review session management
- **[code-reviewer.skill.md](.github/skills/code-reviewer.skill.md)** - Code review assistance

#### Templates
Located in `.github/templates/`:
- **pr-review/** - PR review specific templates
  - `output-formats.md` - Standard output formats for reviews
  - `severity-guidelines.md` - Issue severity classification
  - `comment-examples.md` - Example review comments
- **shared/** - Shared configurations
  - `state-schema.json` - State management schema

## Usage

These prompts can be used with VS Code and GitHub Copilot to enhance your development workflow. Each prompt/agent is designed for specific tasks and follows consistent patterns.

## Structure

```
.github/
├── agents/         # Agent definitions
├── skills/         # Skill modules
└── templates/      # Reusable templates
```

## Adding New Prompts

When adding new prompts:
1. Choose appropriate directory (agents, skills, or templates)
2. Follow existing naming conventions
3. Update this README with a brief description
4. Include inline documentation in the prompt file
