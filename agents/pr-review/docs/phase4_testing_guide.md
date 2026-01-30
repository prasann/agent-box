# Phase 4 Testing Guide

## Overview
Phase 4 implements review generation and posting to GitHub. This guide describes how to test the new features.

## New Features

### 1. Review Generation (`/generate`)
- **What it does**: Synthesizes all collected feedback items into a structured GitHub review
- **Output**: Formatted markdown review with summary and detailed feedback
- **Side effect**: Saves draft to `review_draft.md` in session directory

**Test Steps**:
```bash
# 1. Start a review session
pr-agent review 123

# 2. Add some feedback
pr-123> /feedback src/main.py:45 critical Missing null check
pr-123> /feedback src/utils.js:20-25 suggestion Consider using const instead of let

# 3. Generate review
pr-123> /generate
```

**Expected Output**:
- Markdown-formatted review with:
  - Summary section with severity counts
  - Assessment based on severity (Critical/Important/Minor)
  - Detailed feedback grouped by file
  - Each feedback item with emoji indicators
  - Timestamp footer

### 2. Review Preview (`/preview`)
- **What it does**: Shows complete review preview with decision suggestion
- **Output**: Full formatted preview with review decision (APPROVE/REQUEST_CHANGES/COMMENT)

**Test Steps**:
```bash
pr-123> /preview
```

**Expected Output**:
```
================================================================================
REVIEW PREVIEW - Decision: ❌ REQUEST CHANGES
================================================================================

## Review Summary

⚠️ **Critical issues found** - Please address before merging

**Total feedback items**: 2
- 🔴 Critical: 1
- 🟡 Important: 0
- 💡 Suggestions: 1
- ❓ Questions: 0

## Detailed Feedback

### `src/main.py`
...
================================================================================
```

### 3. Review Editor (`/edit`)
- **What it does**: Opens review draft in your text editor
- **Editor**: Uses `$EDITOR` environment variable (defaults to vim)

**Test Steps**:
```bash
# Set editor if needed
export EDITOR=nano  # or vim, code, etc.

# Edit review
pr-123> /edit
```

**Expected Behavior**:
- Opens `review_draft.md` in configured editor
- Changes are saved to the file
- Can be previewed again with `/preview`
- Edited version is used when posting with `/post`

### 4. Post Review (`/post`)
- **What it does**: Posts review to GitHub using gh CLI
- **Actions**: `approve`, `request-changes`, `comment`, `auto` (suggested based on severity)

**Test Steps**:
```bash
# Test with auto-suggested action
pr-123> /post auto

# Test with specific action
pr-123> /post comment

# Test with request changes
pr-123> /post request-changes
```

**Expected Behavior**:
1. Shows full review preview
2. Displays suggested/selected action
3. Shows PR info for confirmation
4. Prompts: "Continue? (yes/no):"
5. Posts to GitHub via `gh pr review`
6. Shows success message with review URL
7. Marks session as "review_posted"

**Safety Features**:
- Requires "yes" to confirm (not just "y")
- Shows full preview before posting
- Checks gh authentication first
- Clear error messages if posting fails

## Review Decision Logic

The system automatically suggests review actions based on feedback severity:

| Severity | Count | Suggested Action |
|----------|-------|------------------|
| Critical | >= 1 | REQUEST_CHANGES |
| Important | >= 3 | REQUEST_CHANGES |
| Any other | - | COMMENT |
| No feedback | - | APPROVE |

## Testing Checklist

### Basic Workflow
- [ ] Add feedback items with different severities
- [ ] Generate review with `/generate`
- [ ] Preview shows correct decision
- [ ] Review draft saved to session directory

### Review Content
- [ ] Summary section includes correct counts
- [ ] Assessment message matches severity
- [ ] Feedback grouped by file
- [ ] Line numbers displayed correctly
- [ ] Markdown formatting is valid
- [ ] Emoji indicators show up correctly

### Editor Integration
- [ ] `/edit` opens editor (test with different editors)
- [ ] Edited content preserved
- [ ] Preview reflects edits
- [ ] Post uses edited version

### GitHub Posting
- [ ] gh authentication check works
- [ ] Preview shows before posting
- [ ] Confirmation prompt appears
- [ ] Can cancel posting
- [ ] Successful post shows URL
- [ ] Failed post shows error message
- [ ] Session metadata updated after post

### Edge Cases
- [ ] Empty feedback collection (should warn)
- [ ] Very large review (100+ items)
- [ ] Special characters in feedback
- [ ] Long file paths
- [ ] No $EDITOR set (should default to vim)
- [ ] gh CLI not installed (should fail gracefully)
- [ ] Not authenticated with gh (should show helpful error)

## Manual Testing Script

```bash
#!/bin/bash
# Test Phase 4 features

# 1. Setup
cd /path/to/your/repo
pr-agent review 42

# 2. Add diverse feedback
/feedback README.md:1 critical Missing license header
/feedback src/main.py:45-60 important Need error handling
/feedback src/utils.js:20 suggestion Use const instead of let
/feedback src/config.ts:5 question Why hardcode this value?

# 3. List feedback
/list

# 4. Generate and preview
/generate
/preview

# 5. Edit review
/edit
# Make some changes and save

# 6. Preview edited version
/preview

# 7. Post (with auto-suggest)
/post auto
# Type 'yes' to confirm or 'no' to cancel

# 8. Check on GitHub
# Navigate to the PR and verify review is posted
```

## Integration Testing

### With Real PRs
Test with different PR types:

1. **Small PR (1-3 files)**
   - All feedback items should be included
   - Full context available

2. **Medium PR (4-10 files)**
   - Feedback properly grouped by file
   - Review remains readable

3. **Large PR (10+ files)**
   - Review still well-structured
   - Not overwhelming

### With Different Feedback Types

1. **Only Critical Issues**
   - Should suggest REQUEST_CHANGES
   - Assessment should be urgent

2. **Only Suggestions**
   - Should suggest COMMENT
   - Assessment should be mild

3. **Mixed Severity**
   - Should prioritize critical/important
   - Summary should reflect mix

## Known Limitations

1. **Inline Comments**: Current implementation posts a single review comment. Line-specific comments via gh CLI have limited support and are not yet implemented.

2. **Review Threading**: Each `/post` creates a new review. Cannot edit existing reviews.

3. **Rich Formatting**: Limited to GitHub markdown. No custom styling beyond what GitHub supports.

4. **Rate Limiting**: No explicit rate limit handling (relies on gh CLI)

## Future Enhancements

### Phase 5 Considerations
- [ ] Inline comments support (when gh CLI improves)
- [ ] Review templates
- [ ] Custom review actions (e.g., "approve with comments")
- [ ] Batch posting (multiple reviews)
- [ ] Review history in session
- [ ] AI-enhanced feedback wording using ReviewImprover
- [ ] Suggested code fixes generation

## Troubleshooting

### "gh not authenticated"
```bash
gh auth login
```

### "Editor not found"
```bash
export EDITOR=nano
# or
export EDITOR=code
```

### "Failed to post review"
Check:
- Network connection
- GitHub permissions
- PR is not locked/closed
- You have write access to the repo

### "No feedback items"
- Make sure to add feedback with `/feedback` before generating
- Check with `/list` to see current feedback

## Success Criteria

Phase 4 is complete when:
- [x] Can generate structured reviews from feedback
- [x] Preview shows correct decision and formatting
- [x] Editor integration works with different editors
- [x] Can post to GitHub with confirmation
- [x] All commands have proper error handling
- [x] Documentation is complete
- [ ] Manual testing passes all scenarios
- [ ] Works with real PRs in production use
