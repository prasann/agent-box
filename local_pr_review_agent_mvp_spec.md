# Local PR Review Agent (MVP)

## 1. Goal
Build a **local, CLI-first PR review agent** that runs on macOS, leverages an existing **GitHub Copilot paid license**, and helps the user:
- Understand what a PR actually does (beyond description)
- Interactively ask questions about the PR
- Accumulate review feedback across a session
- Review and approve comments before posting to GitHub

The agent **must not require any code or config to be committed to the repository**.

---

## 2. Non-Goals (MVP Scope Control)
- No autonomous auto-posting of comments
- No background daemons
- No multi-user support
- No full semantic indexing of the repo
- No tight coupling to VSCode APIs (CLI is source of truth)

---

## 3. High-Level Architecture

```
VSCode / Terminal
        ↓
CLI Agent (pr-agent)
        ↓
Local State (filesystem)
        ↓
Copilot CLI (reasoning)
        ↓
GitHub (read via gh, write via MCP or gh)
```

Key principle:
> **CLI owns logic and state; editors only invoke it**

---

## 4. Execution Model

### Invocation
From any GitHub repo root:

```bash
pr-agent review <PR_NUMBER>
```

Optional future flags (not required for MVP):
```bash
--focus-file <path>
--focus-area <string>
```

---

## 5. Dependencies (MVP)

### Required
- macOS
- `git`
- `gh` (GitHub CLI, authenticated)
- GitHub Copilot CLI (authenticated, paid license)

### Optional (later)
- GitHub MCP (for posting comments from VSCode)

---

## 6. Directory Layout (Local Only)

```
~/.local/bin/pr-agent
~/.config/pr-agent/
~/.cache/pr-agent/
  └── sessions/
      └── <repo>/<pr-number>/
          ├── pr_meta.json
          ├── diff.txt
          ├── summary.md
          ├── qa.log
          ├── feedback.json
          └── review_draft.md
```

No files are written inside the GitHub repo.

---

## 7. Core Workflow (MVP)

### Step 1: Repo & PR Detection

**Inputs**
- Current working directory
- PR number

**Derived**
- Repo owner/name (from `.git/config`)
- Default branch

**Implementation**
- `git rev-parse --show-toplevel`
- `gh repo view`

---

### Step 2: PR Ingestion (Read-only)

Fetch and store:
- PR metadata (title, description, author)
- File list
- Unified diff

Artifacts:
- `pr_meta.json`
- `diff.txt`

No LLM involved yet.

---

### Step 3: PR Understanding (Copilot Call #1)

**Input**
- PR diff
- File list
- High-level repo hints (README if present)

**Output**
- Functional summary of changes
- High-level mapping of affected areas

Stored as:
- `summary.md`

---

### Step 4: Interactive Session Loop

User can:
- Ask questions about the PR
- Request explanations or snippets
- Provide feedback (not posted yet)

#### Q&A Mode
- Agent selects relevant diff snippets
- Sends focused prompt to Copilot
- Displays answer
- Appends to `qa.log`

#### Feedback Capture
When user says things like:
- "This needs to be changed"
- "This logic is incorrect"

Agent creates a structured entry:

```json
{
  "file": "path/to/file",
  "lines": "120-145",
  "issue": "description",
  "severity": "blocking | suggestion",
  "notes": "optional"
}
```

Stored in:
- `feedback.json`

---

### Step 5: Review Synthesis (Copilot Call #2)

**Input**
- All accumulated feedback

**Output**
- Clean, grouped review comments
- GitHub-ready wording

Stored as:
- `review_draft.md`

User can:
- Edit
- Remove
- Reclassify comments

---

### Step 6: Posting Review (Manual Approval)

User explicitly triggers posting:

```bash
pr-agent post
```

Implementation options:
- `gh pr review --comment`
- GitHub MCP (preferred when invoked from VSCode)

No auto-posting in MVP.

---

## 8. Copilot CLI Usage Strategy

- Treat Copilot as a **stateless reasoning engine**
- Multiple small, scoped calls
- No long-running conversations inside Copilot

Agent is responsible for:
- Context selection
- State persistence
- Safety checks

---

## 9. Error Handling (MVP)

- Missing auth → clear message
- Invalid PR number → exit early
- Copilot failure → retry or degrade gracefully

No silent failures.

---

## 10. Extensibility (Post-MVP)

Designed to allow:
- Multiple agents sharing the same runtime
- Additional review lenses (security, perf, etc.)
- VSCode UI overlays
- MCP-first GitHub interactions

---

## 11. Success Criteria (MVP)

- Can run from terminal or VSCode
- Produces meaningful PR summaries
- Supports interactive Q&A
- Accumulates review feedback
- Posts comments only after explicit approval
- Zero repo pollution

---

## 12. Summary

This MVP delivers a **personal, stateful PR review agent** that:
- Leverages GitHub Copilot effectively
- Respects developer control
- Lives entirely on the local machine
- Scales naturally to future helper agents

Focus is correctness, clarity, and developer trust — not automation for its own sake.

