# Editing Prompts

All prompts are now in the `prompts/` directory as `.prompty` files.

## Quick Start

1. Open any `.prompty` file in VS Code
2. Edit the content below the `---` markers
3. Save - changes take effect immediately (no restart needed)

## File Structure

```
prompts/
  ├── system.prompty                    # Base system prompt
  ├── pr_review_with_context.prompty    # Main PR review
  ├── refinement.prompty                # Follow-up questions
  └── comment_generation.prompty        # Generate comments
```

## Prompty File Format

```yaml
---
name: Prompt Name
description: What this prompt does
model:
  api: chat
  configuration:
    type: openai
    model: gpt-4
inputs:
  variable_name:
    type: string
    description: What this variable contains
---
system:
Your system message here

user:
Your user message with {{variables}}
```

## Example: Editing the PR Review Prompt

**File:** `prompts/pr_review_with_context.prompty`

```yaml
---
name: PR Review with Full Codebase Context
inputs:
  pr_info: PR metadata
  file_list: Changed files
  diff: Git diff
  repo_path: Repository path
---
user:
You are reviewing a pull request...

**PR Information:**
{{pr_info}}

**Your Task:**
1. Read related files
2. Check for issues
3. Provide feedback
```

### To add a new instruction:

Just edit the text! For example:

```diff
**Your Task:**
1. Read related files
2. Check for issues
3. Provide feedback
+ 4. Suggest test coverage
```

### To use a variable:

Use double curly braces: `{{variable_name}}`

Example:
```
The repository is at: {{repo_path}}
```

## VS Code Extension (Recommended)

Install the Prompty extension for:
- Syntax highlighting
- IntelliSense
- Prompt testing UI
- Variable validation

Search "Prompty" in VS Code extensions or:
```bash
code --install-extension ms-toolsai.prompty
```

## Testing Prompts

### From Python:

```python
from src.prompt_loader import render_prompt

result = render_prompt('system')
print(result)
```

### With variables:

```python
result = render_prompt('pr_review_with_context',
    pr_info="Title: Fix bug",
    file_list="- auth.py",
    diff="...",
    repo_path="/path/to/repo"
)
```

## Available Variables

### `pr_review_with_context.prompty`
- `pr_info` - PR title, author, description (formatted)
- `file_list` - List of changed files with +/- stats (formatted)
- `diff` - Full git diff
- `repo_path` - Absolute path to repository

### `refinement.prompty`
- `question` - User's follow-up question

### `system.prompty`
- (No variables)

### `comment_generation.prompty`
- (No variables)

## Tips

1. **Keep it concise** - LLMs work better with clear, brief instructions
2. **Use examples** - Show the LLM what you want
3. **Be specific** - "Check for null pointer bugs" vs "Review the code"
4. **Test iteratively** - Make small changes, test, repeat
5. **Use markdown** - It helps structure the prompt

## Common Edits

### Change the tone:

```diff
- Be encouraging and helpful
+ Be direct and technical
```

### Add a new check:

```diff
**Review Instructions:**
1. Understand Context
2. Check Consistency
3. Find Issues
+ 4. Verify test coverage
```

### Modify output format:

```diff
**Output Format:**
## Summary
[overview]

+ ## Test Coverage
+ [assessment of tests]
```

## Troubleshooting

### Prompt not loading?

Check filename matches exactly: `render_prompt('system')` → `prompts/system.prompty`

### Variables not substituting?

Make sure you're using `{{variable}}` not `{variable}` or `$variable`

### Changes not appearing?

Prompts are cached - restart the app or clear cache:
```python
from src.prompt_loader import _loader
_loader._cache.clear()
```

## Advanced: Adding a New Prompt

1. Create `prompts/my_new_prompt.prompty`:

```yaml
---
name: My New Prompt
description: What it does
inputs:
  input1:
    type: string
---
user:
Your prompt with {{input1}}
```

2. Use it in code:

```python
from src.prompt_loader import render_prompt

result = render_prompt('my_new_prompt', input1="value")
```

That's it! The prompt loader will automatically find and load it.
