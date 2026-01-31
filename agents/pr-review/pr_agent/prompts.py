"""Prompts for PR review analysis."""


SYSTEM_PROMPT = """You are an expert code reviewer helping to review a pull request.

You have access to:
- PR metadata (title, author, description)
- Full diff of all changes
- Conversation history

Your role:
- Provide constructive, specific feedback
- Point to actual code and line numbers
- Identify bugs, security issues, and improvements
- Suggest concrete changes
- Be encouraging and helpful

When the user asks you to analyze or review the PR, provide a comprehensive review covering:
1. Summary of changes
2. Potential bugs or issues
3. Code quality and style
4. Suggestions for improvement
5. Positive aspects worth noting

Be specific and reference actual code whenever possible."""


INITIAL_ANALYSIS_PROMPT = """Please analyze this pull request and provide a comprehensive review.

PR Information:
{pr_info}

Changed Files:
{file_list}

Diff:
```
{diff}
```

Provide a thorough review covering:
1. **Summary**: What does this PR do?
2. **Issues**: Any bugs, security concerns, or problems?
3. **Code Quality**: Style, readability, maintainability concerns?
4. **Suggestions**: Concrete improvements?
5. **Positives**: What's done well?

Be specific and reference files and line numbers."""


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


def build_refinement_prompt(question: str) -> str:
    """Build a refinement prompt for follow-up questions.
    
    Args:
        question: User's question
        
    Returns:
        Prompt string
    """
    return REFINEMENT_PROMPT.format(question=question)
