"""Search module for FindTab - FTS5 based search."""
from datetime import datetime
from .database import BookmarkDatabase
from .models import BookmarkSearchResult


class BookmarkSearcher:
    """Search bookmarks using SQLite FTS5."""
    
    def __init__(self, db: BookmarkDatabase):
        """Initialize searcher.
        
        Args:
            db: Bookmark database instance
        """
        self.db = db
    
    def search(self, query: str, limit: int = 10) -> list[BookmarkSearchResult]:
        """Search bookmarks by query.
        
        Uses FTS5 full-text search with BM25 ranking.
        
        Args:
            query: Search query (natural language)
            limit: Maximum results to return
            
        Returns:
            List of matching bookmarks, ranked by relevance
        """
        # Clean query for FTS5
        fts_query = self._prepare_query(query)
        
        results = self.db.search(fts_query, limit=limit)
        
        return [
            BookmarkSearchResult(
                id=r['id'],
                url=r['url'],
                title=r['title'],
                category=r['category'],
                summary=r['summary'],
                topics=r['topics'],
                why_useful=r['why_useful'],
                last_visit_at=r['last_visit_at'],
                visit_count=r['visit_count'],
                rank=r['rank'],
            )
            for r in results
        ]
    
    def _prepare_query(self, query: str) -> str:
        """Prepare query for FTS5 MATCH.
        
        Converts natural language query to FTS5 syntax.
        Simple approach: treat as OR of all words.
        
        Args:
            query: Raw user query
            
        Returns:
            FTS5-compatible query string
        """
        # Remove special FTS5 characters that could cause syntax errors
        special_chars = ['"', "'", '(', ')', '*', '-', '+', ':', '^', '~']
        cleaned = query
        for char in special_chars:
            cleaned = cleaned.replace(char, ' ')
        
        # Split into words and filter
        words = [w.strip().lower() for w in cleaned.split() if len(w.strip()) > 1]
        
        if not words:
            return query
        
        # Join with OR for broader matching
        return ' OR '.join(words)
    
    def list_recent(self, limit: int = 20) -> list[BookmarkSearchResult]:
        """List recently indexed bookmarks.
        
        Args:
            limit: Maximum results
            
        Returns:
            Recent bookmarks ordered by index time
        """
        results = self.db.list_recent(limit=limit)
        
        return [
            BookmarkSearchResult(
                id=r['id'],
                url=r['url'],
                title=r['title'],
                category=r['category'],
                summary=r['summary'],
                topics=r['topics'],
                why_useful=r['why_useful'],
                last_visit_at=r['last_visit_at'],
                visit_count=r['visit_count'],
                rank=0.0,
            )
            for r in results
        ]
    
    def list_by_category(self, category: str, limit: int = 20) -> list[BookmarkSearchResult]:
        """List bookmarks by category.
        
        Args:
            category: Category to filter (docs, article, discussion, code, reference)
            limit: Maximum results
            
        Returns:
            Bookmarks in that category
        """
        # Use FTS5 to search within category
        # This leverages the existing search but filtered
        query = f'category:{category}'
        return self.search(query, limit=limit)
