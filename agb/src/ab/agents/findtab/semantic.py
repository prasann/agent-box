"""Semantic search with embeddings."""
import pickle
from pathlib import Path
from datetime import datetime
from .models import SearchResult
from .ollama_client import OllamaClient
from .database import IndexDatabase


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score between -1 and 1
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = sum(a * a for a in vec1) ** 0.5
    mag2 = sum(b * b for b in vec2) ** 0.5
    
    if mag1 == 0 or mag2 == 0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


class SemanticSearcher:
    """Search using semantic embeddings."""
    
    def __init__(self, db: IndexDatabase, ollama: OllamaClient):
        """Initialize semantic searcher.
        
        Args:
            db: Index database
            ollama: Ollama client for embeddings
        """
        self.db = db
        self.ollama = ollama
    
    def search(self, query: str, limit: int = 10, threshold: float = 0.3) -> list[SearchResult]:
        """Semantic search using embeddings.
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of search results ranked by semantic similarity
        """
        # Expand query with LLM
        expanded = self.ollama.expand_query(query)
        print(f"🔍 Intent: {expanded['intent']}")
        
        # Generate embedding for query
        query_text = f"{expanded['intent']}. {' '.join(expanded['keywords'])}"
        query_embedding = self.ollama.generate_embedding(query_text)
        
        if not query_embedding:
            print("⚠️  Failed to generate query embedding")
            return []
        
        # Get all entries with embeddings
        entries = self.db.get_all_embeddings()
        
        if not entries:
            print("⚠️  No embeddings in database. Run 'findtab embed' first.")
            return []
        
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
                    relevance_score=similarity,
                ))
        
        # Sort by similarity (descending) and recency
        results.sort(key=lambda r: (r.relevance_score, r.visit_time), reverse=True)
        
        return results[:limit]
    
    def generate_embeddings(self, batch_size: int = 50) -> int:
        """Generate embeddings for entries that don't have them.
        
        Args:
            batch_size: Number of entries to process at once
            
        Returns:
            Number of embeddings generated
        """
        entries = self.db.get_entries_without_embeddings(limit=batch_size)
        
        if not entries:
            return 0
        
        count = 0
        for entry_id, title, summary in entries:
            # Combine title and summary for embedding
            text = f"{title}. {summary or ''}"
            
            # Generate embedding
            embedding = self.ollama.generate_embedding(text)
            
            if embedding:
                # Store in database
                if self.db.store_embedding(entry_id, embedding):
                    count += 1
        
        return count
