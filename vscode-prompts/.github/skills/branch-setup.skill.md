````chatskill
# Branch Setup Skill

Create feature branch and specs folder structure for new work.

## Purpose

Handle git branch creation and folder setup:
1. Generate appropriate branch name
2. Create and checkout branch
3. Create `specs/<feature-name>/` directory
4. Return paths for spec files

## Input

```json
{
  "feature_name": "user-authentication",
  "story_number": "1234",  // optional
  "base_branch": "main"     // optional, defaults to "main"
}
```

## Output

```json
{
  "success": true,
  "branch_name": "feature/1234-user-authentication",
  "spec_dir": "specs/user-authentication",
  "files": {
    "spec": "specs/user-authentication/spec.md",
    "plan": "specs/user-authentication/plan.md",
    "tasks": "specs/user-authentication/tasks.md"
  }
}
```

## Logic

### 1. Generate Branch Name

```
If story_number provided:
  branch_name = "feature/{story_number}-{feature_name}"
Else:
  branch_name = "feature/{feature_name}"

Normalize feature_name:
  - Lowercase
  - Replace spaces with hyphens
  - Remove special chars
  - Max 50 chars
```

**Examples**:
- `feature_name="User Auth", story_number="1234"` → `feature/1234-user-auth`
- `feature_name="Add Payment Flow"` → `feature/add-payment-flow`

### 2. Check Branch Exists

```bash
git rev-parse --verify $branch_name 2>/dev/null
```

**If exists**: Ask user "Branch exists. Use it or create new name?"
**If not exists**: Proceed

### 3. Create and Checkout Branch

```bash
git checkout -b $branch_name
```

**Error handling**:
- Uncommitted changes: Suggest stash or commit
- No git repo: Error, can't proceed
- Detached HEAD: Suggest checking out base branch first

### 4. Create Specs Directory

```bash
mkdir -p specs/$feature_name
```

**Structure**:
```
specs/
└── user-authentication/
    ├── spec.md      (to be created by agent)
    ├── plan.md      (to be created by agent)
    └── tasks.md     (to be created by agent)
```

### 5. Return Paths

Return absolute paths for all three files.

## Error Handling

- **Not a git repo**: "No git repository found. Initialize git first?"
- **Dirty working tree**: "You have uncommitted changes. Commit, stash, or continue anyway?"
- **Branch exists**: "Branch already exists. Options: 1) Use existing, 2) Delete and recreate, 3) Create with different name"
- **Permission denied**: "Can't create directory. Check permissions."

## Tools

`run_in_terminal`, `create_directory`

## Example Usage

```json
Input:
{
  "feature_name": "user authentication",
  "story_number": "1234"
}

Commands run:
$ git checkout -b feature/1234-user-authentication
$ mkdir -p specs/user-authentication

Output:
{
  "success": true,
  "branch_name": "feature/1234-user-authentication",
  "spec_dir": "specs/user-authentication",
  "files": {
    "spec": "specs/user-authentication/spec.md",
    "plan": "specs/user-authentication/plan.md",
    "tasks": "specs/user-authentication/tasks.md"
  }
}
```
````
