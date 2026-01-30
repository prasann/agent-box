"""Git context gathering utilities for code review."""

import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    """Information about a git commit."""
    hash: str
    short_hash: str
    author: str
    date: str
    message: str


@dataclass
class BlameLine:
    """Information about a line from git blame."""
    commit_hash: str
    author: str
    timestamp: str
    line_number: int
    content: str


class GitContext:
    """Gather git context for code review."""
    
    def __init__(self, repo_root: Path | str):
        """Initialize the git context gatherer.
        
        Args:
            repo_root: Path to the repository root directory
        """
        self.repo_root = Path(repo_root)
        
        if not self._is_git_repo():
            raise ValueError(f"Not a git repository: {self.repo_root}")
    
    def _is_git_repo(self) -> bool:
        """Check if the directory is a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking if git repo: {e}")
            return False
    
    def get_file_history(self, file_path: str, limit: int = 10) -> list[CommitInfo]:
        """Get the commit history for a specific file.
        
        Args:
            file_path: Path to the file (relative to repo root)
            limit: Maximum number of commits to retrieve
            
        Returns:
            List of commit information
        """
        try:
            # Format: hash|author|date|message
            result = subprocess.run(
                [
                    'git', 'log',
                    f'-{limit}',
                    '--format=%H|%h|%an|%ad|%s',
                    '--date=iso',
                    '--',
                    file_path
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get history for {file_path}: {result.stderr}")
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append(CommitInfo(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        date=parts[3],
                        message=parts[4]
                    ))
            
            return commits
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting history for {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error getting history for {file_path}: {e}")
            return []
    
    def get_blame(self, file_path: str) -> Optional[str]:
        """Get git blame output for a file.
        
        Args:
            file_path: Path to the file (relative to repo root)
            
        Returns:
            Raw git blame output, or None if failed
        """
        try:
            result = subprocess.run(
                ['git', 'blame', '--', file_path],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get blame for {file_path}: {result.stderr}")
                return None
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting blame for {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error getting blame for {file_path}: {e}")
            return None
    
    def get_blame_for_lines(
        self, 
        file_path: str, 
        start_line: int, 
        end_line: int
    ) -> Optional[str]:
        """Get git blame for a specific range of lines.
        
        Args:
            file_path: Path to the file (relative to repo root)
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (inclusive)
            
        Returns:
            Git blame output for the line range, or None if failed
        """
        try:
            result = subprocess.run(
                [
                    'git', 'blame',
                    f'-L{start_line},{end_line}',
                    '--',
                    file_path
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(
                    f"Failed to get blame for {file_path}:{start_line}-{end_line}: "
                    f"{result.stderr}"
                )
                return None
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting blame for {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error getting blame for {file_path}: {e}")
            return None
    
    def get_recent_commits(self, limit: int = 20) -> list[CommitInfo]:
        """Get recent commits in the repository.
        
        Args:
            limit: Maximum number of commits to retrieve
            
        Returns:
            List of recent commit information
        """
        try:
            result = subprocess.run(
                [
                    'git', 'log',
                    f'-{limit}',
                    '--format=%H|%h|%an|%ad|%s',
                    '--date=iso'
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get recent commits: {result.stderr}")
                return []
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append(CommitInfo(
                        hash=parts[0],
                        short_hash=parts[1],
                        author=parts[2],
                        date=parts[3],
                        message=parts[4]
                    ))
            
            return commits
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout getting recent commits")
            return []
        except Exception as e:
            logger.error(f"Error getting recent commits: {e}")
            return []
    
    def get_commit_diff(self, commit_hash: str) -> Optional[str]:
        """Get the diff for a specific commit.
        
        Args:
            commit_hash: The commit hash
            
        Returns:
            Commit diff, or None if failed
        """
        try:
            result = subprocess.run(
                ['git', 'show', commit_hash],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to get diff for commit {commit_hash}: {result.stderr}")
                return None
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting diff for commit {commit_hash}")
            return None
        except Exception as e:
            logger.error(f"Error getting diff for commit {commit_hash}: {e}")
            return None
    
    def get_file_at_commit(self, file_path: str, commit_hash: str) -> Optional[str]:
        """Get the contents of a file at a specific commit.
        
        Args:
            file_path: Path to the file (relative to repo root)
            commit_hash: The commit hash
            
        Returns:
            File contents at that commit, or None if failed
        """
        try:
            result = subprocess.run(
                ['git', 'show', f'{commit_hash}:{file_path}'],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.warning(
                    f"Failed to get {file_path} at {commit_hash}: {result.stderr}"
                )
                return None
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout getting {file_path} at {commit_hash}")
            return None
        except Exception as e:
            logger.error(f"Error getting {file_path} at {commit_hash}: {e}")
            return None
