````chatskill
# Comment Manager Skill

Manage the review comment workflow, including user feedback processing, comment state transitions, and final review preparation.

## Purpose

This skill handles the interactive workflow after comments are generated:
1. Present pending comments to user for approval
2. Parse and process user feedback commands
3. Update comment states (approve, skip, revise)
4. Manage state file lifecycle
5. Format final review output
6. Post approved comments to GitHub PR via MCP

## Invocation

**When**: After code analysis completes, and when processing user feedback

**Input**:
```json
{
  "action": "present" | "present_one_by_one" | "process_feedback" | "finalize" | "post",
  "state_file": ".copilot-tracking/pr-reviews/feature-1234.state.json",
  "user_feedback": "approve all" | "skip" | "revise - {feedback}" | "approve" | "next",
  "pr_number": 1234,
  "repository": "owner/repo",
  "current_comment_index": 0,
  "review_mode": "all_at_once" | "one_by_one"
}
```

**Output**:
```json
{
  "success": true,
  "action_taken": "approved_all" | "updated_comments" | "finalized" | "posted",
  "pending_count": 0,
  "approved_count": 15,
  "skipped_count": 2,
  "revised_count": 1,
  "formatted_output": "<markdown-content>",
  "posted_comment_ids": [123, 456, 789]  // if action was "post"
}
```

## Implementation Steps

### Action 1a: Present All Comments at Once

**When**: `action: "present"` with `review_mode: "all_at_once"`

**Load state file**:
- Read from `state_file` path
- Validate against schema
- Extract `pendingComments` array

**Group comments**:
- By severity: CRITICAL, DEFAULT
- Count per severity level
- Count per file

**Format presentation** using `templates/pr-review/output-formats.md` → "Pending Comments Presentation":

```markdown
## Review Comments (Pending Approval)

I've identified {total} items across {file_count} files. Review these comments before posting:

---

### 🚨 CRITICAL Issues ({count})

{for each CRITICAL comment}
#### 📁 {file}:{line}

**{comment.comment first line}**

{comment.comment body}

```suggestion
{comment.suggestion if exists}
```

**Reference**: {comment.reference}
**Action**: {required action}
---
{end for}

---

### 📋 DEFAULT ({count})

{for each DEFAULT comment}
#### 📁 {file}:{line}

**{comment.comment first line}**

{comment.comment body}

**Suggestion**: {comment.suggestion if exists}
**Reference**: {comment.reference}
---
{end for}

---

## Summary

* **Total Comments**: {total}
* **Files Reviewed**: {count}
* **Critical**: {count} (must fix)
* **Default**: {count} (feedback)

---

**Next Steps**:
Review comments and provide feedback:
* "approve all" - Accept all comments
* "skip {file}:{line}" - Remove specific comment
* "revise {file}:{line} - {feedback}" - Update comment
* "focus on {severity}" - Show only CRITICAL/HIGH/MEDIUM/LOW
* "add comment {file}:{line} - {text}" - Add your comment
```

**Return**: Formatted markdown output

---

### Action 2: Process User Feedback

**When**: `action: "process_feedback"`

**Parse feedback command**:

#### Command: "approve all" (or "approve all remaining" in one-by-one mode)
**Action**:
- Move all `pendingComments` → `approvedComments`
- Set each comment's `status` to "approved"
- Clear `pendingComments` array
- Update state file

**Response**:
```markdown
## ✅ All Comments Approved

{approved_count} comments approved and ready for posting.

Say "post review" to post to GitHub, or "finalize" to save locally.
```

#### Command: "approve" (in one-by-one mode)
**Action**:
- Move current comment from `pendingComments` → `approvedComments`
- Set comment's `status` to "approved"
- Increment `current_comment_index`
- Update state file
- If more pending: Show next comment
- If none pending: Show completion message

**Response**: Next comment or completion message

#### Command: "skip" (in one-by-one mode) or "skip {file}:{line}" (in all-at-once mode)
**Parse**: 
- One-by-one: Use current comment
- All-at-once: Extract file path and line number

**Action**:
- Find/use comment in `pendingComments`
- Move to `skippedComments` with `skipReason: "User requested"`
- Set comment's `status` to "skipped"
- If one-by-one: Increment index, show next comment
- Update state file

**Response**:
```markdown
## ✅ Comment Skipped

{if all_at_once}
Removed comment at {file}:{line}
{end if}

Remaining pending: {pending_count}

{if one_by_one and has_next}
[Shows next comment]
{end if}
```

#### Command: "revise - {user_feedback}" (in one-by-one mode) or "revise {file}:{line} - {feedback}" (all-at-once)
**Parse**: 
- One-by-one: Use current comment + extract feedback
- All-at-once: Extract file, line, and feedback

**Action**:
- Find/use comment in `pendingComments`
- Store original: `originalComment: <original text>`
- Store reason: `revisionReason: <user feedback>`
- Update comment text based on user feedback
- Keep in `pendingComments` for approval
- Set comment's `status` to "revised"
- If one-by-one: Show revised comment again for approval
- Update state file

**Response**:
```markdown
## ✏️ Comment Revised

{if all_at_once}
Updated comment at {file}:{line} based on your feedback.
{end if}

**Original**: {original comment snippet}
**Revised**: {new comment snippet}

{if one_by_one}
Review the revised comment:
[Shows same comment with updated text]
{else}
Review and approve when ready.
{end if}
```

#### Command: "focus on {severity}"
**Parse**: Extract severity level (CRITICAL, HIGH, MEDIUM, LOW)

**Action**:
- Filter `pendingComments` by severity
- Don't modify state file (just a view)

**Response**: Use `templates/pr-review/output-formats.md` → "Filtered Comments View"

#### Command: "add comment {file}:{line} - {text}"
**Parse**: Extract file, line, and comment text

**Action**:
- Create new comment object:
```json
{
  "id": "comment-user-1",
  "file": "<file>",
  "line": <line>,
  "severity": "MEDIUM",
  "category": "custom",
  "comment": "<user text>",
  "suggestion": null,
  "reference": "User-added",
  "status": "approved"
}
```
- Add directly to `approvedComments` (user-added comments skip pending)
- Update state file

**Response**:
```markdown
## ➕ Comment Added

Added your comment at {file}:{line}

This comment will be included in the final review.
```

#### Invalid command
**Detection**: Command doesn't match any pattern

**Response**:
```markdown
❌ **Unrecognized command**

Valid commands:
* "approve all"
* "skip {file}:{line}"
* "revise {file}:{line} - {feedback}"
* "focus on {severity}"
* "add comment {file}:{line} - {text}"

Please try again.
```

**Update state file** after all feedback processing:
- Write updated comments arrays
- Set `lastUpdated` timestamp
- If no pending comments remain: Set `reviewStatus: "approved"`

**Generate acknowledgment** using `templates/pr-review/output-formats.md` → "Feedback Acknowledgment"

### Action 3: Post to GitHub

**When**: `action: "post"`

**Clean comment text** before posting:
- Remove file path/line references (GitHub shows them)
- Remove "At line X:" prefixes
- Keep CRITICAL badge, core message, suggestion, reference

**Post each comment**:
```
GitHub MCP: create_pull_request_review_comment
Parameters:
- body: {cleaned_comment_text}
- path: {comment.file}
- line: {comment.line}
- side: "RIGHT"
- commit_id: {latest_commit_sha}
```

**Optional PR summary** (only if requested OR CRITICAL issues):
```
GitHub MCP: create_pull_request_review
Parameters:
- event: "REQUEST_CHANGES" | "COMMENT"
- body: {2-3 sentence summary}
```

**Track results**:
- Update state: `reviewStatus: "posted"`, `postedAt`, `postedComments[]`, `failedComments[]`
- Return posting summary with success/failure counts, PR link

## Error Handling

**State file issues**:
- Missing: Ask user to start new review
- Corrupted: Archive and start fresh

**Command parsing**:
- Ambiguous file reference: Ask for full path
- Line not found: Show active comment locations
- Invalid command: Show valid command list

**Validation**:
- Pending comments remain: Ask to approve/skip or force finalize
- Empty review: Suggest re-analyze or add manual comments

**GitHub posting**:
- Auth error: Suggest configuration or manual posting
- API error: Continue with remaining, report failures
- Line no longer exists: Try as PR-level comment

## Tools

`read_file`, `create_file`, `grep_search`, `github/github-mcp/create_pull_request_review_comment`, `github/github-mcp/create_pull_request_review`

## References

- `templates/pr-review/output-formats.md`
- `templates/shared/state-schema.json`
- `templates/pr-review/comment-examples.md`

````
