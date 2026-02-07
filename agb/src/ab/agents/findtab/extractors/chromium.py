"""Chromium-based browser history extractor (Chrome, Edge, etc.)."""
import sqlite3
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from .base import BrowserExtractor
from ..models import HistoryEntry


class ChromiumExtractor(BrowserExtractor):
    """Extract history from Chromium-based browsers (Chrome, Edge)."""
    
    def __init__(self, browser_type: str = "edge"):
        """Initialize extractor.
        
        Args:
            browser_type: 'chrome' or 'edge'
        """
        self.browser_type = browser_type.lower()
        self._browser_paths = {
            "chrome": "Google/Chrome",
            "edge": "Microsoft Edge",
        }
        
    @property
    def browser_name(self) -> str:
        return self.browser_type
    
    def detect(self) -> bool:
        """Check if browser is installed."""
        return self.get_history_db_path().exists()
    
    def get_history_db_path(self) -> Path:
        """Get the path to the browser's history database."""
        browser_path = self._browser_paths.get(self.browser_type)
        if not browser_path:
            raise ValueError(f"Unknown browser type: {self.browser_type}")
            
        return Path.home() / "Library/Application Support" / browser_path / "Default/History"
    
    def extract(self, hours_back: int = 24) -> list[HistoryEntry]:
        """Extract history from Chromium browser.
        
        Args:
            hours_back: How many hours of history to extract
            
        Returns:
            List of HistoryEntry objects
        """
        history_db = self.get_history_db_path()
        
        if not history_db.exists():
            return []
        
        # Copy database to temp location (it's locked when browser is open)
        temp_db = Path(f"/tmp/{self.browser_type}_history_copy.db")
        try:
            shutil.copy(history_db, temp_db)
        except Exception as e:
            print(f"Warning: Could not copy {self.browser_type} history: {e}")
            return []
        
        try:
            entries = self._extract_from_db(temp_db, hours_back)
        finally:
            # Clean up temp file
            if temp_db.exists():
                temp_db.unlink()
        
        return entries
    
    def _extract_from_db(self, db_path: Path, hours_back: int) -> list[HistoryEntry]:
        """Extract entries from the copied database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff time in Chrome timestamp format
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        chrome_cutoff = self._to_chrome_timestamp(cutoff_time)
        
        # Query history
        query = """
            SELECT urls.url, urls.title, visits.visit_time, urls.visit_count
            FROM urls
            JOIN visits ON urls.id = visits.url
            WHERE visits.visit_time > ?
            ORDER BY visits.visit_time DESC
        """
        
        try:
            cursor.execute(query, (chrome_cutoff,))
        except sqlite3.OperationalError as e:
            print(f"Warning: Could not query {self.browser_type} history: {e}")
            conn.close()
            return []
        
        entries = []
        for url, title, visit_time, visit_count in cursor.fetchall():
            # Skip empty or invalid URLs
            if not url or url.startswith(('chrome://', 'edge://', 'about:')):
                continue
                
            entries.append(HistoryEntry(
                url=url,
                title=title or "Untitled",
                visit_time=self._from_chrome_timestamp(visit_time),
                visit_count=visit_count or 1,
                browser=self.browser_type,
            ))
        
        conn.close()
        return entries
    
    @staticmethod
    def _to_chrome_timestamp(dt: datetime) -> int:
        """Convert datetime to Chrome timestamp (microseconds since 1601-01-01)."""
        epoch = datetime(1601, 1, 1)
        delta = dt - epoch
        return int(delta.total_seconds() * 1_000_000)
    
    @staticmethod
    def _from_chrome_timestamp(chrome_ts: int) -> datetime:
        """Convert Chrome timestamp to datetime."""
        epoch = datetime(1601, 1, 1)
        return epoch + timedelta(microseconds=chrome_ts)


# Convenience factory functions
def create_chrome_extractor() -> ChromiumExtractor:
    """Create a Chrome history extractor."""
    return ChromiumExtractor("chrome")


def create_edge_extractor() -> ChromiumExtractor:
    """Create an Edge history extractor."""
    return ChromiumExtractor("edge")
