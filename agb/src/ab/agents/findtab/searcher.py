"""Search engine for indexed history."""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
from .models import SearchResult


class HistorySearcher:
    """Search indexed browser history."""
    
    def __init__(self, db_path: Path):
        """Initialize searcher.
        
        Args:
            db_path: Path to index database
        """
        self.db_path = Path(db_path).expanduser()
    
    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search history by query text.
        
        Args:
            query: Search query (can be natural language)
            limit: Maximum number of results
            
        Returns:
            List of search results, ranked by relevance
        """
        if not self.db_path.exists():
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple keyword-based FTS5 search
        # For MVP, we'll use the query directly
        # In Phase 2, we'd extract keywords with LLM
        
        try:
            cursor.execute("""
                SELECT 
                    e.url, 
                    e.title, 
                    e.visit_time, 
                    e.summary,
                    e.visit_count,
                    bm25(history_fts) as rank
                FROM history_fts
                JOIN history_entries e ON history_fts.rowid = e.rowid
                WHERE history_fts MATCH ?
                ORDER BY rank, e.visit_time DESC
                LIMIT ?
            """, (query, limit))
            
            results = []
            for url, title, visit_time, summary, visit_count, rank in cursor.fetchall():
                results.append(SearchResult(
                    url=url,
                    title=title,
                    visit_time=datetime.fromisoformat(visit_time),
                    summary=summary,
                    visit_count=visit_count,
                    relevance_score=abs(rank),  # BM25 scores are negative
                ))
            
        except sqlite3.OperationalError:
            # FTS query error, try simple LIKE search as fallback
            results = self._fallback_search(cursor, query, limit)
        
        conn.close()
        return results
    
    def _fallback_search(self, cursor, query: str, limit: int) -> list[SearchResult]:
        """Fallback to simple LIKE search if FTS fails."""
        query_pattern = f"%{query}%"
        
        cursor.execute("""
            SELECT 
                url, 
                title, 
                visit_time, 
                summary,
                visit_count
            FROM history_entries
            WHERE title LIKE ? OR url LIKE ? OR keywords LIKE ?
            ORDER BY visit_time DESC
            LIMIT ?
        """, (query_pattern, query_pattern, query_pattern, limit))
        
        results = []
        for url, title, visit_time, summary, visit_count in cursor.fetchall():
            results.append(SearchResult(
                url=url,
                title=title,
                visit_time=datetime.fromisoformat(visit_time),
                summary=summary,
                visit_count=visit_count,
                relevance_score=1.0,
            ))
        
        return results
