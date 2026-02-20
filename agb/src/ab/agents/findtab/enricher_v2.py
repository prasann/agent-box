"""LLM enricher for FindTab v2.

Uses Copilot CLI (preferred) or Ollama (fallback) to generate rich metadata.
"""
import json
import subprocess
import shutil
from typing import Optional
from ...core.ollama_client import OllamaClient
from .models import ClassifiedEntry, EnrichedBookmark


ENRICHMENT_PROMPT = """For each URL below, extract bookmark metadata. These are pages someone wants to revisit later.

URLs:
{entries}

For each URL, provide:
- category: one of [docs, article, discussion, code, reference]
  - docs: API documentation, guides, manuals, official docs
  - article: blog posts, tutorials, how-to guides
  - discussion: Reddit threads, GitHub issues/discussions, forum posts
  - code: GitHub repos, code examples, gists
  - reference: Stack Overflow, Wikipedia, lookup resources
- summary: 1-2 sentence description of what this page likely contains based on URL/title
- topics: list of 3-5 key concepts, technologies, or subjects
- why_useful: brief reason someone would want to revisit this

Respond ONLY with a valid JSON array. Example:
[{{"index": 1, "category": "article", "summary": "Tutorial on building CLI tools", "topics": ["rust", "cli", "cargo"], "why_useful": "Reference for CLI argument parsing"}}]

JSON response:"""


class BookmarkEnricher:
    """Enriches bookmarks with LLM-generated metadata."""
    
    def __init__(self, ollama: Optional[OllamaClient] = None, batch_size: int = 15):
        """Initialize enricher.
        
        Args:
            ollama: Ollama client for fallback/primary enrichment
            batch_size: URLs to process per LLM call
        """
        self.ollama = ollama
        self.batch_size = batch_size
        self._copilot_available: Optional[bool] = None
    
    @property
    def copilot_available(self) -> bool:
        """Check if gh copilot CLI is available."""
        if self._copilot_available is None:
            self._copilot_available = shutil.which('gh') is not None
            if self._copilot_available:
                # Check if copilot extension is available
                try:
                    result = subprocess.run(
                        ['gh', 'extension', 'list'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    self._copilot_available = 'copilot' in result.stdout.lower()
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    self._copilot_available = False
        return self._copilot_available
    
    def enrich_batch(self, entries: list[ClassifiedEntry]) -> list[EnrichedBookmark]:
        """Enrich a batch of classified entries.
        
        Args:
            entries: Classified entries to enrich
            
        Returns:
            Enriched bookmarks with metadata
        """
        if not entries:
            return []
        
        results = []
        
        # Process in batches
        for i in range(0, len(entries), self.batch_size):
            batch = entries[i:i + self.batch_size]
            batch_results = self._enrich_single_batch(batch)
            results.extend(batch_results)
        
        return results
    
    def _enrich_single_batch(self, entries: list[ClassifiedEntry]) -> list[EnrichedBookmark]:
        """Enrich a single batch of entries."""
        # Format entries for prompt
        formatted = "\n".join(
            f'{idx + 1}. {entry.url} | "{entry.title}"'
            for idx, entry in enumerate(entries)
        )
        
        prompt = ENRICHMENT_PROMPT.format(entries=formatted)
        
        # Try Copilot first, fall back to Ollama
        try:
            if self.copilot_available:
                response = self._call_copilot(prompt)
            elif self.ollama:
                response = self.ollama.generate(prompt, temperature=0.2, max_tokens=1500)
            else:
                raise RuntimeError("No LLM available for enrichment")
            
            enrichments = self._parse_response(response, len(entries))
        except Exception as e:
            print(f"Warning: Enrichment failed: {e}")
            enrichments = {}
        
        # Build enriched bookmarks
        results = []
        for idx, entry in enumerate(entries):
            enrichment = enrichments.get(idx + 1, {})
            results.append(EnrichedBookmark(
                url=entry.url,
                title=entry.title,
                category=enrichment.get('category', 'article'),
                summary=enrichment.get('summary', ''),
                topics=enrichment.get('topics', []),
                why_useful=enrichment.get('why_useful', ''),
                first_visit_at=entry.visit_time,
                last_visit_at=entry.visit_time,
                visit_count=entry.visit_count,
                browser=entry.browser,
            ))
        
        return results
    
    def _call_copilot(self, prompt: str) -> str:
        """Call GitHub Copilot CLI with prompt.
        
        Uses non-interactive mode to get response.
        """
        # gh copilot suggest expects interactive input, so we use explain
        # with a specific format request
        try:
            result = subprocess.run(
                ['gh', 'copilot', 'explain', prompt],
                capture_output=True,
                text=True,
                timeout=60,
                input='',  # No interactive input
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            raise RuntimeError("Copilot CLI timed out")
        except subprocess.SubprocessError as e:
            raise RuntimeError(f"Copilot CLI error: {e}")
    
    def _parse_response(self, response: str, expected_count: int) -> dict[int, dict]:
        """Parse LLM response into enrichment dict.
        
        Args:
            response: Raw LLM response
            expected_count: Number of entries we expect
            
        Returns:
            Dict mapping index (1-based) to enrichment data
        """
        response = response.strip()
        
        # Handle markdown code blocks
        if "```" in response:
            lines = response.split("```")
            for part in lines:
                if "[" in part and "]" in part:
                    response = part
                    break
        
        # Find JSON array
        start = response.find("[")
        end = response.rfind("]") + 1
        if start == -1 or end == 0:
            return {}
        
        json_str = response[start:end]
        
        try:
            data = json.loads(json_str)
            result = {}
            for item in data:
                idx = item.get("index")
                if idx:
                    result[idx] = {
                        'category': self._validate_category(item.get('category', 'article')),
                        'summary': str(item.get('summary', ''))[:500],
                        'topics': self._validate_topics(item.get('topics', [])),
                        'why_useful': str(item.get('why_useful', ''))[:200],
                    }
            return result
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def _validate_category(self, category: str) -> str:
        """Validate category is one of allowed values."""
        allowed = ['docs', 'article', 'discussion', 'code', 'reference']
        category = str(category).lower().strip()
        return category if category in allowed else 'article'
    
    def _validate_topics(self, topics) -> list[str]:
        """Validate and clean topics list."""
        if not isinstance(topics, list):
            return []
        return [str(t).strip().lower() for t in topics[:5] if t]


def create_enricher(ollama: Optional[OllamaClient] = None, batch_size: int = 15) -> BookmarkEnricher:
    """Factory function to create enricher with best available backend."""
    return BookmarkEnricher(ollama=ollama, batch_size=batch_size)
