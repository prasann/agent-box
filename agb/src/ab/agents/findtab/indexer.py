"""History indexing engine."""
from pathlib import Path
from .models import HistoryEntry, Settings
from .database import IndexDatabase
from .enricher import ContentEnricher
from .extractors.chromium import create_chrome_extractor, create_edge_extractor


class HistoryIndexer:
    """Index browser history incrementally."""
    
    def __init__(self, db: IndexDatabase, settings: Settings):
        """Initialize indexer.
        
        Args:
            db: Index database
            settings: Configuration settings
        """
        self.db = db
        self.settings = settings
        self.enricher = ContentEnricher(settings)
        
        # Setup browser extractors
        self.extractors = [
            create_edge_extractor(),
            create_chrome_extractor(),
        ]
    
    def run_incremental_index(self, hours_back: int = 1) -> int:
        """Index history from last N hours.
        
        Args:
            hours_back: How many hours back to index
            
        Returns:
            Number of new entries indexed
        """
        all_entries = []
        
        # Extract from all available browsers
        for extractor in self.extractors:
            if extractor.detect():
                try:
                    entries = extractor.extract(hours_back)
                    all_entries.extend(entries)
                except Exception as e:
                    print(f"Warning: Failed to extract from {extractor.browser_name}: {e}")
        
        # Deduplicate by URL + visit time
        unique_entries = self._deduplicate(all_entries)
        
        # Filter and enrich
        enriched = []
        for entry in unique_entries:
            # Skip if already indexed
            if self.db.already_indexed(entry.url, entry.visit_time):
                continue
            
            # Skip noise domains
            if self.enricher.should_skip(entry):
                continue
            
            # Enrich with keywords
            enriched_entry = self.enricher.enrich(entry)
            enriched.append(enriched_entry)
        
        # Store in database
        count = self.db.store_entries(enriched)
        
        return count
    
    def _deduplicate(self, entries: list[HistoryEntry]) -> list[HistoryEntry]:
        """Remove duplicate entries."""
        seen = set()
        unique = []
        
        for entry in entries:
            key = (entry.url, entry.visit_time.isoformat())
            if key not in seen:
                seen.add(key)
                unique.append(entry)
        
        return unique
