"""Session state management."""

from pathlib import Path
from typing import Optional

from ..models import PRData
from ..models.feedback import FeedbackCollection
from .storage import SessionStorage, StorageError


class Session:
    """Represents an active PR review session."""
    
    def __init__(
        self,
        pr_data: PRData,
        session_dir: Path,
        storage: SessionStorage
    ):
        """Initialize a session.
        
        Args:
            pr_data: PR data for this session
            session_dir: Directory for session files
            storage: Storage manager
        """
        self.pr_data = pr_data
        self.session_dir = session_dir
        self.storage = storage
        self.conversation: list[dict] = []
        self.feedback: FeedbackCollection = FeedbackCollection(
            pr_number=pr_data.metadata.number
        )
    
    @property
    def pr_number(self) -> int:
        """Get PR number."""
        return self.pr_data.metadata.number
    
    @property
    def owner(self) -> str:
        """Get repository owner."""
        # This should be passed in - for now we'll store it when creating session
        return self.session_dir.parent.parent.name
    
    @property
    def repo(self) -> str:
        """Get repository name."""
        return self.session_dir.parent.name
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation.
        
        Args:
            role: Message role (user/assistant/system)
            content: Message content
        """
        self.conversation.append({
            "role": role,
            "content": content
        })
    
    def save(self) -> None:
        """Save session .items:
            self.storage.save_feedback(self.session_dir, self.feedback)
    
    def load_conversation(self) -> None:
        """Load conversation from disk."""
        self.conversation = self.storage.load_conversation(self.session_dir)
    
    def load_feedback(self) -> None:
        """Load feedback from disk."""
        self.feedback = self.storage.load_feedback(self.session_dir, self.pr_numbe
        """Load feedback from disk."""
        self.feedback = self.storage.load_feedback(self.session_dir)


class SessionManager:
    """Manages PR review sessions."""
    
    def __init__(self, storage: Optional[SessionStorage] = None):
        """Initialize session manager.
        
        Args:
            storage: Session storage (creates default if not provided)
        """
        self.storage = storage or SessionStorage()
    
    def create_session(
        self,
        owner: str,
        repo: str,
        pr_data: PRData
    ) -> Session:
        """Create a new session.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_data: PR data
            
        Returns:
            Created session
        """
        session_dir = self.storage.create_session(owner, repo, pr_data.metadata.number)
        self.storage.save_pr_data(session_dir, pr_data)
        
        session = Session(pr_data, session_dir, self.storage)
        return session
    
    def resume_session(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        pr_data: PRData
    ) -> Session:
        """Resume an existing session.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            pr_data: PR data (refreshed from GitHub)
            
        Returns:
            Resumed session with loaded conversation and feedback
        """
        session_dir = self.storage.get_session_dir(owner, repo, pr_number)
        
        if not session_dir.exists():
            raise ValueError(f"Session does not exist for PR #{pr_number}")
        
        session = Session(pr_data, session_dir, self.storage)
        session.load_conversation()
        session.load_feedback()
        
        return session
    
    def session_exists(self, owner: str, repo: str, pr_number: int) -> bool:
        """Check if a session exists.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            True if session exists
        """
        return self.storage.session_exists(owner, repo, pr_number)
    
    def get_session_dir(self, owner: str, repo: str, pr_number: int) -> Path:
        """Get session directory path.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            Path to session directory
        """
        return self.storage.get_session_dir(owner, repo, pr_number)
