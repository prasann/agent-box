"""Data models for PR information."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PRAuthor(BaseModel):
    """Pull request author information."""
    
    login: str
    name: Optional[str] = None


class PRFile(BaseModel):
    """File changed in a pull request."""
    
    path: str
    additions: int
    deletions: int
    changes: int


class PRCommit(BaseModel):
    """Commit in a pull request."""
    
    sha: str
    message: str
    author: str


class PRMetadata(BaseModel):
    """Complete pull request metadata."""
    
    number: int
    title: str
    body: Optional[str] = None
    author: PRAuthor
    state: str
    created_at: Optional[datetime] = Field(default=None, alias="createdAt")
    updated_at: Optional[datetime] = Field(default=None, alias="updatedAt")
    files: list[PRFile] = []
    commits: list[PRCommit] = []
    additions: int = 0
    deletions: int = 0
    changed_files: int = Field(default=0, alias="changedFiles")
    
    class Config:
        populate_by_name = True


class PRData(BaseModel):
    """Complete PR data including metadata and diff."""
    
    metadata: PRMetadata
    diff: str
