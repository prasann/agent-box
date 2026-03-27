"""History indexer for FindTab - LLM-enriched bookmark pipeline."""
from datetime import datetime
from typing import Optional
from ...core.config import Settings
from ...core.github_models import GitHubModelsClient
from .database import BookmarkDatabase
from .classifier import BookmarkClassifier
from .enricher import BookmarkEnricher
from .prefilter import URLPreFilter
from .models import HistoryEntry, ClassifiedEntry
from .extractors.chromium import create_chrome_extractor, create_edge_extractor


class IndexingStats:
    """Statistics from an indexing run."""
    
    def __init__(self):
        self.extracted: int = 0
        self.already_indexed: int = 0
        self.prefilter_saved: int = 0
        self.prefilter_skipped: int = 0
        self.prefilter_unknown: int = 0
        self.classified_save: int = 0
        self.classified_skip: int = 0
        self.enriched: int = 0
        self.failed: int = 0
        self.window_start: Optional[datetime] = None
        self.window_end: Optional[datetime] = None
    
    def __str__(self) -> str:
        return (
            f"Extracted: {self.extracted}, "
            f"New: {self.extracted - self.already_indexed}, "
            f"Pre-filter: {self.prefilter_saved} save / {self.prefilter_skipped} skip / {self.prefilter_unknown} unknown, "
            f"LLM: {self.classified_save} save / {self.classified_skip} skip, "
            f"Enriched: {self.enriched}"
        )


class BookmarkIndexer:
    """Indexes browser history into enriched bookmarks."""
    
    def __init__(
        self, 
        db: BookmarkDatabase, 
        settings: Settings,
        llm_client: Optional[GitHubModelsClient] = None
    ):
        """Initialize indexer.
        
        Args:
            db: Bookmark database
            settings: Configuration settings
            llm_client: GitHub Models client
        """
        self.db = db
        self.settings = settings
        self.llm_client = llm_client or GitHubModelsClient()
        
        self.prefilter = URLPreFilter(
            custom_rules_path=settings.findtab_rules_path
        )
        self.classifier = BookmarkClassifier(
            self.llm_client, 
            batch_size=settings.findtab_classifier_batch_size
        )
        self.enricher = BookmarkEnricher(
            self.llm_client,
            batch_size=settings.findtab_enricher_batch_size
        )
        
        # Browser extractors
        self.extractors = [
            create_edge_extractor(),
            create_chrome_extractor(),
        ]
    
    def run_incremental_index(self, force_full: bool = False, hours_back: Optional[int] = None) -> IndexingStats:
        """Run incremental indexing pipeline.
        
        Process history from last watermark to now.
        On first run (or force_full), processes last N days.
        
        Args:
            force_full: If True, ignore watermark and process bootstrap period
            hours_back: If specified, process this many hours (overrides watermark)
            
        Returns:
            Statistics about the indexing run
        """
        stats = IndexingStats()
        
        # Determine processing window
        window_end = datetime.now()
        
        if hours_back:
            # Explicit hours specified
            from datetime import timedelta
            window_start = window_end - timedelta(hours=hours_back)
        elif force_full:
            from datetime import timedelta
            window_start = window_end - timedelta(days=self.settings.findtab_bootstrap_days)
        else:
            window_start = self.db.get_processing_window(
                bootstrap_days=self.settings.findtab_bootstrap_days
            )
        
        stats.window_start = window_start
        stats.window_end = window_end
        
        # Calculate hours for extractor
        actual_hours = int((window_end - window_start).total_seconds() / 3600) + 1
        
        # Stage 1: Extract from browsers
        all_entries = self._extract_history(actual_hours)
        stats.extracted = len(all_entries)
        
        if not all_entries:
            self.db.set_last_processed_at(window_end)
            return stats
        
        # Stage 2: Filter out already indexed
        new_entries = self._filter_new(all_entries)
        stats.already_indexed = stats.extracted - len(new_entries)
        
        if not new_entries:
            self.db.set_last_processed_at(window_end)
            return stats
        
        # Stage 2.5: Pre-filter (rule-based)
        pf_save, pf_skip, pf_unknown = self.prefilter.filter_batch(new_entries)
        stats.prefilter_saved = len(pf_save)
        stats.prefilter_skipped = len(pf_skip)
        stats.prefilter_unknown = len(pf_unknown)
        
        # Stage 3: Classify with LLM (only unknowns)
        classified = self.classifier.classify_batch(pf_unknown)
        llm_save = [e for e in classified if e.should_save]
        
        stats.classified_save = len(llm_save)
        stats.classified_skip = len(classified) - len(llm_save)
        
        # Combine pre-filter saves with LLM saves for enrichment
        worth_saving_entries = pf_save + [
            HistoryEntry(
                url=e.url,
                title=e.title,
                visit_time=e.visit_time,
                visit_count=e.visit_count,
                browser=e.browser,
            )
            for e in llm_save
        ]
        
        # Convert to ClassifiedEntry for the enricher
        worth_saving = [
            ClassifiedEntry(
                url=e.url,
                title=e.title,
                visit_time=e.visit_time,
                visit_count=e.visit_count,
                browser=e.browser,
                should_save=True,
            )
            for e in worth_saving_entries
        ]
        
        if not worth_saving:
            self.db.set_last_processed_at(window_end)
            return stats
        
        # Stage 4: Enrich with LLM
        enriched = self.enricher.enrich_batch(worth_saving)
        stats.enriched = len(enriched)
        
        # Stage 5: Store in database
        for bookmark in enriched:
            try:
                # Store pending first
                self.db.store_pending_bookmarks([{
                    'url': bookmark.url,
                    'title': bookmark.title,
                    'first_visit_at': bookmark.first_visit_at,
                    'last_visit_at': bookmark.last_visit_at,
                    'visit_count': bookmark.visit_count,
                    'browser': bookmark.browser,
                }])
                
                # Then update with enrichment
                self.db.update_bookmark_enrichment(
                    url=bookmark.url,
                    category=bookmark.category,
                    summary=bookmark.summary,
                    topics=bookmark.topics,
                    why_useful=bookmark.why_useful,
                )
            except Exception as e:
                print(f"Warning: Failed to store {bookmark.url}: {e}")
                stats.failed += 1
        
        # Update watermark
        self.db.set_last_processed_at(window_end)
        
        return stats
    
    def _extract_history(self, hours_back: int) -> list[HistoryEntry]:
        """Extract history from all available browsers.
        
        Args:
            hours_back: Hours of history to extract
            
        Returns:
            Combined and deduplicated history entries
        """
        all_entries = []
        
        for extractor in self.extractors:
            if extractor.detect():
                try:
                    entries = extractor.extract(hours_back)
                    all_entries.extend(entries)
                except Exception as e:
                    print(f"Warning: Failed to extract from {extractor.browser_name}: {e}")
        
        # Deduplicate by URL (keep most recent)
        return self._deduplicate(all_entries)
    
    def _deduplicate(self, entries: list[HistoryEntry]) -> list[HistoryEntry]:
        """Deduplicate entries by URL, keeping most recent."""
        seen = {}
        
        for entry in entries:
            if entry.url not in seen:
                seen[entry.url] = entry
            else:
                # Keep the one with more recent visit time
                if entry.visit_time > seen[entry.url].visit_time:
                    seen[entry.url] = entry
                # Accumulate visit counts
                seen[entry.url].visit_count += entry.visit_count
        
        return list(seen.values())
    
    def _filter_new(self, entries: list[HistoryEntry]) -> list[HistoryEntry]:
        """Filter out entries already in the database.
        
        Also updates visit counts for existing entries.
        """
        urls = [e.url for e in entries]
        existing_urls = self.db.get_existing_urls(urls)
        
        new_entries = []
        for entry in entries:
            if entry.url in existing_urls:
                # Update visit count for existing
                self.db.update_visit_count(
                    entry.url, 
                    entry.visit_time, 
                    entry.visit_count
                )
            else:
                new_entries.append(entry)
        
        return new_entries
    
    def enrich_pending(self, limit: int = 50) -> int:
        """Enrich any pending bookmarks that failed initial enrichment.
        
        Args:
            limit: Maximum entries to process
            
        Returns:
            Number of entries enriched
        """
        pending = self.db.get_pending_enrichment(limit=limit)
        
        if not pending:
            return 0
        
        # Convert to ClassifiedEntry format for enricher
        from .models import ClassifiedEntry
        entries = [
            ClassifiedEntry(
                url=p['url'],
                title=p['title'],
                visit_time=datetime.now(),
                should_save=True,
            )
            for p in pending
        ]
        
        enriched = self.enricher.enrich_batch(entries)
        
        count = 0
        for bookmark in enriched:
            try:
                self.db.update_bookmark_enrichment(
                    url=bookmark.url,
                    category=bookmark.category,
                    summary=bookmark.summary,
                    topics=bookmark.topics,
                    why_useful=bookmark.why_useful,
                )
                count += 1
            except Exception:
                self.db.mark_enrichment_failed(bookmark.url)
        
        return count
