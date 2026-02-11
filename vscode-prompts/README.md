# VS Code Prompts

GitHub Copilot agent definitions and skills for development workflows.

## Setup

**Multi-root workspace approach:**  
Mount this folder in any project to access these prompts.

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

**Agents:**
- `ab.implementer.agent.md` - Code implementation
- `ab.pr-reviewer.agent.md` - PR review 
- `ab.spec-planner.agent.md` - Spec planning
- `ab.task-generator.agent.md` - Task generation

**Skills:**
- `branch-setup.skill.md` - Git branch management
- `code-reviewer.skill.md` - Code review assistance
- `comment-manager.skill.md` - PR comment handling
- `review-session.skill.md` - Review sessions  

**Templates:**
- `pr-review/` - PR review formats and guidelines
- `shared/` - Shared schemas

## Usage

Once mounted, these prompts are available in VS Code's GitHub Copilot with `#file:` references.

Example: `#file:.github/ag ents/ab.pr-reviewer.agent.md`
