"""GitHub CLI wrapper utilities."""

import json
import subprocess
from typing import Any


class GhError(Exception):
    """GitHub CLI error."""
    pass


def run_gh_command(args: list[str]) -> str:
    """Run a gh CLI command and return output.
    
    Args:
        args: Command arguments to pass to gh
        
    Returns:
        Command output as string
        
    Raises:
        GhError: If command fails
    """
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GhError(f"gh command failed: {e.stderr}")
    except FileNotFoundError:
        raise GhError("gh CLI not found. Install with: brew install gh")


def get_pr_diff(pr_number: int) -> str:
    """Get PR diff using gh CLI.
    
    Args:
        pr_number: Pull request number
        
    Returns:
        PR diff as string
    """
    return run_gh_command(["pr", "diff", str(pr_number)])


def get_pr_info(pr_number: int) -> dict[str, Any]:
    """Get PR metadata using gh CLI.
    
    Args:
        pr_number: Pull request number
        
    Returns:
        PR metadata as dict
    """
    output = run_gh_command([
        "pr", "view", str(pr_number),
        "--json", "number,title,body,author,state,files,additions,deletions"
    ])
    return json.loads(output)


def post_pr_comment(pr_number: int, comment: str) -> None:
    """Post a comment on a PR.
    
    Args:
        pr_number: Pull request number
        comment: Comment text to post
    """
    run_gh_command(["pr", "comment", str(pr_number), "--body", comment])


def post_pr_review(pr_number: int, comment: str, event: str = "COMMENT") -> None:
    """Post a review on a PR.
    
    Args:
        pr_number: Pull request number
        comment: Review comment text
        event: Review event type (COMMENT, APPROVE, REQUEST_CHANGES)
    """
    run_gh_command(["pr", "review", str(pr_number), "--body", comment, "--" + event.lower()])
