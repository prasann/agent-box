"""Content enrichment for history entries."""
from urllib.parse import urlparse
import re
from .models import HistoryEntry, EnrichedEntry, Settings


class ContentEnricher:
    """Enrich history entries with keywords and metadata."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._stop_words = {
            'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and',
            'is', 'it', 'by', 'with', 'from', 'as', 'was', 'are', 'be',
        }
    
    def should_skip(self, entry: HistoryEntry) -> bool:
        """Determine if entry should be skipped from indexing."""
        url_lower = entry.url.lower()
        
        for skip_domain in self.settings.skip_domains:
            if skip_domain in url_lower:
                return True
        
        return False
    
    def is_content_site(self, url: str) -> bool:
        """Check if URL is from a known content site."""
        url_lower = url.lower()
        
        for content_site in self.settings.content_sites:
            if content_site in url_lower:
                return True
        
        return False
    
    def enrich(self, entry: HistoryEntry) -> EnrichedEntry:
        """Enrich a history entry with keywords.
        
        Args:
            entry: Basic history entry
            
        Returns:
            Enriched entry with keywords
        """
        keywords = self._extract_keywords(entry)
        
        return EnrichedEntry(
            **entry.model_dump(),
            keywords=keywords,
            summary=None,  # Will be added by LLM if needed
        )
    
    def _extract_keywords(self, entry: HistoryEntry) -> list[str]:
        """Extract keywords from URL and title."""
        keywords = set()
        
        # Extract from URL
        parsed = urlparse(entry.url)
        
        # Domain parts
        domain_parts = parsed.netloc.split('.')
        for part in domain_parts:
            if part and len(part) > 2 and part not in {'www', 'com', 'org', 'net'}:
                keywords.add(part.lower())
        
        # Path parts
        path_parts = parsed.path.split('/')
        for part in path_parts:
            # Clean and split on common separators
            cleaned = re.sub(r'[^a-zA-Z0-9]+', ' ', part)
            for word in cleaned.split():
                word = word.lower()
                if len(word) > 2 and word not in self._stop_words:
                    keywords.add(word)
        
        # Extract from title
        title_words = re.sub(r'[^a-zA-Z0-9]+', ' ', entry.title).split()
        for word in title_words:
            word = word.lower()
            if len(word) > 2 and word not in self._stop_words:
                keywords.add(word)
        
        return sorted(list(keywords))[:20]  # Limit to top 20
