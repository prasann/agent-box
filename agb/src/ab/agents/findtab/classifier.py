"""LLM-based URL classifier for FindTab v2.

Uses Ollama to classify which URLs are worth saving as bookmarks.
"""
import json
from typing import Optional
from ...core.ollama_client import OllamaClient
from .models import HistoryEntry, ClassifiedEntry


CLASSIFICATION_PROMPT = """You are a bookmark curator. For each URL below, decide if it's worth saving for future reference.

SAVE if it's:
- An article, blog post, or tutorial someone might want to revisit
- Documentation or reference material (API docs, guides, manuals)
- A GitHub repo, issue, PR, or discussion with useful content
- A Reddit or X.com thread with substantive technical discussion
- Stack Overflow question with good answers
- A Medium, Dev.to, Substack, or similar blog post

SKIP if it's:
- Behind authentication (email, banking, shopping carts, dashboards, account pages)
- Ephemeral content (search results, feeds, notifications, login/signup pages)
- Video content (YouTube, Vimeo, TikTok, etc.)
- Navigation/landing pages without substance (homepages, category listings)
- Social media profiles, timelines, or feeds
- E-commerce product pages or shopping sites
- News site homepages (but individual articles are OK)
- URL shorteners or redirect pages

URLs to classify:
{entries}

Respond ONLY with a valid JSON array. Each object must have "index" (number) and "save" (boolean).
Example: [{{"index": 1, "save": true}}, {{"index": 2, "save": false}}]

JSON response:"""


class BookmarkClassifier:
    """Classifies URLs using Ollama LLM."""
    
    def __init__(self, ollama: OllamaClient, batch_size: int = 30):
        """Initialize classifier.
        
        Args:
            ollama: Ollama client instance
            batch_size: Number of URLs to process per LLM call
        """
        self.ollama = ollama
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
            response = self.ollama.generate(prompt, temperature=0.1, max_tokens=500)
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
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1])
        
        # Find JSON array in response
        start = response.find("[")
        end = response.rfind("]") + 1
        if start == -1 or end == 0:
            return {i + 1: False for i in range(expected_count)}
        
        json_str = response[start:end]
        
        try:
            data = json.loads(json_str)
            return {item["index"]: item.get("save", False) for item in data}
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
