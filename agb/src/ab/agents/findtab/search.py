"""Semantic search for browser history."""
import pickle
from datetime import datetime
from ...core.ollama_client import OllamaClient
from .models import SearchResult
from .database import IndexDatabase


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = sum(a * a for a in vec1) ** 0.5
    mag2 = sum(b * b for b in vec2) ** 0.5
    
    return dot_product / (mag1 * mag2) if mag1 and mag2 else 0.0


class HistorySearcher:
    """Semantic search for browser history."""
    
    def __init__(self, db: IndexDatabase, ollama: OllamaClient):
        self.db = db
        self.ollama = ollama
    
    def search(self, query: str, limit: int = 10, threshold: float = 0.3) -> tuple[list[SearchResult], str]:
        """Search history semantically.
        
        Returns:
            Tuple of (results, intent_description)
        """
        # Expand query with LLM
        expanded = self.ollama.expand_query(query)
        intent = expanded['intent']
        
        # Generate embedding for query
        query_text = f"{intent}. {' '.join(expanded['keywords'])}"
        query_embedding = self.ollama.generate_embedding(query_text)
        
        if not query_embedding:
            return [], intent
        
        # Get all entries with embeddings
        entries = self.db.get_all_embeddings()
        
        if not entries:
            return [], intent
        
        # Calculate similarities
        results = []
        for row in entries:
            entry_id, url, title, visit_time, summary, visit_count, embedding_blob = row
            entry_embedding = pickle.loads(embedding_blob)
            similarity = cosine_similarity(query_embedding, entry_embedding)
            
            if similarity >= threshold:
                results.append(SearchResult(
                    url=url,
                    title=title,
                    visit_time=datetime.fromisoformat(visit_time),
                    summary=summary,
                    visit_count=visit_count,
                    relevance_score=similarity,
                ))
        
        # Sort by similarity (descending) and recency
        results.sort(key=lambda r: (r.relevance_score, r.visit_time), reverse=True)
        
        return results[:limit], intent
    
    def generate_embeddings(self, batch_size: int = 50) -> int:
        """Generate embeddings for entries that don't have them."""
        entries = self.db.get_entries_without_embeddings(limit=batch_size)
        
        if not entries:
            return 0
        
        count = 0
        for entry_id, title, summary in entries:
            text = f"{title}. {summary or ''}"
            embedding = self.ollama.generate_embedding(text)
            
            if embedding and self.db.store_embedding(entry_id, embedding):
                count += 1
        
        return count
