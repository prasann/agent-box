"""Data models for Find That Tab."""
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class HistoryEntry(BaseModel):
    """A browser history entry."""
    
    url: str
    title: str
    visit_time: datetime
    visit_count: int = 1
    browser: str = "chrome"
    
    
class EnrichedEntry(HistoryEntry):
    """History entry enriched with metadata."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    keywords: list[str] = Field(default_factory=list)
    summary: Optional[str] = None
    indexed_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def search_text(self) -> str:
        """Combined text for search indexing."""
        return ' '.join(filter(None, [
            self.title,
            self.url,
            ' '.join(self.keywords),
            self.summary or '',
        ]))


class SearchResult(BaseModel):
    """A search result with relevance scoring."""
    
    url: str
    title: str
    visit_time: datetime
    summary: Optional[str] = None
    visit_count: int = 1
    relevance_score: float = 0.0
    
    def time_ago(self) -> str:
        """Human-readable time since visit."""
        now = datetime.now()
        delta = now - self.visit_time
        
        if delta < timedelta(minutes=1):
            return "Just now"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes}m ago"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        elif delta < timedelta(days=7):
            days = delta.days
            return f"{days}d ago"
        elif delta < timedelta(days=30):
            weeks = delta.days // 7
            return f"{weeks}w ago"
        else:
            months = delta.days // 30
            return f"{months}mo ago"
