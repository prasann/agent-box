"""LLM-based URL classifier for FindTab.

Uses GitHub Models API to classify which URLs are worth saving as bookmarks.
Classifies based on URL patterns only - does not fetch webpage content.
"""
import json
from typing import Optional
from ...core.github_models import GitHubModelsClient
from .models import HistoryEntry, ClassifiedEntry


# Focused prompt for URL-pattern-only classification
CLASSIFICATION_PROMPT = """You are building a personal bookmark index for a developer. Your job is to classify URLs based ONLY on the URL pattern and page title - do NOT try to fetch or access the URLs.

CONTEXT: The user browses many websites daily. We want to save only content worth revisiting later - articles, documentation, code references, and discussions. We must SKIP anything that requires authentication or is ephemeral.

CLASSIFY each URL as SAVE or SKIP based on these rules:

SAVE (content worth bookmarking):
- Technical articles/blogs: medium.com/@*/, dev.to/*, *.substack.com/p/*, hashnode.dev/*
- Documentation: docs.*, *.readthedocs.io, developer.*, learn.microsoft.com/*
- Code: github.com/*/blob/*, github.com/*/tree/*, github.com/*/*/issues/*, github.com/*/*/discussions/*
- Q&A: stackoverflow.com/questions/*, stackexchange.com/*
- Discussions: reddit.com/r/*/comments/*, news.ycombinator.com/item*
- Reference: wikipedia.org/wiki/*, *.wiki/*

SKIP (not worth bookmarking):
- Auth-required: mail.*, outlook.*, gmail.*, */login, */signin, */account, */settings, */dashboard
- E-commerce: amazon.*, flipkart.*, */cart, */checkout, */orders
- Video: youtube.com/*, vimeo.com/*, tiktok.com/*
- Search/feeds: */search*, */feed, */notifications, */trending
- Homepages: Just a domain with no path (e.g., github.com, google.com)
- Local: localhost*, 127.0.0.1*, file://*

When uncertain, SKIP (be conservative).

URLs to classify:
{entries}

Respond with ONLY a JSON array. No explanation. Format:
[{{"i": 1, "s": true}}, {{"i": 2, "s": false}}]

JSON:"""


class BookmarkClassifier:
    """Classifies URLs using GitHub Models API."""
    
    def __init__(self, client: Optional[GitHubModelsClient] = None, batch_size: int = 30):
        """Initialize classifier.
        
        Args:
            client: GitHub Models client
            batch_size: Number of URLs to process per LLM call
        """
        self.client = client or GitHubModelsClient()
        self.batch_size = batch_size
    
    def classify_batch(self, entries: list[HistoryEntry]) -> list[ClassifiedEntry]:
        """Classify a batch of history entries.
        
        Args:
            entries: List of history entries to classify
            
        Returns:
            List of classified entries (both save and skip)
        """
        if not entries:
            return []
        
        results = []
        
        # Process in batches
        for i in range(0, len(entries), self.batch_size):
            batch = entries[i:i + self.batch_size]
            batch_results = self._classify_single_batch(batch)
            results.extend(batch_results)
        
        return results
    
    def _classify_single_batch(self, entries: list[HistoryEntry]) -> list[ClassifiedEntry]:
        """Classify a single batch of entries."""
        # Format entries for prompt
        formatted = "\n".join(
            f'{idx + 1}. {entry.url} | "{entry.title}"'
            for idx, entry in enumerate(entries)
        )
        
        prompt = CLASSIFICATION_PROMPT.format(entries=formatted)
        
        try:
            response = self.client.generate(prompt, temperature=0.1, max_tokens=500)
            classifications = self._parse_response(response, len(entries))
        except Exception as e:
            # On error, default to skipping all (conservative)
            print(f"Warning: Classification failed: {e}")
            classifications = {i + 1: False for i in range(len(entries))}
        
        # Build classified entries
        results = []
        for idx, entry in enumerate(entries):
            should_save = classifications.get(idx + 1, False)
            results.append(ClassifiedEntry(
                url=entry.url,
                title=entry.title,
                visit_time=entry.visit_time,
                visit_count=entry.visit_count,
                browser=entry.browser,
                should_save=should_save,
            ))
        
        return results
    
    def _parse_response(self, response: str, expected_count: int) -> dict[int, bool]:
        """Parse LLM response into classification dict.
        
        Args:
            response: Raw LLM response
            expected_count: Number of entries we expect
            
        Returns:
            Dict mapping index (1-based) to save decision
        """
        # Try to extract JSON from response
        response = response.strip()
        
        # Handle case where LLM wraps in markdown code block
        if "```" in response:
            # Extract content between code fences
            parts = response.split("```")
            for part in parts:
                if "[" in part and "]" in part:
                    response = part.strip()
                    if response.startswith("json"):
                        response = response[4:].strip()
                    break
        
        # Find JSON array in response
        start = response.find("[")
        end = response.rfind("]") + 1
        if start == -1 or end == 0:
            return {i + 1: False for i in range(expected_count)}
        
        json_str = response[start:end]
        
        try:
            data = json.loads(json_str)
            # Support both compact {"i": 1, "s": true} and full {"index": 1, "save": true}
            result = {}
            for item in data:
                idx = item.get("i") or item.get("index")
                save = item.get("s") if "s" in item else item.get("save", False)
                if idx:
                    result[idx] = bool(save)
            return result
        except (json.JSONDecodeError, KeyError, TypeError):
            # Fallback: try line-by-line parsing for simpler formats
            return self._parse_simple_format(response, expected_count)
    
    def _parse_simple_format(self, response: str, expected_count: int) -> dict[int, bool]:
        """Fallback parser for non-JSON responses."""
        results = {}
        
        for line in response.split("\n"):
            line = line.strip().lower()
            for i in range(1, expected_count + 1):
                if f"{i}" in line:
                    # Look for save/skip indicators
                    if "save" in line or "true" in line or "yes" in line:
                        results[i] = True
                    elif "skip" in line or "false" in line or "no" in line:
                        results[i] = False
        
        # Default unmatched to False (skip)
        for i in range(1, expected_count + 1):
            if i not in results:
                results[i] = False
        
        return results
    
    def filter_worth_saving(self, entries: list[HistoryEntry]) -> list[ClassifiedEntry]:
        """Classify and filter to only entries worth saving.
        
        Args:
            entries: List of history entries
            
        Returns:
            Only entries classified as worth saving
        """
        classified = self.classify_batch(entries)
        return [e for e in classified if e.should_save]
