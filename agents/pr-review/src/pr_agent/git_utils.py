"""Utilities for working with git repositories."""

import re
import subprocess
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class RepoInfo(BaseModel):
    """Repository information."""
    
    owner: str
    repo: str
    root: Path


class GitError(Exception):
    """Git operation error."""
    pass


def get_repo_root() -> Path:
    """Get the root directory of the current git repository.
    
    Returns:
        Path to the repository root
        
    Raises:
        GitError: If not in a git repository
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        raise GitError("Not in a git repository. Please run this command from within a git repo.")


def get_remote_url() -> str:
    """Get the origin remote URL.
    
    Returns:
        Remote URL string
        
    Raises:
        GitError: If no remote origin is configured
    """
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise GitError("No remote origin configured for this repository.")


def parse_github_url(url: str) -> tuple[str, str]:
    """Parse GitHub owner and repo from a remote URL.
    
    Args:
        url: Git remote URL (HTTPS or SSH format)
        
    Returns:
        Tuple of (owner, repo)
        
    Raises:
        GitError: If URL is not a valid GitHub URL
        
    Examples:
        >>> parse_github_url("https://github.com/owner/repo.git")
        ('owner', 'repo')
        >>> parse_github_url("git@github.com:owner/repo.git")
        ('owner', 'repo')
    """
    # HTTPS format: https://github.com/owner/repo.git
    https_pattern = r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$"
    
    # SSH format: git@github.com:owner/repo.git
    ssh_pattern = r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$"
    
    for pattern in [https_pattern, ssh_pattern]:
        match = re.match(pattern, url)
        if match:
            return match.group(1), match.group(2)
    
    raise GitError(f"Not a valid GitHub URL: {url}")


def get_repo_info() -> RepoInfo:
    """Get complete repository information.
    
    Returns:
        RepoInfo with owner, repo, and root path
        
    Raises:
        GitError: If not in a valid GitHub repository
    """
    root = get_repo_root()
    url = get_remote_url()
    owner, repo = parse_github_url(url)
    
    return RepoInfo(owner=owner, repo=repo, root=root)
