"""Search module for FindTab - LLM-enhanced semantic search with FTS5 fallback."""
import json
from datetime import datetime
from typing import Optional

from .database import BookmarkDatabase
from .models import BookmarkSearchResult


class BookmarkSearcher:
    """Search bookmarks using LLM query expansion + re-ranking over FTS5."""
    
    def __init__(self, db: BookmarkDatabase, llm_client: Optional['AzureOpenAIClient'] = None):
        """Initialize searcher.
        
        Args:
            db: Bookmark database instance
            llm_client: Optional LLM client for query expansion and re-ranking.
                        If None, falls back to FTS5-only search.
        """
        self.db = db
        self.llm_client = llm_client
    
    def search(self, query: str, limit: int = 10) -> list[BookmarkSearchResult]:
        """Search bookmarks by query with optional LLM enhancement.
        
        When an LLM client is available, uses two-stage search:
          1. Query expansion: LLM interprets the query into keywords + time hint
          2. Re-ranking: LLM scores FTS5 candidates by semantic relevance
        
        Falls back to FTS5-only when LLM is unavailable or errors occur.
        
        Args:
            query: Search query (natural language)
            limit: Maximum results to return
            
        Returns:
            List of matching bookmarks, ranked by relevance
        """
        if self.llm_client is None:
            return self._fts_search(query, limit=limit)
        
        try:
            return self._llm_search(query, limit=limit)
        except Exception as e:
            print(f"[findtab] LLM search failed, falling back to FTS5: {e}")
            return self._fts_search(query, limit=limit)
    
    # ─────────────────────────────────────────────────────────────
    # LLM-enhanced search
    # ─────────────────────────────────────────────────────────────
    
    def _llm_search(self, query: str, limit: int = 10) -> list[BookmarkSearchResult]:
        """Two-stage LLM search: expand → fetch candidates → re-rank."""
        # Stage 1: Query expansion
        expansion = self._expand_query(query)
        keywords = expansion.get("keywords", [])
        time_hint = expansion.get("time_hint")
        
        if not keywords:
            # Expansion produced nothing useful, fall back to raw query words
            fts_query = self._prepare_query(query)
        else:
            # Deduplicate and build OR query from expanded keywords
            seen = set()
            unique = []
            for kw in keywords:
                kw_lower = kw.lower().strip()
                if kw_lower and kw_lower not in seen and len(kw_lower) > 1:
                    seen.add(kw_lower)
                    unique.append(self._sanitize_fts_token(kw_lower))
            fts_query = ' OR '.join(unique) if unique else self._prepare_query(query)
        
        # Fetch more candidates than needed for re-ranking
        candidate_limit = max(limit * 3, 20)
        candidates = self.db.search(fts_query, limit=candidate_limit, since=time_hint)
        
        if not candidates:
            return []
        
        # Stage 2: Re-rank with LLM
        ranked = self._rerank(query, candidates, limit=limit)
        return ranked
    
    def _expand_query(self, query: str) -> dict:
        """Use LLM to expand a natural language query into search terms.
        
        Returns:
            Dict with 'keywords' (list[str]) and 'time_hint' (str or None)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        prompt = (
            "Given a user's search query for their browser history bookmarks, expand it into search terms.\n"
            "Extract:\n"
            "1. keywords: list of relevant search terms, synonyms, and related concepts\n"
            "2. time_hint: if the query mentions a time (e.g., \"last week\", \"yesterday\"), "
            f"convert to a date string (YYYY-MM-DD) relative to today ({today}), otherwise null\n"
            "\n"
            f'User query: "{query}"\n'
            "\n"
            'Respond with ONLY JSON:\n'
            '{"keywords": ["term1", "term2", ...], "time_hint": null}'
        )
        
        try:
            raw = self.llm_client.generate(prompt, temperature=0.1, max_tokens=300)
            return self._parse_json_response(raw, fallback={"keywords": [], "time_hint": None})
        except Exception as e:
            print(f"[findtab] Query expansion failed: {e}")
            return {"keywords": [], "time_hint": None}
    
    def _rerank(self, query: str, candidates: list[dict], limit: int) -> list[BookmarkSearchResult]:
        """Use LLM to re-rank candidates by semantic relevance.
        
        Falls back to FTS5 ordering if re-ranking fails.
        """
        # Format candidates for the prompt
        lines = []
        for i, c in enumerate(candidates, 1):
            title = c.get('title', 'Untitled') or 'Untitled'
            summary = c.get('summary', '') or ''
            url = c.get('url', '')
            line = f'{i}. "{title}" - {summary} ({url})'
            lines.append(line)
        formatted_candidates = '\n'.join(lines)
        
        prompt = (
            "You are ranking bookmarks by relevance to a user's search query.\n"
            "\n"
            f'User\'s search: "{query}"\n'
            "\n"
            f"Candidates (numbered):\n{formatted_candidates}\n"
            "\n"
            f"Rank the top {limit} most relevant results. Consider semantic meaning, not just keyword overlap.\n"
            "\n"
            "Respond with ONLY a JSON array of indices (1-based) in order of relevance:\n"
            "[3, 1, 7, ...]"
        )
        
        try:
            raw = self.llm_client.generate(prompt, temperature=0.1, max_tokens=300)
            indices = self._parse_json_response(raw, fallback=None)
            
            if not isinstance(indices, list):
                raise ValueError(f"Expected list, got {type(indices)}")
            
            # Convert 1-based indices to results, skipping invalid ones
            results = []
            seen_ids = set()
            for idx in indices:
                if not isinstance(idx, int):
                    continue
                pos = idx - 1  # 1-based → 0-based
                if 0 <= pos < len(candidates) and pos not in seen_ids:
                    seen_ids.add(pos)
                    results.append(self._to_search_result(candidates[pos], rank=len(results)))
                if len(results) >= limit:
                    break
            
            # If LLM returned fewer than limit, pad with remaining FTS-ordered candidates
            if len(results) < limit:
                for i, c in enumerate(candidates):
                    if i not in seen_ids:
                        results.append(self._to_search_result(c, rank=len(results)))
                        seen_ids.add(i)
                    if len(results) >= limit:
                        break
            
            return results
        except Exception as e:
            print(f"[findtab] Re-ranking failed, using FTS5 order: {e}")
            return [
                self._to_search_result(c, rank=i)
                for i, c in enumerate(candidates[:limit])
            ]
    
    # ─────────────────────────────────────────────────────────────
    # FTS5-only fallback
    # ─────────────────────────────────────────────────────────────
    
    def _fts_search(self, query: str, limit: int = 10) -> list[BookmarkSearchResult]:
        """Plain FTS5 search without LLM enhancement."""
        fts_query = self._prepare_query(query)
        results = self.db.search(fts_query, limit=limit)
        return [self._to_search_result(r) for r in results]
    
    def _prepare_query(self, query: str) -> str:
        """Prepare query for FTS5 MATCH.
        
        Converts natural language query to FTS5 syntax.
        Simple approach: treat as OR of all words.
        """
        special_chars = ['"', "'", '(', ')', '*', '-', '+', ':', '^', '~']
        cleaned = query
        for char in special_chars:
            cleaned = cleaned.replace(char, ' ')
        
        words = [w.strip().lower() for w in cleaned.split() if len(w.strip()) > 1]
        
        if not words:
            return query
        
        return ' OR '.join(words)
    
    # ─────────────────────────────────────────────────────────────
    # List operations
    # ─────────────────────────────────────────────────────────────
    
    def list_recent(self, limit: int = 20) -> list[BookmarkSearchResult]:
        """List recently indexed bookmarks."""
        results = self.db.list_recent(limit=limit)
        return [self._to_search_result(r, rank=0.0) for r in results]
    
    def list_by_category(self, category: str, limit: int = 20) -> list[BookmarkSearchResult]:
        """List bookmarks by category using direct SQL query.
        
        Args:
            category: Category to filter (docs, article, discussion, code, reference)
            limit: Maximum results
        """
        results = self.db.list_by_category(category, limit=limit)
        return [self._to_search_result(r, rank=0.0) for r in results]
    
    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def _to_search_result(row: dict, rank: float | None = None) -> BookmarkSearchResult:
        """Convert a database row dict to a BookmarkSearchResult."""
        return BookmarkSearchResult(
            id=row['id'],
            url=row['url'],
            title=row['title'],
            category=row.get('category'),
            summary=row.get('summary'),
            topics=row.get('topics', []),
            why_useful=row.get('why_useful'),
            last_visit_at=row.get('last_visit_at'),
            visit_count=row.get('visit_count', 1),
            rank=rank if rank is not None else row.get('rank', 0.0),
        )
    
    @staticmethod
    def _sanitize_fts_token(token: str) -> str:
        """Remove FTS5 special characters from a single token."""
        for ch in '"\'()*-+:^~':
            token = token.replace(ch, '')
        return token.strip()
    
    @staticmethod
    def _parse_json_response(raw: str, fallback):
        """Extract and parse JSON from an LLM response.
        
        Handles markdown code fences and stray text around the JSON.
        """
        text = raw.strip()
        # Strip markdown fences
        if text.startswith("```"):
            lines = text.split('\n')
            lines = lines[1:]  # drop opening fence
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines).strip()
        
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object or array in the text
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            start = text.find(start_char)
            end = text.rfind(end_char)
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    continue
        
        if fallback is not None:
            return fallback
        raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")
