"""
Metadata filtering for vector search.

Supports filtering by source, disease, drug, document type, date, and more.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


class MetadataFilter:
    """
    Metadata filtering for search results.
    
    Supports various operators: eq, ne, in, nin, gt, gte, lt, lte,
    contains, startswith, endswith.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize metadata filter.
        
        Args:
            config: Retrieval configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Filter configuration
        filter_config = config.get('metadata_filtering', {})
        self.enabled = filter_config.get('enabled', True)
        self.supported_fields = set(filter_config.get('supported_fields', []))
        self.supported_operators = set(filter_config.get('operators', []))
        
        self.logger.info(
            f"MetadataFilter initialized: {len(self.supported_fields)} fields, "
            f"{len(self.supported_operators)} operators"
        )
    
    def validate_filter(self, filters: Dict[str, Any]) -> bool:
        """
        Validate filter specification.
        
        Args:
            filters: Filter dictionary
            
        Returns:
            True if valid, False otherwise
        """
        if not self.enabled:
            return True
        
        if not filters:
            return True
        
        for field, condition in filters.items():
            # Check if field is supported
            if field not in self.supported_fields:
                self.logger.warning(f"Unsupported filter field: {field}")
                return False
            
            # If condition is a dict, validate operator
            if isinstance(condition, dict):
                for operator in condition.keys():
                    if operator not in self.supported_operators:
                        self.logger.warning(f"Unsupported operator: {operator}")
                        return False
        
        return True
    
    def apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply metadata filters to search results.
        
        Args:
            results: Search results
            filters: Filter specification
            
        Returns:
            Filtered results
        """
        if not self.enabled or not filters:
            return results
        
        if not self.validate_filter(filters):
            self.logger.warning("Invalid filters, returning unfiltered results")
            return results
        
        filtered = []
        
        for result in results:
            metadata = result.get('metadata', {})
            
            if self._match_filters(metadata, filters):
                filtered.append(result)
        
        self.logger.info(
            f"Filtered {len(results)} results to {len(filtered)} results"
        )
        
        return filtered
    
    def _match_filters(
        self,
        metadata: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """
        Check if metadata matches all filters.
        
        Args:
            metadata: Document metadata
            filters: Filter specification
            
        Returns:
            True if matches, False otherwise
        """
        for field, condition in filters.items():
            if not self._match_condition(metadata, field, condition):
                return False
        
        return True
    
    def _match_condition(
        self,
        metadata: Dict[str, Any],
        field: str,
        condition: Any
    ) -> bool:
        """
        Check if a single condition is met.
        
        Args:
            metadata: Document metadata
            field: Field name
            condition: Condition value or operator dict
            
        Returns:
            True if condition is met
        """
        # Get field value from metadata
        value = metadata.get(field)
        
        # If field doesn't exist, condition fails
        if value is None:
            return False
        
        # Simple equality check
        if not isinstance(condition, dict):
            return value == condition
        
        # Operator-based conditions
        for operator, target in condition.items():
            if not self._apply_operator(value, operator, target):
                return False
        
        return True
    
    def _apply_operator(
        self,
        value: Any,
        operator: str,
        target: Any
    ) -> bool:
        """
        Apply a comparison operator.
        
        Args:
            value: Field value
            operator: Operator name (eq, ne, gt, etc.)
            target: Target value
            
        Returns:
            True if condition is met
        """
        try:
            if operator == 'eq':
                return value == target
            
            elif operator == 'ne':
                return value != target
            
            elif operator == 'in':
                return value in target
            
            elif operator == 'nin':
                return value not in target
            
            elif operator == 'gt':
                return value > target
            
            elif operator == 'gte':
                return value >= target
            
            elif operator == 'lt':
                return value < target
            
            elif operator == 'lte':
                return value <= target
            
            elif operator == 'contains':
                return target in str(value)
            
            elif operator == 'startswith':
                return str(value).startswith(str(target))
            
            elif operator == 'endswith':
                return str(value).endswith(str(target))
            
            else:
                self.logger.warning(f"Unknown operator: {operator}")
                return False
        
        except Exception as e:
            self.logger.warning(f"Error applying operator {operator}: {e}")
            return False
    
    def build_chroma_filter(
        self,
        filters: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Build ChromaDB-compatible filter specification.
        
        ChromaDB uses where clauses with operators like $eq, $ne, $in, etc.
        
        Args:
            filters: Our filter specification
            
        Returns:
            ChromaDB where clause
        """
        if not filters:
            return None
        
        # Convert to ChromaDB format
        where = {}
        
        for field, condition in filters.items():
            if isinstance(condition, dict):
                # Convert operators to ChromaDB format
                for operator, value in condition.items():
                    chroma_op = self._to_chroma_operator(operator)
                    if chroma_op:
                        where[field] = {chroma_op: value}
            else:
                # Simple equality
                where[field] = condition
        
        return where if where else None
    
    def _to_chroma_operator(self, operator: str) -> Optional[str]:
        """
        Convert our operator to ChromaDB operator.
        
        Args:
            operator: Our operator name
            
        Returns:
            ChromaDB operator or None
        """
        mapping = {
            'eq': '$eq',
            'ne': '$ne',
            'in': '$in',
            'nin': '$nin',
            'gt': '$gt',
            'gte': '$gte',
            'lt': '$lt',
            'lte': '$lte',
            'contains': '$contains',
        }
        
        return mapping.get(operator)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get filter statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'enabled': self.enabled,
            'supported_fields': list(self.supported_fields),
            'supported_operators': list(self.supported_operators)
        }


def create_filter_examples() -> Dict[str, Dict[str, Any]]:
    """
    Create example filter specifications.
    
    Returns:
        Dictionary of example filters
    """
    return {
        'filter_by_source': {
            'source': 'medquad'
        },
        
        'filter_by_disease': {
            'disease': 'diabetes'
        },
        
        'filter_by_multiple': {
            'source': 'medquad',
            'language': 'en'
        },
        
        'filter_with_operators': {
            'source': {'in': ['medquad', 'pubmed']},
            'date': {'gte': '2020-01-01'}
        },
        
        'filter_contains': {
            'document_type': {'contains': 'guideline'}
        },
        
        'filter_exclude': {
            'source': {'ne': 'test'},
            'language': {'nin': ['fr', 'de']}
        }
    }
