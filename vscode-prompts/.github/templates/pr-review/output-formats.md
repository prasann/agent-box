# Review Output Templates

Standard formats for presenting review information to users. These templates ensure consistent, professional presentation.

## Initial Review Summary

Use this template when first presenting the review session:

```markdown
## PR Review: {branch_name}

📊 **Changes Summary**:
* Branch: {current_branch}
* Files changed: {file_count}
* Additions: +{additions_count} / Deletions: -{deletions_count}
* Commits: {commit_count}

🎯 **Review Focus**:
{focus_description}

📋 **Project Context Loaded**:
* ✅ {convention_category_1}
* ✅ {convention_category_2}
* ✅ {convention_category_3}
{additional_conventions}

Ready to begin review. Would you like me to:
1. Start comprehensive review of all changes
2. Focus on specific files or aspects
3. Review with particular emphasis on {primary_conventions}
```

---

## Analysis Progress Update

Show progress during file-by-file analysis:

```markdown
Analyzing changes... ({current_file_number}/{total_files} files)

📁 Currently reviewing: {file_path}
⚠️  Issues found so far: {issue_count}
```

---

## Pending Comments Presentation

Main template for showing review comments before user approval:

```markdown
## Review Comments (Pending Approval)

I've identified {total_comments} items across {file_count} files. Review these comments before posting:

---

### � CRITICAL Issues ({critical_count})

{for each CRITICAL comment}
#### 📁 {file_path}:{line_number}

**{issue_title}**

{comment_body}

```suggestion
{code_suggestion_if_applicable}
```

**Reference**: {guideline_reference}
**Action**: {required_action}

---
{end for}

---

### 📝 DEFAULT ({default_count})

{for each DEFAULT comment}
#### 📁 {file_path}:{line_number}

**{issue_title}**

{comment_body}

**Suggestion**: {fix_suggestion}
**Reference**: {guideline_reference}

---
{end for}

---

## Summary

* **Total Comments**: {total_comments}
* **Files Reviewed**: {files_reviewed_count}
* **Critical Issues**: {critical_count} (must fix)
* **Default Feedback**: {default_count} (should address)

{if focus_areas_specified}
**Focus Area Compliance**: {focus_findings_summary}
{end if}

---

**Next Steps**:
Review the comments above and provide feedback:
* `"approve all"` - Accept all comments as written
* `"skip {file}:{line}"` - Remove specific comment
* `"revise {file}:{line} - {your feedback}"` - Update comment with your input
* `"focus on {severity}"` - Show only CRITICAL or DEFAULT
* `"add comment {file}:{line} - {text}"` - Add your own comment

Once approved:
* `"finalize"` - Save review locally
* `"post review"` - Post comments to GitHub PR

I'll apply your feedback and prepare the final review.
```

---

## Filtered Comments View

When user requests specific severity level:

```markdown
## {SEVERITY} Priority Comments ({count})

{show only requested severity level using same format as above}

---

**Show all**: To see comments at other severity levels, say "show all comments"
**Approve**: To approve these specific comments, say "approve {severity} comments"
```

---

## Feedback Acknowledgment

After processing user feedback:

```markdown
## Updated Review Status

✅ **Approved**: {approved_count} comments
❌ **Skipped**: {skipped_count} comments  
✏️ **Revised**: {revised_count} comments

{if skipped_count > 0}
**Skipped Comments**:
* {file_1}:{line_1} - {reason}
* {file_2}:{line_2} - {reason}
{end if}

{if revised_count > 0}
**Revisions Applied**:
* {file_1}:{line_1} - Updated based on your feedback
{end if}

---

**Current Pending**: {remaining_pending_count} comments

{if remaining_pending_count > 0}
Would you like to:
1. Review remaining pending comments
2. Approve all remaining comments
3. Make more adjustments
{else}
All comments processed! Ready to prepare final review?
{end if}
```

---

## Final Review Summary

Present complete approved review before user posts manually:

```markdown
## ✅ Final Review Summary

**Overall Assessment**: {APPROVE | REQUEST_CHANGES | COMMENT}

---

### High-Level Summary

{2-3 sentence summary of review, highlighting key findings}

---

### Review Statistics

| Category | Count |
|----------|-------|
| Total Comments | {total_approved} |
| Critical Issues | {critical_count} |
| Default Feedback | {default_count} |
| Files Reviewed | {files_count} |

---

### Detailed Comments

{for each approved comment, grouped by file}
#### {file_path}

{for each comment in this file}
**Line {line_number}**: {severity_badge}  
{comment_text}

{if suggestion_code}
```suggestion
{suggestion_code}
```
{end if}

---
{end for}
{end for}

---

### How to Post This Review

**Option 1: GitHub CLI**
```bash
# Save comments to file
cat > review_comments.json << 'EOF'
{json_formatted_comments}
EOF

# Post review
gh pr review {pr_number} --comment -F review_comments.json
```

**Option 2: GitHub UI**
1. Go to PR #{pr_number} on GitHub
2. Click "Files changed" tab
3. Add comments at specified lines using content above
4. Submit review with "{APPROVE | REQUEST_CHANGES | COMMENT}"

**Option 3: Copy from State File**
```bash
cat .copilot-tracking/pr-reviews/{branch_name}.state.json
```

---

**Review session saved at**: `.copilot-tracking/pr-reviews/{branch_name}.state.json`
```

---

## Resume Session View

When user returns to existing review:

```markdown
## Resuming PR Review: {branch_name}

📊 **Review Status**: {review_status}  
⏱️ **Last Updated**: {last_updated_timestamp}  
📝 **Pending Comments**: {pending_count}  
✅ **Approved Comments**: {approved_count}

---

### Session Context

* **Branch**: {branch_name}
* **Files Analyzed**: {files_reviewed_count}
* **Focus Areas**: {focus_areas_list}

{if pending_count > 0}
**Action Required**: You have {pending_count} comments awaiting approval
{end if}

---

**What would you like to do?**
1. Continue reviewing pending comments
2. Re-analyze changes with fresh perspective
3. Modify focus areas
4. Finalize and prepare review
5. Start new review session
```

---

## Error Messages

### Not on PR Branch

```markdown
❌ **Not on a PR branch**

Current branch: {current_branch}

This doesn't appear to be a PR branch. Please:
1. Check out the PR branch: `git checkout feature/XXXX-description`
2. Restart review: "Review this PR"
```

### Uncommitted Changes

```markdown
⚠️ **Uncommitted changes detected**

Working directory has modified files:
{list_of_modified_files}

**Recommendation**: Commit or stash changes before review to ensure clean diff:
* `git add . && git commit -m "..."`  
* `git stash`

Proceed anyway? (Review will include uncommitted changes)
```

### Large PR Warning

```markdown
⚠️ **Large PR detected**

* Lines changed: {total_lines} (>{threshold})
* Files changed: {file_count} (>{threshold})

**Recommendation**: 
* Review in phases by focus area
* Consider breaking into smaller PRs

Proceed with full review or select focus area?
```

### Missing Project Context

```markdown
⚠️ **Limited project context**

Could not find some expected guideline files:
{list_missing_files}

Review will proceed with available conventions but may miss project-specific standards.
```

---

## Compact Summary View

For quick status checks:

```markdown
## Review Status: {branch_name}

| Metric | Value |
|--------|-------|
| Status | {status} |
| Comments | {total} ({critical}C / {default}D) |
| Files | {count} |
| Approved | {approved_count} |
| Pending | {pending_count} |

**Next Action**: {next_recommended_action}
```

---

## Variable Reference

Template variables used across formats:

**Branch/Commit Info**:
- `{branch_name}` - Current git branch
- `{pr_number}` - PR number (if extracted)
- `{commit_count}` - Number of commits
- `{additions_count}` / `{deletions_count}` - Line changes

**File Stats**:
- `{file_count}` - Total files changed
- `{files_reviewed_count}` - Files analyzed so far
- `{file_path}` - Specific file path
- `{line_number}` - Line number for comment

**Comment Stats**:
- `{total_comments}` - Total review comments
- `{critical_count}` / `{high_count}` / `{medium_count}` / `{low_count}` - By severity
- `{approved_count}` / `{pending_count}` / `{skipped_count}` / `{revised_count}` - By status

**Review Data**:
- `{severity_badge}` - CRITICAL / HIGH / MEDIUM / LOW
- `{comment_body}` - Comment text content
- `{suggestion_code}` - Code suggestion block
- `{guideline_reference}` - Link to project convention
- `{focus_description}` - User-specified focus areas

**Timestamps**:
- `{review_started}` - Session start time
- `{last_updated_timestamp}` - Last state update

**Assessment**:
- `{review_status}` - in-progress / pending-approval / approved / posted
- `{APPROVE | REQUEST_CHANGES | COMMENT}` - Overall recommendation
