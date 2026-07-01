"""
Base embedder interface for MedNexus-AI embedding generation.

Defines the abstract base class that all embedding providers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import time
from datetime import datetime


@dataclass
class EmbeddingMetadata:
    """Metadata for a single embedding."""
    
    embedding_id: str
    chunk_id: str
    document_id: str
    provider: str
    model: str
    dimension: int
    created_at: str
    
    # Optional fields
    source: Optional[str] = None
    checksum: Optional[str] = None
    chunk_checksum: Optional[str] = None
    generation_time: Optional[float] = None
    quality_score: Optional[float] = None
    token_count: Optional[int] = None
    processing_status: str = "success"
    retry_count: int = 0
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class EmbeddingResult:
    """Result of embedding generation for a single chunk."""
    
    chunk_id: str
    embedding: Optional[List[float]] = None
    metadata: Optional[EmbeddingMetadata] = None
    error: Optional[str] = None
    status: str = "pending"  # pending, success, failed, cached
    generation_time: float = 0.0
    retry_count: int = 0
    
    def is_success(self) -> bool:
        """Check if embedding was successfully generated."""
        return self.status in ("success", "cached") and self.embedding is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without embedding vector)."""
        return {
            'chunk_id': self.chunk_id,
            'status': self.status,
            'error': self.error,
            'generation_time': self.generation_time,
            'retry_count': self.retry_count,
            'metadata': self.metadata.to_dict() if self.metadata else None
        }


class BaseEmbedder(ABC):
    """
    Abstract base class for embedding providers.
    
    All embedding providers must inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize embedder with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.provider_name = self.__class__.__name__.replace('Embedder', '').lower()
        self.model_name = config.get('model', 'unknown')
        self.dimension = config.get('dimension', 0)
        self._is_initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the embedding provider.
        
        This method should load models, establish connections, etc.
        Must be called before embed_batch().
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (one per text)
            
        Raises:
            RuntimeError: If provider not initialized
            ValueError: If texts is empty or invalid
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the embedding dimension for this provider.
        
        Returns:
            Embedding dimension (e.g., 384, 768, 1536)
        """
        pass
    
    @abstractmethod
    def get_max_batch_size(self) -> int:
        """
        Get the maximum batch size supported by this provider.
        
        Returns:
            Maximum batch size
        """
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Default implementation uses simple character-based estimation.
        Providers can override for more accurate estimation.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Simple estimation: 4 characters ≈ 1 token
        return len(text) // 4
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """
        Validate an embedding vector.
        
        Args:
            embedding: Embedding vector to validate
            
        Returns:
            True if valid, False otherwise
        """
        import math
        
        if not embedding:
            return False
        
        if len(embedding) != self.dimension:
            return False
        
        # Check for NaN or infinite values
        if any(math.isnan(x) or math.isinf(x) for x in embedding):
            return False
        
        # Check for zero vector
        if all(x == 0 for x in embedding):
            return False
        
        return True
    
    def cleanup(self) -> None:
        """
        Cleanup resources used by the provider.
        
        Default implementation does nothing.
        Providers can override to release resources.
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this provider.
        
        Returns:
            Dictionary containing provider information
        """
        return {
            'provider': self.provider_name,
            'model': self.model_name,
            'dimension': self.dimension,
            'max_batch_size': self.get_max_batch_size(),
            'initialized': self._is_initialized
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False
