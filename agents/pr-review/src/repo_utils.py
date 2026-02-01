"""Repository operations and validation."""

import subprocess
from .gh_utils import run_gh_command, GhError


class RepoError(Exception):
    """Repository operation error."""
    pass


def check_repo_clean() -> bool:
    """Check if repo has uncommitted changes.
    
    Returns:
        True if repo is clean, False if there are uncommitted changes
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    return len(result.stdout.strip()) == 0


def get_current_branch() -> str:
    """Get current git branch.
    
    Returns:
        Name of current branch
        
    Raises:
        RepoError: If not in a git repository
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RepoError("Not in a git repository")


def get_repo_root() -> str:
    """Get repository root directory.
    
    Returns:
        Absolute path to repository root
        
    Raises:
        RepoError: If not in a git repository
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        raise RepoError("Not in a git repository")


def checkout_pr(pr_number: int) -> tuple[str, str]:
    """Check out PR branch.
    
    Args:
        pr_number: Pull request number
        
    Returns:
        Tuple of (repo_path, original_branch)
        
    Raises:
        RepoError: If repo has uncommitted changes or checkout fails
    """
    # Safety check
    if not check_repo_clean():
        raise RepoError(
            "Repository has uncommitted changes. "
            "Please commit or stash them before reviewing PRs."
        )
    
    # Remember current state
    try:
        original_branch = get_current_branch()
        repo_path = get_repo_root()
    except RepoError as e:
        raise RepoError(f"Failed to get repository info: {e}")
    
    # Checkout PR
    try:
        run_gh_command(["pr", "checkout", str(pr_number)])
        return repo_path, original_branch
    except GhError as e:
        raise RepoError(f"Failed to checkout PR: {e}")


def restore_branch(branch: str) -> None:
    """Switch back to original branch.
    
    Args:
        branch: Branch name to restore
        
    Raises:
        RepoError: If checkout fails
    """
    try:
        subprocess.run(
            ["git", "checkout", branch],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        raise RepoError(f"Failed to restore branch: {e.stderr}")
