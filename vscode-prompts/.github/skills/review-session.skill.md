````chatskill
# Review Session Initialization Skill

Initialize PR review session by detecting local git context and loading project conventions.

## Purpose

This skill handles the setup phase of a PR review:
1. Detect current branch and git status
2. Get list of changed files with diffs
3. Load project conventions and guidelines
4. Create or resume review session state file
5. Present initial review summary

## Invocation

**When**: User starts a new review or resumes an existing one

**Input**:
```json
{
  "focus_areas": ["testing", "security"],  // Optional: specific areas to focus on
  "resume": false                          // Optional: resume existing session if true
}
```

**Output**:
```json
{
  "success": true,
  "branch": "feature/1234-description",
  "pr_number": 1234,
  "files_changed": ["src/example.py", "tests/test_example.py"],
  "commit_count": 5,
  "additions": 120,
  "deletions": 45,
  "conventions": {
    "loaded_files": [".github/instructions/testing.instructions.md"],
    "critical_rules": ["No unused imports", "TDD required"]
  },
  "state_file": ".copilot-tracking/pr-reviews/feature-1234-description.state.json",
  "session_status": "initialized"
}
```

## Implementation

### 1. Detect Git Context

```bash
git status --porcelain  # Warn if uncommitted changes
git branch --show-current  # Extract PR number from branch name
git log --oneline origin/main..HEAD  # Count commits
```

Use `changes` tool for file list and diff stats.

### 2. Load Project Conventions

Read in priority order:
1. `.github/copilot-instructions.md`
2. `.github/instructions/code-and-documentation-hygiene.instructions.md`
3. `.github/instructions/testing.instructions.md`
4. `.github/instructions/code-structure.instructions.md`
5. `README.md`, constitution, other conventions

Extract MUST/SHOULD requirements and zero-tolerance rules. Filter to focus areas if specified.

### 3. Create/Resume State File

**Path**: `.copilot-tracking/pr-reviews/<branch-name>.state.json`

**Resume**: If state exists, ask "Resume or start fresh?"
**New**: Create directory, initialize state from `templates/shared/state-schema.json`

**Validate**: Warn if large PR (>20 files/500 lines), missing conventions, or can't extract PR number.

### 4. Present Summary

Use template from `templates/pr-review/output-formats.md` → "Initial Review Summary"

## Error Handling

- **Not PR branch**: Ask user to checkout PR branch
- **Uncommitted changes**: Warn, ask to commit/stash/proceed
- **Missing origin/main**: Try alternative bases, ask user if needed
- **State corruption**: Archive, start fresh
- **Permission errors**: Suggest fix or proceed in-memory

## Tools

`runCommands`, `changes`, `read_file`, `create_file`, `list_dir`

## References

- `templates/shared/state-schema.json`
- `templates/pr-review/output-formats.md`

````
