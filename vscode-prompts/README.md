# VS Code Prompts

GitHub Copilot agent definitions, skills, and hooks for development workflows.

## Setup

**Global configuration (recommended for hooks):**  
Configure VS Code to load hooks from this toolkit across all projects:

```json
// User Settings (Cmd+Shift+P → Preferences: Open User Settings JSON)
{
  "chat.hookFilesLocations": {
    "~/.agent-box-toolkit/hooks": true
  }
}
```

Then run the installer from the repo root:
```bash
./install-hooks.sh
```

**Multi-root workspace approach (for agents/skills):**  
Mount this folder in any project to access agents and skills.

```json
// .code-workspace file
{
  "folders": [
    { "path": "/path/to/your/project" },
    { "path": "/path/to/agent-box/vscode-prompts" }
  ]
}
```

Or add to existing workspace: File → Add Folder to Workspace → Select `vscode-prompts/`

## Available Prompts

**Agents** (`.github/agents/`):
- `agb.implementer.agent.md` - Code implementation
- `agb.pr-reviewer.agent.md` - PR review 
- `agb.spec-planner.agent.md` - Spec planning
- `agb.task-generator.agent.md` - Task generation

**Skills** (`.github/skills/`):
- `branch-setup/` - Git branch management
- `code-reviewer/` - Code review assistance
- `comment-manager/` - PR comment handling
- `review-session/` - Review sessions
- `humanizer/` - Remove AI writing patterns

**Hooks** (`.github/hooks/`):
- Native macOS system notifications for agent lifecycle events
- Session start/stop, subagent tracking, prompt submission alerts
- See [.github/hooks/README.md](.github/hooks/README.md) for setup

**Agents and Skills:**
Once mounted in a multi-root workspace, these are available in VS Code's GitHub Copilot with `@` mentions.

Example: `@AGB - Implementer execute the tasks`

**Hooks:**
Hooks are loaded globally and run automatically on agent lifecycle events. No explicit invocation needed.

## Usage

Once mounted, these prompts are available in VS Code's GitHub Copilot with `#file:` references.

Example: `#file:.github/ag ents/ab.pr-reviewer.agent.md`
