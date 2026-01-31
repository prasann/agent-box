"""Simple state management for PR reviews."""

import json
from pathlib import Path
from typing import Any


class StateError(Exception):
    """State operation error."""
    pass


class ReviewState:
    """Manages review state in a JSON file."""
    
    def __init__(self, pr_number: int, state_dir: Path | None = None):
        """Initialize state manager.
        
        Args:
            pr_number: Pull request number
            state_dir: Directory for state files (default: ~/.pr-agent)
        """
        self.pr_number = pr_number
        self.state_dir = state_dir or (Path.home() / ".pr-agent")
        self.state_file = self.state_dir / f"pr-{pr_number}.json"
        
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self.data: dict[str, Any] = {
            "pr_number": pr_number,
            "conversation": [],
            "comments": [],
            "metadata": {}
        }
        
        # Load existing state if available
        if self.state_file.exists():
            self.load()
    
    def load(self) -> None:
        """Load state from file."""
        try:
            with open(self.state_file, "r") as f:
                self.data = json.load(f)
        except Exception as e:
            raise StateError(f"Failed to load state: {e}")
    
    def save(self) -> None:
        """Save state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            raise StateError(f"Failed to save state: {e}")
    
    def add_message(self, role: str, content: str, persist: bool = True) -> None:
        """Add a message to conversation history.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            persist: Whether to save this message to disk (default True)
        """
        self.data["conversation"].append({"role": role, "content": content})
        if persist:
            self.save()
    
    def add_comment(self, file: str, line: int, comment: str, severity: str = "comment") -> None:
        """Add a review comment.
        
        Args:
            file: File path
            line: Line number
            comment: Comment text
            severity: Severity level (comment, suggestion, issue)
        """
        self.data["comments"].append({
            "file": file,
            "line": line,
            "comment": comment,
            "severity": severity
        })
        self.save()
    
    def get_conversation(self) -> list[dict[str, str]]:
        """Get conversation history.
        
        Returns:
            List of message dicts
        """
        return self.data["conversation"]
    
    def get_comments(self) -> list[dict[str, Any]]:
        """Get all review comments.
        
        Returns:
            List of comment dicts
        """
        return self.data["comments"]
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.data["metadata"][key] = value
        self.save()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value
        """
        return self.data["metadata"].get(key, default)
    
    def clear_comments(self) -> None:
        """Clear all review comments."""
        self.data["comments"] = []
        self.save()
