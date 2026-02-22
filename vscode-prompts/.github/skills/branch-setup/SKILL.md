---
name: branch-setup
description: |
  Create feature branch and specs folder structure. Use when starting a new feature
  to automatically create a git branch and initialize the specs directory with
  spec.md, plan.md, and tasks.md files.
---

# Branch Setup Skill

Create feature branch and specs folder structure.

## Input/Output

```json
Input: {
  "feature_name": "user-authentication",
  "story_number": "1234",  // optional
  "base_branch": "main"    // optional
}

Output: {
  "branch_name": "feature/1234-user-authentication",
  "spec_dir": "specs/user-authentication",
  "files": { "spec": "...", "plan": "...", "tasks": "..." }
}
```

## Steps

1. **Generate branch name**: `feature/{story_number?}-{normalized_name}` (lowercase, hyphens, max 50 chars)
2. **Check exists**: If exists, ask user to use/rename
3. **Create branch**: `git checkout -b $branch_name`
4. **Create specs**: `mkdir -p specs/$feature_name` with spec.md, plan.md, tasks.md
5. **Return paths**: Absolute paths to all files

## Error Handling

- Uncommitted changes: Suggest stash/commit
- Not git repo: Can't proceed
- Branch exists: Offer use/delete/rename
- Permission denied: Check permissions

**Tools**: `run_in_terminal`, `create_directory`
