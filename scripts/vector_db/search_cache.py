"""
Search cache for MedNexus-AI.

Implements LRU cache with TTL for search results.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import OrderedDict
import hashlib

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


class SearchCache:
    """LRU cache for search results with TTL."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize search cache.
        
        Args:
            config: Cache configuration
        """
        cache_config = config.get('cache', {})
        self.enabled = cache_config.get('enabled', True)
        self.max_size = cache_config.get('max_size', 1000)
        self.ttl_seconds = cache_config.get('ttl_seconds', 3600)
        
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.logger = get_logger(__name__)
    
    def get(self, query_hash: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached results."""
        if not self.enabled:
            return None
        
        if query_hash in self.cache:
            entry = self.cache[query_hash]
            
            # Check TTL
            if time.time() - entry['timestamp'] < self.ttl_seconds:
                # Move to end (LRU)
                self.cache.move_to_end(query_hash)
                self.hits += 1
                return entry['results']
            else:
                # Expired
                del self.cache[query_hash]
        
        self.misses += 1
        return None
    
    def put(self, query_hash: str, results: List[Dict[str, Any]]) -> None:
        """Cache results."""
        if not self.enabled:
            return
        
        # Evict oldest if full
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[query_hash] = {
            'results': results,
            'timestamp': time.time()
        }
    
    def hash_query(
        self,
        query_text: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate query hash."""
        query_str = f"{query_text}|{top_k}|{str(filters)}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'enabled': self.enabled,
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }
