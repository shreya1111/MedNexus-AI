"""
Query processor for MedNexus-AI.

Preprocesses search queries for better retrieval.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import re

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


class QueryProcessor:
    """Processes and normalizes search queries."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize query processor.
        
        Args:
            config: Query preprocessing configuration
        """
        qp_config = config.get('query_preprocessing', {})
        self.enabled = qp_config.get('enabled', True)
        self.lowercase = qp_config.get('lowercase', True)
        self.normalize_whitespace = qp_config.get('normalize_whitespace', True)
        self.expand_abbreviations = qp_config.get('expand_abbreviations', True)
        self.abbreviations = qp_config.get('abbreviations', {})
        self.min_length = qp_config.get('min_query_length', 2)
        self.max_length = qp_config.get('max_query_length', 500)
        
        self.logger = get_logger(__name__)
    
    def process(self, query: str) -> str:
        """
        Process query.
        
        Args:
            query: Raw query text
            
        Returns:
            Processed query
        """
        if not self.enabled:
            return query
        
        processed = query
        
        # Normalize whitespace
        if self.normalize_whitespace:
            processed = ' '.join(processed.split())
        
        # Lowercase
        if self.lowercase:
            processed = processed.lower()
        
        # Expand abbreviations
        if self.expand_abbreviations and self.abbreviations:
            processed = self._expand_abbreviations(processed)
        
        # Validate length
        if len(processed) < self.min_length:
            raise ValueError(f"Query too short (min: {self.min_length})")
        if len(processed) > self.max_length:
            processed = processed[:self.max_length]
        
        return processed
    
    def _expand_abbreviations(self, query: str) -> str:
        """Expand medical abbreviations."""
        words = query.split()
        expanded = []
        
        for word in words:
            # Check if word is an abbreviation
            if word in self.abbreviations:
                expanded.append(self.abbreviations[word])
            else:
                expanded.append(word)
        
        return ' '.join(expanded)
    
    def validate(self, query: str) -> bool:
        """
        Validate query.
        
        Args:
            query: Query to validate
            
        Returns:
            True if valid
        """
        if not query or not query.strip():
            return False
        
        if len(query) < self.min_length:
            return False
        
        if len(query) > self.max_length:
            return False
        
        return True
