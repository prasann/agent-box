"""Base browser history extractor interface."""
from abc import ABC, abstractmethod
from pathlib import Path
from ..models import HistoryEntry


class BrowserExtractor(ABC):
    """Base class for browser history extractors."""
    
    @abstractmethod
    def detect(self) -> bool:
        """Check if this browser is installed."""
        pass
    
    @abstractmethod
    def get_history_db_path(self) -> Path:
        """Get the path to the browser's history database."""
        pass
    
    @abstractmethod
    def extract(self, hours_back: int = 24) -> list[HistoryEntry]:
        """Extract history entries from the last N hours."""
        pass
    
    @property
    @abstractmethod
    def browser_name(self) -> str:
        """Name of the browser (e.g., 'chrome', 'edge', 'safari')."""
        pass
