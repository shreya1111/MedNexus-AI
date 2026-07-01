"""
Search service for knowledge base retrieval.

Integrates with the RAG retrieval engine.
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from scripts.vector_db.collection_manager import CollectionManager
from scripts.vector_db.retriever import VectorRetriever
from scripts.vector_db.hybrid_retriever import HybridRetriever
from scripts.vector_db.query_processor import QueryProcessor
from scripts.embeddings.provider_factory import ProviderFactory
from scripts.utils.config_loader import load_yaml_config

from app.core.exceptions import NotFoundError, ValidationError


class SearchService:
    """Search service for knowledge base retrieval."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize search service.
        
        Args:
            db: Database session
        """
        self.db = db
        self._initialize_retrieval()
    
    def _initialize_retrieval(self):
        """Initialize retrieval components."""
        # Load configs
        retrieval_config = load_yaml_config(Path("config/retrieval.yaml"))
        embedding_config = load_yaml_config(Path("config/embedding.yaml"))
        
        # Initialize collection manager
        self.collection_manager = CollectionManager(retrieval_config)
        self.collection_manager.get_or_create_collection()
        
        # Initialize query processor
        self.query_processor = QueryProcessor(retrieval_config)
        
        # Initialize embedder
        provider_config = embedding_config.get('provider', {})
        active_provider = provider_config.get('active', 'sentence-transformers')
        provider_settings = provider_config.get(active_provider, {})
        
        self.embedder = ProviderFactory.create_embedder(
            active_provider,
            provider_settings
        )
        self.embedder.initialize()
        
        # Initialize retrievers
        self.vector_retriever = VectorRetriever(
            retrieval_config,
            self.collection_manager
        )
        
        self.hybrid_retriever = HybridRetriever(
            retrieval_config,
            self.collection_manager
        )
    
    async def vector_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Perform vector search.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Optional filters
            
        Returns:
            Search results
        """
        start_time = time.time()
        
        # Process query
        processed_query = self.query_processor.process(query)
        
        # Generate embedding
        query_embedding = self.embedder.embed_batch([processed_query])[0]
        
        # Search
        results = self.vector_retriever.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )
        
        # Format results
        formatted_results = [
            {
                'chunk_id': r.get('chunk_id', ''),
                'document': r.get('document', ''),
                'content': r.get('text', ''),
                'similarity': r.get('similarity', 0.0),
                'metadata': r.get('metadata', {})
            }
            for r in results
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results),
            'processing_time_ms': processing_time
        }
    
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Perform hybrid search (vector + BM25).
        
        Args:
            query: Search query
            top_k: Number of results
            vector_weight: Weight for vector search
            bm25_weight: Weight for BM25
            filters: Optional filters
            
        Returns:
            Search results
        """
        start_time = time.time()
        
        # Process query
        processed_query = self.query_processor.process(query)
        
        # Generate embedding
        query_embedding = self.embedder.embed_batch([processed_query])[0]
        
        # Hybrid search
        results = self.hybrid_retriever.search(
            query_embedding=query_embedding,
            query_text=processed_query,
            top_k=top_k,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            filters=filters
        )
        
        # Format results
        formatted_results = [
            {
                'chunk_id': r.get('chunk_id', ''),
                'document': r.get('document', ''),
                'content': r.get('text', ''),
                'similarity': r.get('score', 0.0),
                'metadata': r.get('metadata', {})
            }
            for r in results
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results),
            'processing_time_ms': processing_time,
            'weights': {
                'vector': vector_weight,
                'bm25': bm25_weight
            }
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get search/knowledge base statistics.
        
        Returns:
            Statistics
        """
        # Get collection stats
        collection = self.collection_manager.get_or_create_collection()
        total_chunks = collection.count()
        
        return {
            'total_documents': total_chunks,
            'collection_name': self.collection_manager.collection_name,
            'embedding_dimension': self.collection_manager.embedding_dimension
        }
