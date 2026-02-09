"""Pydantic models for shell history."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    """A single entry in shell history."""
    
    command: str = Field(..., description="The command that was executed")
    timestamp: Optional[datetime] = Field(None, description="When the command was executed")
    elapsed_seconds: Optional[int] = Field(None, description="How long the command took")
    exit_code: Optional[int] = Field(None, description="Exit code of the command")
    
    def to_zsh_format(self) -> str:
        """Convert entry back to zsh extended history format."""
        if self.timestamp and self.elapsed_seconds is not None:
            # Extended format: : timestamp:elapsed;command
            unix_timestamp = int(self.timestamp.timestamp())
            return f": {unix_timestamp}:{self.elapsed_seconds};{self.command}"
        else:
            # Simple format: just the command
            return self.command
    
    class Config:
        """Pydantic config."""
        frozen = False
