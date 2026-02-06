````chatskill
# Comment Manager Skill

Manage review comments: present, process user feedback, update states, post to GitHub.

## Input/Output

```json
Input: {
  "action": "present" | "process_feedback" | "post",
  "state_file": ".copilot-tracking/pr-reviews/feature-1234.state.json",
  "user_feedback": "approve all | skip {file}:{line} | revise {file}:{line} - {text} | add comment {file}:{line} - {text}",
  "pr_number": 1234,
  "repository": "owner/repo"
}

Output: {
  "action_taken": "...",
  "pending_count": 0,
  "approved_count": 15,
  "skipped_count": 2,
  "formatted_output": "...",
  "posted_comment_ids": [...]
}
```

## Actions

### 1. Present Comments
Load state, group by severity (CRITICAL/DEFAULT), format using `templates/pr-review/output-formats.md`. Show file:line, comment, suggestion, reference for each.

### 2. Process Feedback

| Command | Action | Response |
|---------|--------|----------|
| `approve all` | Move all pending → approved, set status "approved" | "✅ {count} approved, ready to post" |
| `skip {file}:{line}` | Move to skippedComments, set status "skipped" | "✅ Skipped, {pending_count} remaining" |
| `revise {file}:{line} - {text}` | Store original, update comment, keep in pending, set status "revised" | "✏️ Revised: {original} → {new}" |
| `focus on {severity}` | Filter view by severity (no state change) | Show filtered comments |
| `add comment {file}:{line} - {text}` | Create user comment, add to approved directly | "➕ Added at {file}:{line}" |
| Invalid | N/A | Show valid command list |

Update state file after each command. Set `reviewStatus: "approved"` when no pending remain.

### 3. Post to GitHub
Clean comments (remove file/line refs), post via `create_pull_request_review_comment`. Track results in state (`reviewStatus: "posted"`, `postedAt`, `postedComments[]`, `failedComments[]`). Optionally create PR summary review if CRITICAL issues.

## Error Handling

- State missing/corrupted: Ask to start new or archive
- Command parsing errors: Request full path or show valid commands
- GitHub API errors: Continue with remaining, report failures
- Line no longer exists: Post as PR-level comment

**Tools**: `read_file`, `create_file`, `grep_search`, `github-mcp` (create_pull_request_review_comment, create_pull_request_review)
**Refs**: `templates/pr-review/output-formats.md`, `templates/shared/state-schema.json`, `templates/pr-review/comment-examples.md`
````
