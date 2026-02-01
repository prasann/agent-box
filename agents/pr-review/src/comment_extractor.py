"""Extract structured comments from LLM responses."""

import re
from typing import List
from .comment_store import Comment


def extract_comments_from_response(text: str) -> List[Comment]:
    """Parse LLM response for structured comments.
    
    Expects format like:
    **File**: path/file.py
    **Line**: 42
    **Code**: original code
    **Comment**: suggestion text
    **Severity**: issue|suggestion|comment
    
    Args:
        text: LLM response text
        
    Returns:
        List of extracted comments
    """
    comments = []
    
    # Pattern to match comment blocks
    # More flexible pattern that handles variations
    pattern = r'\*\*File\*\*:\s*`?([^`\n]+?)`?\s*\n\s*\*\*Line\*\*:\s*(\d+)\s*(?:\n\s*\*\*Code\*\*:\s*```[\w]*\n(.*?)\n```\s*)?\n\s*\*\*Comment\*\*:\s*(.*?)(?:\n\s*\*\*Severity\*\*:\s*(issue|suggestion|comment))?(?=\n\s*\*\*File\*\*:|\n\s*---|\Z)'
    
    matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        file_path = match.group(1).strip()
        line_num = int(match.group(2))
        code_snippet = match.group(3).strip() if match.group(3) else ""
        comment_text = match.group(4).strip()
        severity = match.group(5).lower() if match.group(5) else "comment"
        
        # Clean up comment text (remove extra whitespace, trailing dashes)
        comment_text = re.sub(r'\s+', ' ', comment_text).strip()
        comment_text = re.sub(r'-+\s*$', '', comment_text).strip()
        
        if file_path and comment_text:
            comments.append(Comment(
                file=file_path,
                line=line_num,
                code_snippet=code_snippet,
                comment=comment_text,
                severity=severity
            ))
    
    return comments


def extract_comments_from_markdown_list(text: str) -> List[Comment]:
    """Extract comments from numbered/bulleted lists.
    
    Alternative format:
    1. **src/file.py:42** - Issue with error handling
       ```python
       code snippet
       ```
    
    Args:
        text: LLM response text
        
    Returns:
        List of extracted comments
    """
    comments = []
    
    # Pattern for list-style comments
    pattern = r'(?:^|\n)\s*[\d\-\*]+\.\s*\*\*([^:]+):(\d+)\*\*\s*(?:-\s*)?(.*?)(?:```[\w]*\n(.*?)\n```)?(?=\n\s*[\d\-\*]+\.|\n\n|\Z)'
    
    matches = re.finditer(pattern, text, re.DOTALL | re.MULTILINE)
    
    for match in matches:
        file_path = match.group(1).strip()
        line_num = int(match.group(2))
        comment_text = match.group(3).strip()
        code_snippet = match.group(4).strip() if match.group(4) else ""
        
        # Infer severity from keywords
        severity = "comment"
        comment_lower = comment_text.lower()
        if any(word in comment_lower for word in ['error', 'bug', 'issue', 'problem', 'critical']):
            severity = "issue"
        elif any(word in comment_lower for word in ['suggest', 'could', 'should', 'consider', 'recommend']):
            severity = "suggestion"
        
        if file_path and comment_text:
            comments.append(Comment(
                file=file_path,
                line=line_num,
                code_snippet=code_snippet,
                comment=comment_text,
                severity=severity
            ))
    
    return comments


def auto_extract_comments(text: str) -> List[Comment]:
    """Automatically extract comments using all available patterns.
    
    Args:
        text: LLM response text
        
    Returns:
        List of all extracted comments
    """
    all_comments = []
    
    # Try structured format first
    structured = extract_comments_from_response(text)
    all_comments.extend(structured)
    
    # Try list format if no structured comments found
    if not structured:
        list_format = extract_comments_from_markdown_list(text)
        all_comments.extend(list_format)
    
    return all_comments
