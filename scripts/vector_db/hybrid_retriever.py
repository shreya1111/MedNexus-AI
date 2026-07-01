"""
Hybrid retriever combining vector and BM25 search.

Uses Reciprocal Rank Fusion (RRF) to combine results.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent))

from vector_db.retriever import VectorRetriever
from vector_db.bm25_retriever import BM25Retriever
from utils.logger import get_logger


class HybridRetriever:
    """Hybrid retrieval combining vector and BM25 search."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        vector_retriever: VectorRetriever,
        bm25_retriever: Optional[BM25Retriever] = None
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            config: Retrieval configuration
            vector_retriever: Vector retriever instance
            bm25_retriever: BM25 retriever instance (optional)
        """
        self.config = config
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.logger = get_logger(__name__)
        
        # Hybrid configuration
        hybrid_config = config.get('search', {}).get('hybrid', {})
        self.vector_weight = hybrid_config.get('vector_weight', 0.7)
        self.bm25_weight = hybrid_config.get('bm25_weight', 0.3)
        self.rrf_k = hybrid_config.get('rrf_k', 60)
        
        # Search mode
        search_config = config.get('search', {})
        self.mode = search_config.get('mode', 'hybrid')
    
    def search(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        
        Args:
            query_embedding: Query embedding vector
            query_text: Query text for BM25
            top_k: Number of results
            filters: Metadata filters
            
        Returns:
            Combined search results
        """
        # Vector-only mode
        if self.mode == 'vector' or not self.bm25_retriever:
            return self.vector_retriever.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=filters
            )
        
        # BM25-only mode
        if self.mode == 'bm25' and self.bm25_retriever:
            return self.bm25_retriever.search(
                query_text=query_text,
                top_k=top_k,
                filters=filters
            )
        
        # Hybrid mode
        if self.mode == 'hybrid' and self.bm25_retriever:
            # Get vector results
            vector_results = self.vector_retriever.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Fetch more for fusion
                filters=filters
            )
            
            # Get BM25 results
            bm25_results = self.bm25_retriever.search(
                query_text=query_text,
                top_k=top_k * 2,
                filters=filters
            )
            
            # Combine using RRF
            combined = self._reciprocal_rank_fusion(
                vector_results,
                bm25_results,
                top_k
            )
            
            return combined
        
        # Fallback to vector search
        return self.vector_retriever.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )
    
    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Combine results using Reciprocal Rank Fusion.
        
        RRF Formula: score = Σ(1 / (k + rank))
        """
        scores = defaultdict(float)
        results_map = {}
        
        # Score vector results
        for rank, result in enumerate(vector_results, 1):
            chunk_id = result['chunk_id']
            scores[chunk_id] += self.vector_weight / (self.rrf_k + rank)
            results_map[chunk_id] = result
        
        # Score BM25 results
        for rank, result in enumerate(bm25_results, 1):
            chunk_id = result['chunk_id']
            scores[chunk_id] += self.bm25_weight / (self.rrf_k + rank)
            if chunk_id not in results_map:
                results_map[chunk_id] = result
        
        # Sort by combined score
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        # Build combined results
        combined = []
        for chunk_id in sorted_ids[:top_k]:
            result = results_map[chunk_id]
            result['rrf_score'] = scores[chunk_id]
            combined.append(result)
        
        return combined
