"""Repository file reader with size limits and error handling."""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RepoReader:
    """Read files from a git repository with safety limits."""
    
    # 1MB limit for files to prevent memory issues
    MAX_FILE_SIZE = 1_000_000
    
    def __init__(self, repo_root: Path | str):
        """Initialize the repository reader.
        
        Args:
            repo_root: Path to the repository root directory
        """
        self.repo_root = Path(repo_root)
        
        if not self.repo_root.exists():
            raise ValueError(f"Repository root does not exist: {self.repo_root}")
        
        if not self.repo_root.is_dir():
            raise ValueError(f"Repository root is not a directory: {self.repo_root}")
    
    def read_file(self, relative_path: str) -> Optional[str]:
        """Read a file from the repository.
        
        Args:
            relative_path: Path relative to repository root
            
        Returns:
            File contents as string, or None if file cannot be read
        """
        file_path = self.repo_root / relative_path
        
        # Check if file exists
        if not file_path.exists():
            logger.warning(f"File not found: {relative_path}")
            return None
        
        # Check if it's actually a file
        if not file_path.is_file():
            logger.warning(f"Path is not a file: {relative_path}")
            return None
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            logger.warning(
                f"File too large to read: {relative_path} "
                f"({file_size} bytes, max {self.MAX_FILE_SIZE})"
            )
            return None
        
        # Try to read the file
        try:
            return file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"File is not valid UTF-8: {relative_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading file {relative_path}: {e}")
            return None
    
    def read_files(self, relative_paths: list[str]) -> dict[str, Optional[str]]:
        """Read multiple files from the repository.
        
        Args:
            relative_paths: List of paths relative to repository root
            
        Returns:
            Dictionary mapping paths to their contents (or None if unreadable)
        """
        return {path: self.read_file(path) for path in relative_paths}
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if a file exists in the repository.
        
        Args:
            relative_path: Path relative to repository root
            
        Returns:
            True if file exists, False otherwise
        """
        file_path = self.repo_root / relative_path
        return file_path.exists() and file_path.is_file()
    
    def get_file_size(self, relative_path: str) -> Optional[int]:
        """Get the size of a file in bytes.
        
        Args:
            relative_path: Path relative to repository root
            
        Returns:
            File size in bytes, or None if file doesn't exist
        """
        file_path = self.repo_root / relative_path
        
        if not file_path.exists() or not file_path.is_file():
            return None
        
        return file_path.stat().st_size
    
    def is_file_too_large(self, relative_path: str) -> bool:
        """Check if a file exceeds the size limit.
        
        Args:
            relative_path: Path relative to repository root
            
        Returns:
            True if file is too large or doesn't exist, False otherwise
        """
        size = self.get_file_size(relative_path)
        return size is None or size > self.MAX_FILE_SIZE
