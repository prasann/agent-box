"""Database management for Find That Tab index."""
import sqlite3
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from .models import EnrichedEntry


class IndexDatabase:
    """Manages the local search index database."""
    
    def __init__(self, db_path: Path):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def initialize(self):
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history_entries (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                visit_time TIMESTAMP NOT NULL,
                visit_count INTEGER DEFAULT 1,
                keywords TEXT,
                summary TEXT,
                browser TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                search_text TEXT,
                UNIQUE(url, visit_time)
            )
        """)
        
        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_visit_time 
            ON history_entries(visit_time DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_browser 
            ON history_entries(browser)
        """)
        
        # Full-text search (SQLite FTS5)
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS history_fts USING fts5(
                url,
                title,
                keywords,
                summary,
                content='history_entries',
                content_rowid='rowid'
            )
        """)
        
        # Triggers to keep FTS in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS history_fts_insert 
            AFTER INSERT ON history_entries BEGIN
                INSERT INTO history_fts(rowid, url, title, keywords, summary)
                VALUES (new.rowid, new.url, new.title, new.keywords, new.summary);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS history_fts_delete 
            AFTER DELETE ON history_entries BEGIN
                DELETE FROM history_fts WHERE rowid = old.rowid;
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS history_fts_update 
            AFTER UPDATE ON history_entries BEGIN
                UPDATE history_fts 
                SET url = new.url, 
                    title = new.title, 
                    keywords = new.keywords, 
                    summary = new.summary
                WHERE rowid = new.rowid;
            END
        """)
        
        conn.commit()
        conn.close()
    
    def already_indexed(self, url: str, visit_time: datetime) -> bool:
        """Check if an entry is already in the index."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM history_entries WHERE url = ? AND visit_time = ?",
            (url, visit_time.isoformat())
        )
        
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def store_entries(self, entries: list[EnrichedEntry]) -> int:
        """Store enriched entries in the index.
        
        Args:
            entries: List of enriched entries to store
            
        Returns:
            Number of entries stored
        """
        if not entries:
            return 0
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stored_count = 0
        for entry in entries:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO history_entries 
                    (id, url, title, visit_time, visit_count, keywords, summary, browser, search_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.id,
                    entry.url,
                    entry.title,
                    entry.visit_time.isoformat(),
                    entry.visit_count,
                    json.dumps(entry.keywords),
                    entry.summary,
                    entry.browser,
                    entry.search_text,
                ))
                
                if cursor.rowcount > 0:
                    stored_count += 1
                    
            except sqlite3.IntegrityError:
                # Duplicate entry, skip
                continue
        
        conn.commit()
        conn.close()
        
        return stored_count
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM history_entries")
        total = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(visit_time), MAX(visit_time) FROM history_entries")
        oldest, newest = cursor.fetchone()
        
        # Browsers
        cursor.execute("SELECT DISTINCT browser FROM history_entries")
        browsers = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total": total,
            "oldest": oldest,
            "newest": newest,
            "browsers": browsers,
        }
