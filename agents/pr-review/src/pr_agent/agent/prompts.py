"""Prompt templates and context formatting for the PR review agent."""

from typing import Optional
from pr_agent.context.context_builder import PRContext, FileContext


# System prompt for the PR review agent
SYSTEM_PROMPT = """You are an expert code reviewer helping to review a GitHub Pull Request.

Your responsibilities:
- Analyze code changes for potential bugs, security issues, and performance problems
- Check for code quality, readability, and maintainability concerns
- Suggest improvements and best practices
- Answer questions about the changes
- Provide constructive, actionable feedback

Guidelines:
- Be thorough but concise
- Focus on significant issues rather than nitpicking style
- Explain the reasoning behind your suggestions
- Consider the broader context of the codebase
- Be respectful and constructive in your feedback
- If you're uncertain, acknowledge it

You have access to:
- The PR diff showing all changes
- The full content of changed files (when available)
- Git history for changed files
- Recent commits in the repository
- Git blame information (for context)

When providing feedback:
- Reference specific files and line numbers
- Explain the impact of issues you find
- Suggest concrete solutions
- Prioritize issues by severity (critical, important, suggestion)"""


ANALYSIS_PROMPT = """Please analyze this Pull Request and provide a comprehensive review.

Focus on:
1. **Correctness**: Are there any bugs or logical errors?
2. **Security**: Are there any security vulnerabilities?
3. **Performance**: Could anything be optimized?
4. **Code Quality**: Is the code clean, readable, and maintainable?
5. **Best Practices**: Does it follow language/framework conventions?
6. **Testing**: Are there adequate tests?

Provide your feedback in a structured format."""


SUMMARY_PROMPT = """Please provide a brief summary of the main changes in this Pull Request.

Include:
- What features or fixes are being introduced
- Which areas of the codebase are affected
- Any notable patterns or architectural changes"""


QUESTION_ANSWER_PROMPT = """Based on the PR context provided, please answer the following question:

{question}

Provide a clear, specific answer referencing relevant parts of the code."""


FOCUSED_REVIEW_PROMPT = """Please review the following specific file from the PR:

File: {file_path}

Focus on this file in detail and provide specific feedback."""


FEEDBACK_GENERATION_PROMPT = """Based on the conversation history and the issues identified, generate a structured review with specific, actionable feedback comments.

For each piece of feedback, include:
- The file path and line numbers (if applicable)
- A clear description of the issue or suggestion
- The severity level (critical, important, suggestion)
- Suggested improvement or fix

Format the output as structured feedback items that can be posted to GitHub."""


def format_pr_context_for_llm(context: PRContext, include_blame: bool = False) -> str:
    """Format PR context for inclusion in LLM prompts.
    
    Args:
        context: The PR context to format
        include_blame: Whether to include git blame information
        
    Returns:
        Formatted context string
    """
    sections = []
    
    # PR Metadata
    sections.append(f"""# Pull Request #{context.pr_number}

**Title**: {context.title}
**Author**: {context.author}
**Strategy**: {context.strategy} context

## Description
{context.description or "No description provided"}
""")
    
    # Recent commits (if available)
    if context.recent_commits:
        sections.append("\n## Recent Commits")
        for commit in context.recent_commits[:5]:  # Limit to 5
            sections.append(f"- {commit.short_hash}: {commit.message} ({commit.author})")
    
    # Diff
    sections.append(f"\n## Changes (Diff)\n```diff\n{context.diff}\n```")
    
    # File details
    if context.files:
        sections.append("\n## Changed Files")
        
        for file_path, file_ctx in context.files.items():
            sections.append(f"\n### {file_path}")
            
            if file_ctx.not_found:
                sections.append("*(File not found - possibly deleted)*")
                continue
            
            if file_ctx.too_large:
                sections.append(f"*(File too large: {file_ctx.size:,} bytes)*")
                continue
            
            # File content
            if file_ctx.content:
                sections.append(f"\n**Current Content**:\n```\n{file_ctx.content}\n```")
            
            # File history
            if file_ctx.history:
                sections.append("\n**Recent Changes**:")
                for commit in file_ctx.history[:3]:  # Limit to 3
                    sections.append(f"- {commit.short_hash}: {commit.message}")
            
            # Blame (optional, can be verbose)
            if include_blame and file_ctx.blame:
                sections.append(f"\n**Git Blame**:\n```\n{file_ctx.blame}\n```")
    
    return "\n".join(sections)


def format_file_context_for_llm(file_ctx: FileContext, include_blame: bool = True) -> str:
    """Format a single file's context for LLM prompts.
    
    Args:
        file_ctx: The file context to format
        include_blame: Whether to include git blame
        
    Returns:
        Formatted file context string
    """
    sections = [f"# File: {file_ctx.path}"]
    
    if file_ctx.not_found:
        sections.append("\n*(File not found - possibly deleted)*")
        return "\n".join(sections)
    
    if file_ctx.too_large:
        sections.append(f"\n*(File too large: {file_ctx.size:,} bytes)*")
        return "\n".join(sections)
    
    # File content
    if file_ctx.content:
        sections.append(f"\n## Current Content\n```\n{file_ctx.content}\n```")
    
    # File history
    if file_ctx.history:
        sections.append("\n## Recent Changes")
        for commit in file_ctx.history:
            sections.append(f"- {commit.short_hash}: {commit.message} by {commit.author}")
    
    # Blame
    if include_blame and file_ctx.blame:
        sections.append(f"\n## Git Blame\n```\n{file_ctx.blame}\n```")
    
    return "\n".join(sections)


def build_prompt_with_context(
    base_prompt: str,
    context: PRContext,
    include_blame: bool = False,
    additional_context: Optional[str] = None
) -> str:
    """Build a complete prompt with PR context.
    
    Args:
        base_prompt: The base prompt template
        context: PR context to include
        include_blame: Whether to include git blame
        additional_context: Any additional context to append
        
    Returns:
        Complete prompt with context
    """
    parts = [
        format_pr_context_for_llm(context, include_blame=include_blame),
        "",
        "---",
        "",
        base_prompt
    ]
    
    if additional_context:
        parts.extend(["", "## Additional Context", additional_context])
    
    return "\n".join(parts)


def build_question_prompt(question: str, context: PRContext) -> str:
    """Build a prompt for answering a specific question.
    
    Args:
        question: The user's question
        context: PR context
        
    Returns:
        Complete prompt
    """
    formatted_question = QUESTION_ANSWER_PROMPT.format(question=question)
    return build_prompt_with_context(
        formatted_question,
        context,
        include_blame=False  # Skip blame for questions to reduce tokens
    )


def build_analysis_prompt(context: PRContext) -> str:
    """Build a prompt for comprehensive PR analysis.
    
    Args:
        context: PR context
        
    Returns:
        Complete prompt
    """
    return build_prompt_with_context(
        ANALYSIS_PROMPT,
        context,
        include_blame=(context.strategy == "full")  # Only include blame for small PRs
    )


def build_summary_prompt(context: PRContext) -> str:
    """Build a prompt for PR summary.
    
    Args:
        context: PR context
        
    Returns:
        Complete prompt
    """
    return build_prompt_with_context(
        SUMMARY_PROMPT,
        context,
        include_blame=False  # No blame needed for summaries
    )


def build_focused_review_prompt(file_path: str, file_ctx: FileContext) -> str:
    """Build a prompt for reviewing a specific file.
    
    Args:
        file_path: Path to the file
        file_ctx: File context
        
    Returns:
        Complete prompt
    """
    file_context = format_file_context_for_llm(file_ctx, include_blame=True)
    focused_prompt = FOCUSED_REVIEW_PROMPT.format(file_path=file_path)
    
    return f"{file_context}\n\n---\n\n{focused_prompt}"


def estimate_token_count(text: str) -> int:
    """Rough estimate of token count (1 token ≈ 4 characters).
    
    Args:
        text: Text to estimate
        
    Returns:
        Estimated token count
    """
    return len(text) // 4


def should_truncate_context(context: PRContext, max_tokens: int = 100000) -> bool:
    """Check if context should be truncated based on estimated token count.
    
    Args:
        context: PR context
        max_tokens: Maximum allowed tokens
        
    Returns:
        True if context should be truncated
    """
    formatted = format_pr_context_for_llm(context, include_blame=True)
    estimated_tokens = estimate_token_count(formatted)
    return estimated_tokens > max_tokens
