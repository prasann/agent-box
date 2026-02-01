# Implementation Notes: Full Codebase Context PR Review

## What Changed

### New Capabilities
✅ **Full codebase access** - LLM can now read any file in the repository
✅ **Automatic exploration** - LLM decides what files to read based on the diff
✅ **Consistency checking** - Can verify changes align with existing patterns
✅ **Breaking change detection** - Can search for usages of changed functions
✅ **Safe branch management** - Auto-checkout PR, restore original branch

### Files Added
- `src/repo_utils.py` - Repository operations (checkout, branch management, validation)

### Files Modified
- `src/analyzer.py` - Added PR checkout, `working_directory` configuration, branch restore
- `src/prompts.py` - Added context-aware prompt that encourages codebase exploration
- `app.py` - Added repo validation checks and better error handling
- `README.md` - Updated documentation

## How It Works

### Flow
```
1. User starts agent → Check repo is clean (no uncommitted changes)
2. User enters PR number
3. Agent remembers current branch
4. Agent checks out PR branch
5. Agent creates Copilot session with working_directory = repo_root
6. Agent sends enhanced prompt with diff + codebase access instructions
7. LLM analyzes diff AND explores codebase using built-in tools:
   - read_file / view - Read any file
   - list_files - List directory contents
   - shell commands - Run git/grep/search
8. LLM provides comprehensive review with file references
9. User can ask follow-up questions (LLM continues exploring)
10. On session end → Restore original branch
```

### Key Implementation Details

#### 1. Working Directory Configuration
```python
session = await client.create_session({
    "model": "gpt-4",
    "streaming": True,
    "working_directory": repo_path  # 🎯 Enables full codebase access
})
```

This single line enables the Copilot SDK's built-in tools to access the entire repository.

#### 2. Enhanced Prompt
The prompt now explicitly tells the LLM it has codebase access:

```
You have access to the complete codebase at: {repo_path}

Use your built-in tools to:
- Read any file in the repository
- Search for function/class definitions
- Check how changed code is used elsewhere
- Look for similar patterns
- Verify consistency with existing code
```

#### 3. Safety Checks
```python
# Before starting
if not check_repo_clean():
    abort("Repository has uncommitted changes")

# After review
restore_branch(original_branch)
```

## What the LLM Can Now Do

### Before (Diff Only)
- See changed lines with ~3 lines context
- Make educated guesses about impact
- Limited to information in the diff

### After (Full Codebase Access)
- **Read related files** - "Let me check how authenticate() is used..."
- **Search for patterns** - "Looking for similar error handling..."
- **Verify consistency** - "Comparing with existing API endpoints..."
- **Check dependencies** - "Reading the imports to understand context..."
- **Find breaking changes** - "Searching for all callers of this function..."

## Example Interactions

### Before
```
User: Review PR #42
Agent: [Reviews diff only]
       "This changes the auth function. Looks good."
```

### After
```
User: Review PR #42
Agent: [Reviews diff]
       "I see changes to auth.py. Let me check where authenticate() is used..."
       [Reads auth_middleware.py, user_service.py, tests/auth_test.py]
       "⚠️ This will break user_service.py line 45 because it expects a 
       'token' field but the PR removes it. Also, tests need updating."
```

## Built-in Tools Available

The SDK provides these tools automatically (no custom implementation needed):
- `view` / `read_file` - Read file contents
- `list_files` - List directory
- `shell` - Execute commands (git, grep, find, etc.)
- `write` - Create/edit files (can be disabled)
- `search` - Search codebase

## Next Phase: UI Improvements

Future enhancements for better UX:
- [ ] Show which files the LLM is reading in real-time
- [ ] Display "Exploring codebase..." status messages
- [ ] Add file tree view of explored files
- [ ] Show diff inline in chat
- [ ] Add "Review Status" panel (Issues found, Files checked, etc.)
- [ ] Enable diff commenting directly in UI

## Testing

To test the implementation:

```bash
# 1. Make sure you're in a repo with a PR
cd ~/some-project

# 2. Commit any changes
git status
git commit -am "save work"

# 3. Run the agent
cd ~/agent-box/agents/pr-review
uv run chainlit run app.py

# 4. Try a PR number
# Example prompts to test:
# - "Review this PR and check related files"
# - "Are there any similar functions in the codebase?"
# - "Show me where this function is used"
```

## Limitations & Considerations

1. **Requires clean repo** - Won't start if uncommitted changes exist
2. **Checks out PR branch** - Temporarily switches branches (restores after)
3. **LLM decides what to read** - May miss relevant files (can ask follow-ups)
4. **Token usage** - More context = more tokens (but more accurate reviews)
5. **Network dependency** - Needs GitHub CLI for PR operations

## Philosophy Maintained

✅ **"Beautiful UI, simple code, powerful AI"**
✅ **Let the LLM do the work** - It decides what to explore
✅ **Minimal code** - Leveraged SDK's built-in capabilities
✅ **Natural conversation** - No new commands needed
✅ **Simple** - Just added working_directory + enhanced prompt
