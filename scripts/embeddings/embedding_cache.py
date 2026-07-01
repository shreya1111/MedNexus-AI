"""
Embedding cache for MedNexus-AI.

Provides checksum-based caching to avoid regenerating embeddings for unchanged chunks.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.file_utils import ensure_directory


class EmbeddingCache:
    """Cache for storing and retrieving embeddings based on checksums."""
    
    def __init__(
        self,
        cache_dir: Path,
        strategy: str = "checksum",
        enabled: bool = True
    ):
        """
        Initialize embedding cache.
        
        Args:
            cache_dir: Directory to store cache files
            strategy: Caching strategy (checksum, timestamp, disabled)
            enabled: Whether caching is enabled
        """
        self.cache_dir = ensure_directory(cache_dir)
        self.strategy = strategy
        self.enabled = enabled and strategy != "disabled"
        self.logger = get_logger(__name__)
        
        # Cache index file
        self.index_file = self.cache_dir / "cache_index.json"
        self.index: Dict[str, Any] = {}
        
        # Statistics
        self.hits = 0
        self.misses = 0
        
        # Load existing index
        if self.enabled:
            self._load_index()
    
    def _load_index(self) -> None:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
                self.logger.debug(f"Loaded cache index with {len(self.index)} entries")
            except Exception as e:
                self.logger.warning(f"Failed to load cache index: {e}")
                self.index = {}
    
    def _save_index(self) -> None:
        """Save cache index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save cache index: {e}")
    
    def _get_cache_key(
        self,
        chunk_checksum: str,
        provider: str,
        model: str
    ) -> str:
        """
        Generate cache key.
        
        Args:
            chunk_checksum: Checksum of the chunk text
            provider: Embedding provider name
            model: Model name
            
        Returns:
            Cache key string
        """
        return f"{provider}_{model}_{chunk_checksum}"
    
    def get(
        self,
        chunk_id: str,
        chunk_checksum: str,
        provider: str,
        model: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached embedding.
        
        Args:
            chunk_id: Chunk identifier
            chunk_checksum: Checksum of chunk text
            provider: Embedding provider
            model: Model name
            
        Returns:
            Cached embedding data or None if not found
        """
        if not self.enabled:
            return None
        
        cache_key = self._get_cache_key(chunk_checksum, provider, model)
        
        if cache_key in self.index:
            cache_entry = self.index[cache_key]
            
            # Validate cache entry
            if self._validate_entry(cache_entry, chunk_id):
                self.hits += 1
                self.logger.debug(f"Cache hit: {chunk_id}")
                return cache_entry
        
        self.misses += 1
        self.logger.debug(f"Cache miss: {chunk_id}")
        return None
    
    def _validate_entry(
        self,
        entry: Dict[str, Any],
        chunk_id: str
    ) -> bool:
        """
        Validate cache entry.
        
        Args:
            entry: Cache entry to validate
            chunk_id: Expected chunk ID
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required = ['embedding', 'metadata', 'chunk_id']
        if not all(field in entry for field in required):
            return False
        
        # Check chunk ID matches
        if entry['chunk_id'] != chunk_id:
            return False
        
        # Check embedding is valid
        embedding = entry.get('embedding')
        if not embedding or not isinstance(embedding, list):
            return False
        
        return True
    
    def put(
        self,
        chunk_id: str,
        chunk_checksum: str,
        provider: str,
        model: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """
        Store embedding in cache.
        
        Args:
            chunk_id: Chunk identifier
            chunk_checksum: Checksum of chunk text
            provider: Embedding provider
            model: Model name
            embedding: Embedding vector
            metadata: Embedding metadata
        """
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(chunk_checksum, provider, model)
        
        entry = {
            'chunk_id': chunk_id,
            'chunk_checksum': chunk_checksum,
            'provider': provider,
            'model': model,
            'embedding': embedding,
            'metadata': metadata,
            'cached_at': datetime.now().isoformat()
        }
        
        self.index[cache_key] = entry
        self.logger.debug(f"Cached embedding: {chunk_id}")
    
    def invalidate(
        self,
        chunk_checksum: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> int:
        """
        Invalidate cache entries.
        
        Args:
            chunk_checksum: Invalidate specific chunk (optional)
            provider: Invalidate specific provider (optional)
            model: Invalidate specific model (optional)
            
        Returns:
            Number of entries invalidated
        """
        if not self.enabled:
            return 0
        
        initial_count = len(self.index)
        
        # Filter entries to keep
        new_index = {}
        for key, entry in self.index.items():
            keep = True
            
            if chunk_checksum and entry.get('chunk_checksum') == chunk_checksum:
                keep = False
            
            if provider and entry.get('provider') == provider:
                keep = False
            
            if model and entry.get('model') == model:
                keep = False
            
            if keep:
                new_index[key] = entry
        
        self.index = new_index
        invalidated = initial_count - len(self.index)
        
        if invalidated > 0:
            self._save_index()
            self.logger.info(f"Invalidated {invalidated} cache entries")
        
        return invalidated
    
    def clear(self) -> int:
        """
        Clear entire cache.
        
        Returns:
            Number of entries cleared
        """
        count = len(self.index)
        self.index = {}
        self._save_index()
        self.logger.info(f"Cleared cache ({count} entries)")
        return count
    
    def save(self) -> None:
        """Save cache to disk."""
        self._save_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache stats
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'enabled': self.enabled,
            'strategy': self.strategy,
            'entries': len(self.index),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'cache_dir': str(self.cache_dir)
        }
