"""Session storage and management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..models import PRData
from ..models.feedback import FeedbackCollection


class StorageError(Exception):
    """Storage operation error."""
    pass


class SessionStorage:
    """Manages session data on disk."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize session storage.
        
        Args:
            base_path: Base directory for sessions (defaults to ~/.config/pr-agent/sessions)
        """
        if base_path is None:
            self.base_path = Path.home() / ".config" / "pr-agent" / "sessions"
        else:
            self.base_path = Path(base_path)
    
    def get_session_dir(self, owner: str, repo: str, pr_number: int) -> Path:
        """Get session directory path.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            Path to session directory
        """
        return self.base_path / owner / repo / f"pr-{pr_number}"
    
    def create_session(self, owner: str, repo: str, pr_number: int) -> Path:
        """Create a new session directory.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            Path to created session directory
        """
        session_dir = self.get_session_dir(owner, repo, pr_number)
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def session_exists(self, owner: str, repo: str, pr_number: int) -> bool:
        """Check if a session exists.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            True if session directory exists
        """
        return self.get_session_dir(owner, repo, pr_number).exists()
    
    def save_pr_data(self, session_dir: Path, pr_data: PRData) -> None:
        """Save PR data to session.
        
        Args:
            session_dir: Session directory path
            pr_data: PR data to save
        """
        try:
            # Save metadata
            metadata_file = session_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(pr_data.metadata.model_dump(mode="json"), f, indent=2, default=str)
            
            # Save diff
            diff_file = session_dir / "diff.txt"
            diff_file.write_text(pr_data.diff)
            
            # Save session info
            info_file = session_dir / "session_info.json"
            info = {
                "created_at": datetime.now().isoformat(),
                "pr_number": pr_data.metadata.number,
                "pr_title": pr_data.metadata.title,
                "pr_author": pr_data.metadata.author.login,
            }
            with open(info_file, "w") as f:
                json.dump(info, f, indent=2)
                
        except Exception as e:
            raise StorageError(f"Failed to save PR data: {e}")
    
    def save_conversation(self, session_dir: Path, messages: list[dict]) -> None:
        """Save conversation history.
        
        Args:
            session_dir: Session directory path
            messages: List of conversation messages
        """
        try:
            conversation_file = session_dir / "conversation.json"
            data = {
                "updated_at": datetime.now().isoformat(),
                "messages": messages
            }
            with open(conversation_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise StorageError(f"Failed to save conversation: {e}")
    
    def load_conversation(self, session_dir: Path) -> list[dict]:
        """Load conversation history.
        
        Args:
            session_dir: Session directory path
            
        Returns:
            List of conversation messages
        """
        try:
            conversation_file = session_dir / "conversation.json"
            if not conversation_file.exists():
                return []
            
            with open(conversation_file, "r") as f:
                data = json.load(f)
                return data.get("messages", [])
        except Exception as e:
            raise StorageError(f"Failed to load conversation: {e}")
    
    def save_feedback(self, session_dir: Path, feedback_collection: FeedbackCollection) -> None:
        """Save feedback collection.
        
        Args:
            session_dir: Session directory path
            feedback_collection: Feedback collection to save
        """
        try:
            feedback_file = session_dir / "feedback.json"
            data = {
                "updated_at": datetime.now().isoformat(),
                "pr_number": feedback_collection.pr_number,
                "next_id": feedback_collection.next_id,
                "items": [item.model_dump(mode="json") for item in feedback_collection.items]
            }
            with open(feedback_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            raise StorageError(f"Failed to save feedback: {e}")
    
    def load_feedback(self, session_dir: Path, pr_number: int) -> FeedbackCollection:
        """Load feedback collection.
        
        Args:
            session_dir: Session directory path
            pr_number: PR number
            
        Returns:
            Feedback collection
        """
        try:
            feedback_file = session_dir / "feedback.json"
            if not feedback_file.exists():
                return FeedbackCollection(pr_number=pr_number)
            
            with open(feedback_file, "r") as f:
                data = json.load(f)
                return FeedbackCollection.model_validate(data)
        except Exception as e:
            raise StorageError(f"Failed to load feedback: {e}")
