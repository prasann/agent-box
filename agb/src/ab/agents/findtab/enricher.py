"""LLM enricher for FindTab.

Uses Azure OpenAI to generate rich bookmark metadata.
"""
import json
from typing import Optional
from ...core.azure_openai_client import AzureOpenAIClient
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
    
    def __init__(self, llm_client: Optional[AzureOpenAIClient] = None, batch_size: int = 15):
        """Initialize enricher.
        
        Args:
            llm_client: Azure OpenAI client
            batch_size: URLs to process per LLM call
        """
        self.client = llm_client or AzureOpenAIClient()
        self.batch_size = batch_size
    
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
        
        # Use configured LLM client
        try:
            if self.client:
                response = self.client.generate(prompt, temperature=0.2, max_tokens=1500)
            else:
                raise RuntimeError("No LLM client available for enrichment")
            
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


def create_enricher(llm_client: Optional[AzureOpenAIClient] = None, batch_size: int = 15) -> BookmarkEnricher:
    """Factory function to create enricher."""
    return BookmarkEnricher(llm_client=llm_client, batch_size=batch_size)
