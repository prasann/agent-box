"""Comment storage and management for PR reviews."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


@dataclass
class Comment:
    """A single review comment."""
    file: str
    line: int
    code_snippet: str
    comment: str
    severity: str  # 'issue' | 'suggestion' | 'comment'
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Comment':
        """Create from dictionary."""
        return cls(**data)


class CommentStore:
    """Manages review comments with persistence."""
    
    def __init__(self, pr_number: int):
        """Initialize comment store.
        
        Args:
            pr_number: Pull request number
        """
        self.pr_number = pr_number
        self.comments: List[Comment] = []
        
        # Setup storage path
        storage_dir = Path.home() / ".pr-agent"
        storage_dir.mkdir(exist_ok=True)
        self.file_path = storage_dir / f"pr-{pr_number}-comments.json"
        
        # Load existing comments
        self.load()
    
    def add_comment(self, comment: Comment) -> None:
        """Add a single comment.
        
        Args:
            comment: Comment to add
        """
        self.comments.append(comment)
        self.save()
    
    def add_comments(self, comments: List[Comment]) -> None:
        """Add multiple comments.
        
        Args:
            comments: Comments to add
        """
        self.comments.extend(comments)
        self.save()
    
    def remove_comment(self, index: int) -> None:
        """Remove comment at index.
        
        Args:
            index: Index of comment to remove
        """
        if 0 <= index < len(self.comments):
            self.comments.pop(index)
            self.save()
    
    def update_comment(self, index: int, comment: Comment) -> None:
        """Update comment at index.
        
        Args:
            index: Index of comment to update
            comment: New comment data
        """
        if 0 <= index < len(self.comments):
            self.comments[index] = comment
            self.save()
    
    def clear(self) -> None:
        """Clear all comments."""
        self.comments = []
        self.save()
    
    def save(self) -> None:
        """Save comments to disk."""
        data = {
            'pr_number': self.pr_number,
            'comments': [c.to_dict() for c in self.comments]
        }
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> None:
        """Load comments from disk."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    self.comments = [
                        Comment.from_dict(c) for c in data.get('comments', [])
                    ]
            except (json.JSONDecodeError, KeyError):
                # If file is corrupted, start fresh
                self.comments = []
    
    def to_markdown(self) -> str:
        """Export comments as markdown.
        
        Returns:
            Markdown formatted comments
        """
        if not self.comments:
            return "No comments to export."
        
        lines = [f"# Review Comments for PR #{self.pr_number}\n"]
        
        for i, comment in enumerate(self.comments, 1):
            severity_emoji = {
                'issue': '🔴',
                'suggestion': '🟡',
                'comment': '🔵'
            }.get(comment.severity, '💬')
            
            lines.append(f"## {i}. {severity_emoji} {comment.severity.title()}")
            lines.append(f"**File:** `{comment.file}`")
            lines.append(f"**Line:** {comment.line}\n")
            
            if comment.code_snippet:
                lines.append("**Code:**")
                lines.append(f"```python\n{comment.code_snippet}\n```\n")
            
            lines.append(f"**Comment:** {comment.comment}\n")
            lines.append("---\n")
        
        return "\n".join(lines)
    
    def get_github_review_comments(self) -> List[dict]:
        """Format comments for GitHub API.
        
        Returns:
            List of comment dictionaries for GitHub API
        """
        return [
            {
                'path': comment.file,
                'line': comment.line,
                'body': f"**{comment.severity.title()}:** {comment.comment}"
            }
            for comment in self.comments
        ]
