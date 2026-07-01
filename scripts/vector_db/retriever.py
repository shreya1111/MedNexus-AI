"""
Vector retriever for MedNexus-AI.

Implements semantic search with metadata filtering and MMR.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import time

sys.path.append(str(Path(__file__).parent.parent))

from vector_db.collection_manager import CollectionManager
from utils.logger import get_logger


class VectorRetriever:
    """Vector-based semantic search retriever."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        collection_manager: CollectionManager
    ):
        """
        Initialize vector retriever.
        
        Args:
            config: Retrieval configuration
            collection_manager: Collection manager instance
        """
        self.config = config
        self.collection_manager = collection_manager
        self.logger = get_logger(__name__)
        
        # Search configuration
        search_config = config.get('search', {})
        self.default_top_k = search_config.get('top_k', 10)
        self.similarity_threshold = search_config.get('similarity_threshold', 0.0)
        self.mmr_enabled = search_config.get('mmr_enabled', False)
        self.mmr_lambda = search_config.get('mmr_lambda', 0.5)
        self.mmr_fetch_k = search_config.get('mmr_fetch_k', 20)
        
        # Statistics
        self.stats = {
            'total_searches': 0,
            'total_results': 0,
            'avg_latency': 0.0,
            'cache_hits': 0
        }
    
    def search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        mmr: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Metadata filters
            mmr: Enable MMR (Maximum Marginal Relevance)
            
        Returns:
            List of search results
        """
        start = time.time()
        
        top_k = top_k or self.default_top_k
        mmr = mmr if mmr is not None else self.mmr_enabled
        
        collection = self.collection_manager.collection
        if not collection:
            self.logger.error("No collection loaded")
            return []
        
        try:
            # Build where clause for filters
            where = self._build_where_clause(filters) if filters else None
            
            # Determine n_results
            n_results = self.mmr_fetch_k if mmr else top_k
            
            # Query collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=['embeddings', 'documents', 'metadatas', 'distances']
            )
            
            # Extract results
            search_results = self._format_results(results)
            
            # Apply MMR if enabled
            if mmr and search_results:
                search_results = self._apply_mmr(
                    query_embedding,
                    search_results,
                    top_k
                )
            else:
                search_results = search_results[:top_k]
            
            # Filter by similarity threshold
            if self.similarity_threshold > 0:
                search_results = [
                    r for r in search_results
                    if r.get('similarity', 0) >= self.similarity_threshold
                ]
            
            # Update statistics
            latency = time.time() - start
            self.stats['total_searches'] += 1
            self.stats['total_results'] += len(search_results)
            self.stats['avg_latency'] = (
                (self.stats['avg_latency'] * (self.stats['total_searches'] - 1) + latency)
                / self.stats['total_searches']
            )
            
            self.logger.debug(
                f"Vector search returned {len(search_results)} results in {latency:.3f}s"
            )
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where clause from filters."""
        where = {}
        
        for key, value in filters.items():
            if isinstance(value, dict):
                # Handle operators
                for op, val in value.items():
                    if op == 'eq':
                        where[key] = val
                    elif op == '$in':
                        where[key] = {'$in': val}
                    elif op == '$ne':
                        where[key] = {'$ne': val}
                    # Add more operators as needed
            else:
                where[key] = value
        
        return where
    
    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format ChromaDB results."""
        formatted = []
        
        if not results or 'ids' not in results:
            return formatted
        
        ids = results['ids'][0] if results['ids'] else []
        distances = results['distances'][0] if results.get('distances') else []
        metadatas = results['metadatas'][0] if results.get('metadatas') else []
        documents = results['documents'][0] if results.get('documents') else []
        embeddings = results['embeddings'][0] if results.get('embeddings') else []
        
        for i, chunk_id in enumerate(ids):
            distance = distances[i] if i < len(distances) else 0.0
            
            # Convert distance to similarity (cosine: 1 - distance)
            similarity = 1.0 - distance
            
            result = {
                'chunk_id': chunk_id,
                'similarity': similarity,
                'distance': distance,
                'document': documents[i] if i < len(documents) else '',
                'metadata': metadatas[i] if i < len(metadatas) else {},
                'embedding': embeddings[i] if i < len(embeddings) else []
            }
            
            formatted.append(result)
        
        return formatted
    
    def _apply_mmr(
        self,
        query_embedding: List[float],
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Apply Maximum Marginal Relevance.
        
        Balances relevance and diversity in results.
        """
        import numpy as np
        
        if len(results) <= top_k:
            return results
        
        try:
            # Extract embeddings
            embeddings = np.array([r['embedding'] for r in results])
            query = np.array(query_embedding)
            
            # Normalize
            query = query / (np.linalg.norm(query) + 1e-10)
            embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10)
            
            # Calculate query similarities
            query_similarities = np.dot(embeddings, query)
            
            # MMR algorithm
            selected = []
            candidates = list(range(len(results)))
            
            # Select first (most relevant)
            selected.append(candidates[np.argmax(query_similarities)])
            candidates.remove(selected[0])
            
            # Select remaining
            while len(selected) < top_k and candidates:
                mmr_scores = []
                
                for idx in candidates:
                    # Relevance to query
                    relevance = query_similarities[idx]
                    
                    # Max similarity to already selected
                    if selected:
                        selected_embs = embeddings[selected]
                        similarities = np.dot(selected_embs, embeddings[idx])
                        max_sim = np.max(similarities)
                    else:
                        max_sim = 0
                    
                    # MMR score: λ * relevance - (1-λ) * max_similarity
                    mmr_score = self.mmr_lambda * relevance - (1 - self.mmr_lambda) * max_sim
                    mmr_scores.append(mmr_score)
                
                # Select best MMR score
                best_idx = candidates[np.argmax(mmr_scores)]
                selected.append(best_idx)
                candidates.remove(best_idx)
            
            # Return selected results
            return [results[i] for i in selected]
            
        except Exception as e:
            self.logger.error(f"MMR failed: {e}")
            return results[:top_k]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return self.stats.copy()
