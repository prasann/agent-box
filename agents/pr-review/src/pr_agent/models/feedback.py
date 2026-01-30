"""Data models for PR review feedback."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FeedbackSeverity(str, Enum):
    """Severity levels for feedback items."""
    CRITICAL = "critical"
    IMPORTANT = "important"
    SUGGESTION = "suggestion"
    QUESTION = "question"


class FeedbackItem(BaseModel):
    """A single piece of feedback for a PR."""
    
    id: int = Field(..., description="Unique identifier for this feedback item")
    file: str = Field(..., description="File path the feedback relates to")
    lines: Optional[str] = Field(None, description="Line range (e.g., '45' or '45-60')")
    comment: str = Field(..., description="The feedback comment")
    severity: FeedbackSeverity = Field(
        default=FeedbackSeverity.SUGGESTION,
        description="Severity level of the feedback"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the feedback was created"
    )
    
    def format_for_display(self) -> str:
        """Format the feedback item for terminal display.
        
        Returns:
            Formatted string for display
        """
        severity_emoji = {
            FeedbackSeverity.CRITICAL: "🔴",
            FeedbackSeverity.IMPORTANT: "🟡",
            FeedbackSeverity.SUGGESTION: "💡",
            FeedbackSeverity.QUESTION: "❓"
        }
        
        emoji = severity_emoji.get(self.severity, "•")
        location = f"{self.file}"
        if self.lines:
            location += f":{self.lines}"
        
        return f"{emoji} [{self.id}] {location}\n   {self.comment}"
    
    def format_for_github(self) -> str:
        """Format the feedback item for GitHub comment.
        
        Returns:
            Formatted markdown string for GitHub
        """
        severity_label = {
            FeedbackSeverity.CRITICAL: "**🔴 Critical**",
            FeedbackSeverity.IMPORTANT: "**🟡 Important**",
            FeedbackSeverity.SUGGESTION: "**💡 Suggestion**",
            FeedbackSeverity.QUESTION: "**❓ Question**"
        }
        
        label = severity_label.get(self.severity, "**Note**")
        location = f"`{self.file}`"
        if self.lines:
            location += f" (lines {self.lines})"
        
        return f"{label}: {location}\n\n{self.comment}"


class FeedbackCollection(BaseModel):
    """Collection of feedback items for a PR."""
    
    pr_number: int = Field(..., description="PR number this feedback is for")
    items: list[FeedbackItem] = Field(
        default_factory=list,
        description="List of feedback items"
    )
    next_id: int = Field(default=1, description="Next available ID")
    
    def add_item(
        self,
        file: str,
        comment: str,
        lines: Optional[str] = None,
        severity: FeedbackSeverity = FeedbackSeverity.SUGGESTION
    ) -> FeedbackItem:
        """Add a new feedback item.
        
        Args:
            file: File path
            comment: Feedback comment
            lines: Line range (optional)
            severity: Severity level
            
        Returns:
            The created feedback item
        """
        item = FeedbackItem(
            id=self.next_id,
            file=file,
            lines=lines,
            comment=comment,
            severity=severity
        )
        self.items.append(item)
        self.next_id += 1
        return item
    
    def get_item(self, item_id: int) -> Optional[FeedbackItem]:
        """Get a feedback item by ID.
        
        Args:
            item_id: The item ID
            
        Returns:
            The feedback item, or None if not found
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def delete_item(self, item_id: int) -> bool:
        """Delete a feedback item by ID.
        
        Args:
            item_id: The item ID
            
        Returns:
            True if deleted, False if not found
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                return True
        return False
    
    def get_items_by_file(self, file: str) -> list[FeedbackItem]:
        """Get all feedback items for a specific file.
        
        Args:
            file: File path
            
        Returns:
            List of feedback items for the file
        """
        return [item for item in self.items if item.file == file]
    
    def get_items_by_severity(self, severity: FeedbackSeverity) -> list[FeedbackItem]:
        """Get all feedback items of a specific severity.
        
        Args:
            severity: Severity level
            
        Returns:
            List of feedback items with that severity
        """
        return [item for item in self.items if item.severity == severity]
    
    def count_by_severity(self) -> dict[FeedbackSeverity, int]:
        """Count feedback items by severity.
        
        Returns:
            Dictionary mapping severity to count
        """
        counts = {severity: 0 for severity in FeedbackSeverity}
        for item in self.items:
            counts[item.severity] += 1
        return counts
    
    def format_summary(self) -> str:
        """Format a summary of the feedback collection.
        
        Returns:
            Formatted summary string
        """
        if not self.items:
            return "No feedback items"
        
        counts = self.count_by_severity()
        parts = [
            f"Total feedback items: {len(self.items)}",
            f"  🔴 Critical: {counts[FeedbackSeverity.CRITICAL]}",
            f"  🟡 Important: {counts[FeedbackSeverity.IMPORTANT]}",
            f"  💡 Suggestions: {counts[FeedbackSeverity.SUGGESTION]}",
            f"  ❓ Questions: {counts[FeedbackSeverity.QUESTION]}"
        ]
        return "\n".join(parts)
    
    def format_for_github_review(self) -> str:
        """Format all feedback items as a GitHub review comment.
        
        Returns:
            Formatted markdown for GitHub
        """
        if not self.items:
            return "No feedback items to post."
        
        parts = [
            "# Code Review Feedback",
            "",
            self.format_summary(),
            "",
            "---",
            ""
        ]
        
        # Group by file
        files = {}
        for item in self.items:
            if item.file not in files:
                files[item.file] = []
            files[item.file].append(item)
        
        for file, items in sorted(files.items()):
            parts.append(f"## `{file}`")
            parts.append("")
            for item in items:
                parts.append(item.format_for_github())
                parts.append("")
        
        return "\n".join(parts)
