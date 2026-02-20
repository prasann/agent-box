"""Data models for Find That Tab v2."""
from datetime import datetime, timedelta
from typing import Optional, Literal
from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    """A browser history entry (raw from browser)."""
    
    url: str
    title: str
    visit_time: datetime
    visit_count: int = 1
    browser: str = "chrome"


class ClassifiedEntry(BaseModel):
    """Entry after LLM classification."""
    
    url: str
    title: str
    visit_time: datetime
    visit_count: int = 1
    browser: str = "chrome"
    
    # Classification result
    should_save: bool = False
    classification_reason: Optional[str] = None


class EnrichedBookmark(BaseModel):
    """Bookmark enriched with LLM-generated metadata."""
    
    url: str
    title: str
    
    # LLM-enriched fields
    category: Literal['docs', 'article', 'discussion', 'code', 'reference'] = 'article'
    summary: str = ""
    topics: list[str] = Field(default_factory=list)
    why_useful: str = ""
    
    # Visit metadata
    first_visit_at: datetime = Field(default_factory=datetime.now)
    last_visit_at: datetime = Field(default_factory=datetime.now)
    visit_count: int = 1
    browser: str = "chrome"


class BookmarkSearchResult(BaseModel):
    """A search result from the bookmark index."""
    
    id: int
    url: str
    title: str
    category: Optional[str] = None
    summary: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    why_useful: Optional[str] = None
    last_visit_at: Optional[datetime] = None
    visit_count: int = 1
    rank: float = 0.0
    
    def time_ago(self) -> str:
        """Human-readable time since last visit."""
        if not self.last_visit_at:
            return "Unknown"
        
        now = datetime.now()
        delta = now - self.last_visit_at
        
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
    
    @property
    def category_emoji(self) -> str:
        """Emoji for category display."""
        return {
            'docs': '📚',
            'article': '📝',
            'discussion': '💬',
            'code': '💻',
            'reference': '📖',
        }.get(self.category or '', '📄')
