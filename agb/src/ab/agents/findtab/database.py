"""Database management for FindTab - LLM-enriched bookmarks."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from .models import EnrichedBookmark


class BookmarkDatabase:
    """Manages the bookmark database with watermark tracking."""
    
    SCHEMA_VERSION = "2.0"
    
    def __init__(self, db_path: str):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (supports ~)
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Auto-initialize schema
        self.initialize()
    
    def initialize(self) -> None:
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Metadata table for tracking state
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Main bookmarks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                
                -- LLM-enriched fields
                category TEXT,
                summary TEXT,
                topics TEXT,
                why_useful TEXT,
                
                -- Visit metadata
                first_visit_at TIMESTAMP,
                last_visit_at TIMESTAMP,
                visit_count INTEGER DEFAULT 1,
                browser TEXT,
                
                -- Index metadata
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                enriched_at TIMESTAMP,
                enrichment_status TEXT DEFAULT 'pending'
            )
        """)
        
        # Indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bookmarks_category 
            ON bookmarks(category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bookmarks_indexed_at 
            ON bookmarks(indexed_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bookmarks_enrichment_status 
            ON bookmarks(enrichment_status)
        """)
        
        # Full-text search index (standalone, not content-linked)
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS bookmarks_fts USING fts5(
                url,
                title,
                summary,
                topics,
                why_useful
            )
        """)
        
        # Triggers to keep FTS in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS bookmarks_fts_insert 
            AFTER INSERT ON bookmarks BEGIN
                INSERT INTO bookmarks_fts(url, title, summary, topics, why_useful)
                VALUES (new.url, new.title, new.summary, new.topics, new.why_useful);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS bookmarks_fts_update 
            AFTER UPDATE ON bookmarks BEGIN
                DELETE FROM bookmarks_fts WHERE url = old.url;
                INSERT INTO bookmarks_fts(url, title, summary, topics, why_useful)
                VALUES (new.url, new.title, new.summary, new.topics, new.why_useful);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS bookmarks_fts_delete 
            AFTER DELETE ON bookmarks BEGIN
                DELETE FROM bookmarks_fts WHERE url = old.url;
            END
        """)
        
        # Set schema version
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', ?)
        """, (self.SCHEMA_VERSION,))
        
        conn.commit()
        conn.close()
    
    # ─────────────────────────────────────────────────────────────
    # Watermark management
    # ─────────────────────────────────────────────────────────────
    
    def get_last_processed_at(self) -> Optional[datetime]:
        """Get timestamp of last successful processing run.
        
        Returns:
            datetime if previously processed, None for first run
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT value FROM metadata WHERE key = 'last_processed_at'"
        )
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return datetime.fromisoformat(row[0])
        return None
    
    def set_last_processed_at(self, timestamp: datetime) -> None:
        """Update the last processed timestamp.
        
        Args:
            timestamp: Time to record as last processed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_processed_at', ?)
        """, (timestamp.isoformat(),))
        
        conn.commit()
        conn.close()
    
    def get_processing_window(self, bootstrap_days: int = 7) -> datetime:
        """Get the start timestamp for processing.
        
        Returns last_processed_at if available, otherwise (now - bootstrap_days).
        
        Args:
            bootstrap_days: Days to look back on first run
            
        Returns:
            Start timestamp for processing window
        """
        last_processed = self.get_last_processed_at()
        if last_processed:
            return last_processed
        return datetime.now() - timedelta(days=bootstrap_days)
    
    # ─────────────────────────────────────────────────────────────
    # Bookmark operations
    # ─────────────────────────────────────────────────────────────
    
    def url_exists(self, url: str) -> bool:
        """Check if URL is already in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM bookmarks WHERE url = ?", (url,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def get_existing_urls(self, urls: list[str]) -> set[str]:
        """Get set of URLs that already exist in database.
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Set of URLs that already exist
        """
        if not urls:
            return set()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(urls))
        cursor.execute(f"SELECT url FROM bookmarks WHERE url IN ({placeholders})", urls)
        existing = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        return existing
    
    def store_pending_bookmarks(self, entries: list[dict]) -> int:
        """Store entries pending enrichment.
        
        Args:
            entries: List of dicts with url, title, first_visit_at, 
                     last_visit_at, visit_count, browser
        
        Returns:
            Number of entries stored
        """
        if not entries:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stored = 0
        for entry in entries:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO bookmarks 
                    (url, title, first_visit_at, last_visit_at, visit_count, browser, enrichment_status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                """, (
                    entry['url'],
                    entry['title'],
                    entry.get('first_visit_at', datetime.now()).isoformat(),
                    entry.get('last_visit_at', datetime.now()).isoformat(),
                    entry.get('visit_count', 1),
                    entry.get('browser', 'unknown'),
                ))
                if cursor.rowcount > 0:
                    stored += 1
            except sqlite3.IntegrityError:
                continue
        
        conn.commit()
        conn.close()
        return stored
    
    def update_bookmark_enrichment(self, url: str, category: str, summary: str, 
                                    topics: list[str], why_useful: str) -> bool:
        """Update bookmark with LLM-enriched data.
        
        Args:
            url: URL to update
            category: Content category
            summary: Brief description
            topics: List of key topics
            why_useful: Reason to revisit
            
        Returns:
            True if updated successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE bookmarks 
                SET category = ?, 
                    summary = ?, 
                    topics = ?, 
                    why_useful = ?,
                    enriched_at = ?,
                    enrichment_status = 'enriched'
                WHERE url = ?
            """, (
                category,
                summary,
                json.dumps(topics),
                why_useful,
                datetime.now().isoformat(),
                url,
            ))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def mark_enrichment_failed(self, url: str) -> None:
        """Mark bookmark enrichment as failed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bookmarks SET enrichment_status = 'failed' WHERE url = ?
        """, (url,))
        
        conn.commit()
        conn.close()
    
    def get_pending_enrichment(self, limit: int = 50) -> list[dict]:
        """Get bookmarks pending enrichment.
        
        Returns:
            List of {id, url, title} dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, url, title FROM bookmarks 
            WHERE enrichment_status = 'pending'
            LIMIT ?
        """, (limit,))
        
        results = [
            {'id': row[0], 'url': row[1], 'title': row[2]}
            for row in cursor.fetchall()
        ]
        conn.close()
        return results
    
    def update_visit_count(self, url: str, last_visit_at: datetime, 
                           additional_visits: int = 1) -> None:
        """Update visit count for existing bookmark."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE bookmarks 
            SET visit_count = visit_count + ?,
                last_visit_at = ?
            WHERE url = ?
        """, (additional_visits, last_visit_at.isoformat(), url))
        
        conn.commit()
        conn.close()
    
    # ─────────────────────────────────────────────────────────────
    # Search operations
    # ─────────────────────────────────────────────────────────────
    
    def search(self, query: str, limit: int = 10, since: Optional[str] = None) -> list[dict]:
        """Search bookmarks using FTS5.
        
        Args:
            query: Search query
            limit: Maximum results
            since: Optional date string (YYYY-MM-DD) to filter by last_visit_at
            
        Returns:
            List of matching bookmarks
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if since:
            cursor.execute("""
                SELECT 
                    b.id, b.url, b.title, b.category, b.summary, 
                    b.topics, b.why_useful, b.last_visit_at, b.visit_count,
                    bm25(bookmarks_fts) as rank
                FROM bookmarks_fts fts
                JOIN bookmarks b ON fts.url = b.url
                WHERE bookmarks_fts MATCH ?
                  AND b.last_visit_at >= ?
                ORDER BY rank
                LIMIT ?
            """, (query, since, limit))
        else:
            cursor.execute("""
                SELECT 
                    b.id, b.url, b.title, b.category, b.summary, 
                    b.topics, b.why_useful, b.last_visit_at, b.visit_count,
                    bm25(bookmarks_fts) as rank
                FROM bookmarks_fts fts
                JOIN bookmarks b ON fts.url = b.url
                WHERE bookmarks_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'topics': json.loads(row[5]) if row[5] else [],
                'why_useful': row[6],
                'last_visit_at': datetime.fromisoformat(row[7]) if row[7] else None,
                'visit_count': row[8],
                'rank': row[9],
            })
        
        conn.close()
        return results
    
    def list_by_category(self, category: str, limit: int = 20) -> list[dict]:
        """List bookmarks by category using direct SQL.
        
        Args:
            category: Category to filter (docs, article, discussion, code, reference)
            limit: Maximum results
            
        Returns:
            List of bookmarks in the given category
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, url, title, category, summary, topics,
                   why_useful, last_visit_at, visit_count
            FROM bookmarks
            WHERE category = ? AND enrichment_status = 'enriched'
            ORDER BY last_visit_at DESC
            LIMIT ?
        """, (category, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'topics': json.loads(row[5]) if row[5] else [],
                'why_useful': row[6],
                'last_visit_at': datetime.fromisoformat(row[7]) if row[7] else None,
                'visit_count': row[8],
            })
        
        conn.close()
        return results
    
    def list_recent(self, limit: int = 20) -> list[dict]:
        """List recently indexed bookmarks.
        
        Returns:
            List of recent bookmarks
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, url, title, category, summary, topics, 
                   why_useful, last_visit_at, visit_count, indexed_at
            FROM bookmarks 
            WHERE enrichment_status = 'enriched'
            ORDER BY indexed_at DESC
            LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'url': row[1],
                'title': row[2],
                'category': row[3],
                'summary': row[4],
                'topics': json.loads(row[5]) if row[5] else [],
                'why_useful': row[6],
                'last_visit_at': datetime.fromisoformat(row[7]) if row[7] else None,
                'visit_count': row[8],
                'indexed_at': datetime.fromisoformat(row[9]) if row[9] else None,
            })
        
        conn.close()
        return results
    
    # ─────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM bookmarks")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bookmarks WHERE enrichment_status = 'enriched'")
        enriched = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bookmarks WHERE enrichment_status = 'pending'")
        pending = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bookmarks WHERE enrichment_status = 'failed'")
        failed = cursor.fetchone()[0]
        
        # Category breakdown
        cursor.execute("""
            SELECT category, COUNT(*) FROM bookmarks 
            WHERE category IS NOT NULL 
            GROUP BY category
        """)
        categories = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Date range
        cursor.execute("SELECT MIN(first_visit_at), MAX(last_visit_at) FROM bookmarks")
        oldest, newest = cursor.fetchone()
        
        # Browsers
        cursor.execute("SELECT DISTINCT browser FROM bookmarks WHERE browser IS NOT NULL")
        browsers = [row[0] for row in cursor.fetchall()]
        
        # Last processed
        cursor.execute("SELECT value FROM metadata WHERE key = 'last_processed_at'")
        row = cursor.fetchone()
        last_processed = row[0] if row else None
        
        conn.close()
        
        return {
            'total': total,
            'enriched': enriched,
            'pending': pending,
            'failed': failed,
            'categories': categories,
            'oldest': oldest,
            'newest': newest,
            'browsers': browsers,
            'last_processed_at': last_processed,
            'db_path': str(self.db_path),
        }
    
    def delete_bookmark(self, url: str) -> bool:
        """Delete a bookmark by URL."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM bookmarks WHERE url = ?", (url,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
