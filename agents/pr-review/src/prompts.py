"""Prompts for PR review analysis."""


SYSTEM_PROMPT = """You are an expert code reviewer helping to review a pull request.

Your role:
- Provide concise, actionable feedback
- Point to actual code and line numbers
- Identify bugs, security issues, and improvements
- Suggest concrete changes
- Be encouraging and helpful

When reviewing, be brief and focused on what matters most. Skip obvious observations."""


INITIAL_ANALYSIS_PROMPT = """Analyze this PR and provide a concise review.

PR: {pr_info}

Files:
{file_list}

Diff:
```
{diff}
```

Provide a brief review:
1. **Summary** (2-3 sentences): What does this PR do?
2. **Key Issues**: Critical bugs or concerns only
3. **Suggestions**: Top 2-3 improvements

Be specific, reference files/lines, keep it concise."""


INITIAL_ANALYSIS_WITH_CONTEXT_PROMPT = """You are reviewing a pull request with FULL ACCESS to the codebase.

**PR Information:**
{pr_info}

**Files Changed:**
{file_list}

**Diff:**
```
{diff}
```

**Your Capabilities:**
You have access to the complete codebase at: `{repo_path}`

Use your built-in tools to:
- Read any file in the repository
- Search for function/class definitions
- Check how changed code is used elsewhere
- Look for similar patterns
- Verify consistency with existing code

**Review Instructions:**
1. **Understand Context**: Read related files to understand the full picture
2. **Check Consistency**: Verify changes align with existing patterns
3. **Find Issues**: Look for bugs, inconsistencies, or breaking changes
4. **Provide Specific Feedback**: Reference actual files and line numbers

**Output Format:**
## Summary
[2-3 sentence overview of what this PR does]

## Key Findings
[Critical issues or concerns with specific file references]

## Suggestions
[Concrete improvements with examples from the codebase]

Be thorough but concise. Focus on meaningful issues."""


REFINEMENT_PROMPT = """The user has a follow-up question about the PR review.

Previous conversation context is available in the chat history.

User's question: {question}

Please provide a helpful, specific answer. Reference actual code and line numbers when relevant."""


COMMENT_GENERATION_PROMPT = """Based on our conversation, generate review comments in this format:

For each significant issue or suggestion, provide:
- **File**: path/to/file.py
- **Line**: line number
- **Severity**: comment|suggestion|issue
- **Comment**: The actual comment text

Example format:
```
**File**: src/utils.py
**Line**: 42
**Severity**: issue
**Comment**: This function doesn't handle None values, which could cause a TypeError.
```

Generate comments based on all the issues and suggestions we've discussed."""


def format_pr_info(pr_data: dict) -> str:
    """Format PR metadata for prompt.
    
    Args:
        pr_data: PR metadata from gh CLI
        
    Returns:
        Formatted string
    """
    return f"""Title: {pr_data['title']}
Author: @{pr_data['author']['login']}
State: {pr_data['state']}
Files Changed: {len(pr_data.get('files', []))}
Additions: +{pr_data.get('additions', 0)}
Deletions: -{pr_data.get('deletions', 0)}

Description:
{pr_data.get('body', 'No description provided')}"""


def format_file_list(pr_data: dict) -> str:
    """Format file list for prompt.
    
    Args:
        pr_data: PR metadata from gh CLI
        
    Returns:
        Formatted string
    """
    files = pr_data.get('files', [])
    if not files:
        return "No files changed"
    
    lines = []
    for f in files:
        additions = f.get('additions', 0)
        deletions = f.get('deletions', 0)
        lines.append(f"- {f['path']} (+{additions} -{deletions})")
    
    return "\n".join(lines)


def build_initial_prompt(pr_info: dict, diff: str) -> str:
    """Build the initial analysis prompt.
    
    Args:
        pr_info: PR metadata from gh CLI
        diff: Full PR diff
        
    Returns:
        Complete prompt string
    """
    return INITIAL_ANALYSIS_PROMPT.format(
        pr_info=format_pr_info(pr_info),
        file_list=format_file_list(pr_info),
        diff=diff
    )


def build_initial_prompt_with_context(pr_info: dict, diff: str, repo_path: str) -> str:
    """Build prompt that encourages codebase exploration.
    
    Args:
        pr_info: PR metadata from gh CLI
        diff: Full PR diff
        repo_path: Path to repository root
        
    Returns:
        Complete prompt string with codebase context
    """
    return INITIAL_ANALYSIS_WITH_CONTEXT_PROMPT.format(
        pr_info=format_pr_info(pr_info),
        file_list=format_file_list(pr_info),
        diff=diff,
        repo_path=repo_path
    )


def build_refinement_prompt(question: str) -> str:
    """Build a refinement prompt for follow-up questions.
    
    Args:
        question: User's question
        
    Returns:
        Prompt string
    """
    return REFINEMENT_PROMPT.format(question=question)
