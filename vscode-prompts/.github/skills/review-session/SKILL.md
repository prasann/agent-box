---
name: review-session
description: |
  Initialize PR review session. Detects git context (branch, PR number, changed files),
  loads repository conventions and instructions, creates state file for tracking.
  Use at the start of a PR review to set up the review context.
---

# Review Session Skill

Initialize PR review session: detect git context, load conventions, create state.

## Input/Output

```json
Input: {
  "focus_areas": ["testing", "security"],  // optional
  "resume": false                          // optional
}

Output: {
  "branch": "feature/1234-description",
  "pr_number": 1234,
  "files_changed": [...],
  "conventions": { "loaded_files": [...], "critical_rules": [...] },
  "state_file": ".copilot-tracking/pr-reviews/<branch>.state.json"
}
```

## Steps

1. **Detect Git Context**: Current branch, PR number, commits, diff stats. Use `changes` tool.
2. **Load Conventions**: Read `.github/copilot-instructions.md`, `code-and-documentation-hygiene.instructions.md`, `testing.instructions.md`, `code-structure.instructions.md`, README. Extract MUST/SHOULD rules.
3. **State File**: Create/resume `.copilot-tracking/pr-reviews/<branch>.state.json`. Ask to resume if exists.
4. **Present Summary**: Show branch, file count, diff stats, loaded conventions. Warn if large PR (>20 files/500 lines).

## Error Handling

- Not PR branch / uncommitted changes / missing origin: Warn and guide user
- State corruption: Archive, start fresh
- Permission denied: Proceed in-memory

**Tools**: `runCommands`, `changes`, `read_file`, `create_file`, `list_dir`
**Refs**: `templates/shared/state-schema.json`, `templates/pr-review/output-formats.md`
