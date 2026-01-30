"""PR data fetching using gh CLI."""

import json
import subprocess
from typing import Optional

from rich.console import Console

from ..models import PRData, PRMetadata

console = Console()


class PRFetchError(Exception):
    """Error fetching PR data."""
    pass


def check_gh_auth() -> bool:
    """Check if gh CLI is authenticated.
    
    Returns:
        True if authenticated, False otherwise
    """
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def fetch_pr_metadata(pr_number: int, owner: str, repo: str) -> PRMetadata:
    """Fetch PR metadata using gh CLI.
    
    Args:
        pr_number: Pull request number
        owner: Repository owner
        repo: Repository name
        
    Returns:
        PRMetadata object
        
    Raises:
        PRFetchError: If fetching fails
    """
    if not check_gh_auth():
        raise PRFetchError(
            "GitHub CLI (gh) is not authenticated. Please run: gh auth login"
        )
    
    try:
        # Fetch PR data with all required fields
        result = subprocess.run(
            [
                "gh", "pr", "view", str(pr_number),
                "--repo", f"{owner}/{repo}",
                "--json", "number,title,body,author,state,createdAt,updatedAt,"
                         "files,commits,additions,deletions,changedFiles"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        data = json.loads(result.stdout)
        
        # Transform the data to match our model
        # gh returns files as array with additions/deletions
        if "files" in data:
            data["files"] = [
                {
                    "path": f["path"],
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                    "changes": f.get("additions", 0) + f.get("deletions", 0)
                }
                for f in data["files"]
            ]
        
        # Transform commits
        if "commits" in data:
            data["commits"] = [
                {
                    "sha": c["oid"],
                    "message": c["messageHeadline"],
                    "author": c["authors"][0]["login"] if c.get("authors") else "unknown"
                }
                for c in data["commits"]
            ]
        
        return PRMetadata.model_validate(data)
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        if "Could not resolve to a PullRequest" in error_msg:
            raise PRFetchError(f"PR #{pr_number} not found in {owner}/{repo}")
        raise PRFetchError(f"Failed to fetch PR metadata: {error_msg}")
    except json.JSONDecodeError as e:
        raise PRFetchError(f"Failed to parse PR metadata: {e}")
    except Exception as e:
        raise PRFetchError(f"Unexpected error fetching PR: {e}")


def fetch_pr_diff(pr_number: int, owner: str, repo: str) -> str:
    """Fetch PR diff using gh CLI.
    
    Args:
        pr_number: Pull request number
        owner: Repository owner
        repo: Repository name
        
    Returns:
        PR diff as string
        
    Raises:
        PRFetchError: If fetching fails
    """
    try:
        result = subprocess.run(
            [
                "gh", "pr", "diff", str(pr_number),
                "--repo", f"{owner}/{repo}"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise PRFetchError(f"Failed to fetch PR diff: {error_msg}")


def fetch_pr_data(pr_number: int, owner: str, repo: str) -> PRData:
    """Fetch complete PR data (metadata + diff).
    
    Args:
        pr_number: Pull request number
        owner: Repository owner
        repo: Repository name
        
    Returns:
        PRData object with metadata and diff
        
    Raises:
        PRFetchError: If fetching fails
    """
    console.print(f"[dim]Fetching PR metadata...[/dim]")
    metadata = fetch_pr_metadata(pr_number, owner, repo)
    
    console.print(f"[dim]Fetching PR diff...[/dim]")
    diff = fetch_pr_diff(pr_number, owner, repo)
    
    return PRData(metadata=metadata, diff=diff)
