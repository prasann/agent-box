"""Smart context builder for PR reviews."""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
import logging

from pr_agent.context.repo_reader import RepoReader
from pr_agent.context.git_context import GitContext, CommitInfo

logger = logging.getLogger(__name__)


# Thresholds for context strategies
SMALL_PR_THRESHOLD = 10  # files
LARGE_PR_THRESHOLD = 50  # files
MAX_FILE_SIZE_FOR_FULL_CONTEXT = 500_000  # 500KB


@dataclass
class FileContext:
    """Context information for a single file."""
    path: str
    content: Optional[str] = None
    size: Optional[int] = None
    history: list[CommitInfo] = field(default_factory=list)
    blame: Optional[str] = None
    too_large: bool = False
    not_found: bool = False


@dataclass
class PRContext:
    """Complete context for a PR review."""
    pr_number: int
    title: str
    description: str
    author: str
    diff: str
    files: dict[str, FileContext] = field(default_factory=dict)
    recent_commits: list[CommitInfo] = field(default_factory=list)
    strategy: str = "full"  # full, partial, or minimal
    
    def get_file_count(self) -> int:
        """Get the number of files in this PR."""
        return len(self.files)
    
    def get_total_context_size(self) -> int:
        """Estimate total context size in bytes."""
        size = len(self.diff)
        for file_ctx in self.files.values():
            if file_ctx.content:
                size += len(file_ctx.content)
            if file_ctx.blame:
                size += len(file_ctx.blame)
        return size


class ContextBuilder:
    """Build smart context for PR reviews based on PR size and complexity."""
    
    def __init__(self, repo_root: Path | str):
        """Initialize the context builder.
        
        Args:
            repo_root: Path to the repository root directory
        """
        self.repo_root = Path(repo_root)
        self.repo_reader = RepoReader(repo_root)
        self.git_context = GitContext(repo_root)
    
    def build_context(
        self,
        pr_number: int,
        title: str,
        description: str,
        author: str,
        diff: str,
        changed_files: list[str]
    ) -> PRContext:
        """Build appropriate context based on PR size.
        
        Args:
            pr_number: PR number
            title: PR title
            description: PR description/body
            author: PR author
            diff: PR diff
            changed_files: List of changed file paths
            
        Returns:
            Complete PR context with appropriate detail level
        """
        file_count = len(changed_files)
        
        # Determine strategy based on PR size
        if file_count <= SMALL_PR_THRESHOLD:
            logger.info(f"Small PR ({file_count} files) - using full context")
            return self._build_full_context(
                pr_number, title, description, author, diff, changed_files
            )
        elif file_count <= LARGE_PR_THRESHOLD:
            logger.info(f"Medium PR ({file_count} files) - using partial context")
            return self._build_partial_context(
                pr_number, title, description, author, diff, changed_files
            )
        else:
            logger.info(f"Large PR ({file_count} files) - using minimal context")
            return self._build_minimal_context(
                pr_number, title, description, author, diff, changed_files
            )
    
    def _build_full_context(
        self,
        pr_number: int,
        title: str,
        description: str,
        author: str,
        diff: str,
        changed_files: list[str]
    ) -> PRContext:
        """Build full context for small PRs (includes everything).
        
        Args:
            pr_number: PR number
            title: PR title
            description: PR description
            author: PR author
            diff: PR diff
            changed_files: List of changed file paths
            
        Returns:
            PR context with full details
        """
        context = PRContext(
            pr_number=pr_number,
            title=title,
            description=description,
            author=author,
            diff=diff,
            strategy="full"
        )
        
        # Get recent commits for broader context
        context.recent_commits = self.git_context.get_recent_commits(limit=10)
        
        # Process each file with full details
        for file_path in changed_files:
            file_ctx = FileContext(path=file_path)
            
            # Read file content
            file_ctx.content = self.repo_reader.read_file(file_path)
            file_ctx.size = self.repo_reader.get_file_size(file_path)
            
            if file_ctx.content is None:
                if not self.repo_reader.file_exists(file_path):
                    file_ctx.not_found = True
                elif self.repo_reader.is_file_too_large(file_path):
                    file_ctx.too_large = True
            
            # Get file history (last 5 commits)
            file_ctx.history = self.git_context.get_file_history(file_path, limit=5)
            
            # Get blame for smaller files only
            if file_ctx.size and file_ctx.size < MAX_FILE_SIZE_FOR_FULL_CONTEXT:
                file_ctx.blame = self.git_context.get_blame(file_path)
            
            context.files[file_path] = file_ctx
        
        return context
    
    def _build_partial_context(
        self,
        pr_number: int,
        title: str,
        description: str,
        author: str,
        diff: str,
        changed_files: list[str]
    ) -> PRContext:
        """Build partial context for medium PRs (history but no blame).
        
        Args:
            pr_number: PR number
            title: PR title
            description: PR description
            author: PR author
            diff: PR diff
            changed_files: List of changed file paths
            
        Returns:
            PR context with partial details
        """
        context = PRContext(
            pr_number=pr_number,
            title=title,
            description=description,
            author=author,
            diff=diff,
            strategy="partial"
        )
        
        # Get fewer recent commits
        context.recent_commits = self.git_context.get_recent_commits(limit=5)
        
        # Process each file with limited details
        for file_path in changed_files:
            file_ctx = FileContext(path=file_path)
            
            # Read file content
            file_ctx.content = self.repo_reader.read_file(file_path)
            file_ctx.size = self.repo_reader.get_file_size(file_path)
            
            if file_ctx.content is None:
                if not self.repo_reader.file_exists(file_path):
                    file_ctx.not_found = True
                elif self.repo_reader.is_file_too_large(file_path):
                    file_ctx.too_large = True
            
            # Get limited file history (last 3 commits)
            file_ctx.history = self.git_context.get_file_history(file_path, limit=3)
            
            # Skip blame for medium PRs to save time
            
            context.files[file_path] = file_ctx
        
        return context
    
    def _build_minimal_context(
        self,
        pr_number: int,
        title: str,
        description: str,
        author: str,
        diff: str,
        changed_files: list[str]
    ) -> PRContext:
        """Build minimal context for large PRs (diff and metadata only).
        
        Args:
            pr_number: PR number
            title: PR title
            description: PR description
            author: PR author
            diff: PR diff
            changed_files: List of changed file paths
            
        Returns:
            PR context with minimal details
        """
        context = PRContext(
            pr_number=pr_number,
            title=title,
            description=description,
            author=author,
            diff=diff,
            strategy="minimal"
        )
        
        # No recent commits for large PRs
        
        # Process each file minimally
        for file_path in changed_files:
            file_ctx = FileContext(path=file_path)
            
            # Only check size and existence
            file_ctx.size = self.repo_reader.get_file_size(file_path)
            file_ctx.not_found = not self.repo_reader.file_exists(file_path)
            file_ctx.too_large = self.repo_reader.is_file_too_large(file_path)
            
            # No content, history, or blame for large PRs
            
            context.files[file_path] = file_ctx
        
        return context
    
    def enhance_context_for_file(
        self,
        context: PRContext,
        file_path: str
    ) -> Optional[FileContext]:
        """Enhance context for a specific file (useful for follow-up questions).
        
        Args:
            context: The PR context
            file_path: Path to the file to enhance
            
        Returns:
            Enhanced file context, or None if file not in PR
        """
        if file_path not in context.files:
            logger.warning(f"File {file_path} not in PR context")
            return None
        
        file_ctx = context.files[file_path]
        
        # Add content if missing
        if file_ctx.content is None and not file_ctx.too_large:
            file_ctx.content = self.repo_reader.read_file(file_path)
        
        # Add history if missing
        if not file_ctx.history:
            file_ctx.history = self.git_context.get_file_history(file_path, limit=5)
        
        # Add blame if missing and file is small enough
        if file_ctx.blame is None and file_ctx.size and file_ctx.size < MAX_FILE_SIZE_FOR_FULL_CONTEXT:
            file_ctx.blame = self.git_context.get_blame(file_path)
        
        return file_ctx
    
    def format_context_summary(self, context: PRContext) -> str:
        """Format a human-readable summary of the context.
        
        Args:
            context: The PR context
            
        Returns:
            Formatted summary string
        """
        lines = [
            f"PR #{context.pr_number}: {context.title}",
            f"Author: {context.author}",
            f"Files changed: {context.get_file_count()}",
            f"Strategy: {context.strategy}",
            f"Total context size: ~{context.get_total_context_size() / 1024:.1f} KB",
        ]
        
        if context.recent_commits:
            lines.append(f"Recent commits: {len(context.recent_commits)}")
        
        # File breakdown
        files_with_content = sum(1 for f in context.files.values() if f.content)
        files_with_history = sum(1 for f in context.files.values() if f.history)
        files_with_blame = sum(1 for f in context.files.values() if f.blame)
        
        lines.extend([
            f"Files with content: {files_with_content}/{context.get_file_count()}",
            f"Files with history: {files_with_history}/{context.get_file_count()}",
            f"Files with blame: {files_with_blame}/{context.get_file_count()}",
        ])
        
        return "\n".join(lines)
