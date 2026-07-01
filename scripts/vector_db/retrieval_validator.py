"""
Validation module for vector retrieval system.

Validates collection consistency, vector integrity, and metadata quality.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


@dataclass
class ValidationResult:
    """Validation result."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    statistics: Dict[str, Any]


class RetrievalValidator:
    """
    Validator for vector retrieval system.
    
    Checks for missing vectors, duplicate IDs, broken metadata,
    and collection consistency.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize retrieval validator.
        
        Args:
            config: Retrieval configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Validation configuration
        validation_config = config.get('validation', {})
        self.enabled = validation_config.get('enabled', True)
        self.strict_mode = validation_config.get('strict_mode', False)
        
        checks = validation_config.get('checks', {})
        self.check_missing_vectors = checks.get('missing_vectors', True)
        self.check_duplicate_ids = checks.get('duplicate_ids', True)
        self.check_broken_metadata = checks.get('broken_metadata', True)
        self.check_consistency = checks.get('collection_consistency', True)
        self.check_checksums = checks.get('checksum_match', True)
        
        self.logger.info("RetrievalValidator initialized")
    
    def validate_collection(
        self,
        collection_manager,
        collection_name: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a ChromaDB collection.
        
        Args:
            collection_manager: CollectionManager instance
            collection_name: Collection name (uses default if None)
            
        Returns:
            ValidationResult
        """
        self.logger.info(f"Validating collection: {collection_name or 'default'}")
        
        errors = []
        warnings = []
        statistics = {}
        
        try:
            # Get collection
            collection = collection_manager.get_collection(collection_name)
            
            if collection is None:
                errors.append("Collection not found")
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    statistics=statistics
                )
            
            # Get collection data
            count = collection.count()
            statistics['total_documents'] = count
            
            if count == 0:
                warnings.append("Collection is empty")
                return ValidationResult(
                    is_valid=True,
                    errors=errors,
                    warnings=warnings,
                    statistics=statistics
                )
            
            # Get all data
            results = collection.get(
                include=['embeddings', 'metadatas', 'documents']
            )
            
            ids = results.get('ids', [])
            embeddings = results.get('embeddings', [])
            metadatas = results.get('metadatas', [])
            documents = results.get('documents', [])
            
            # Check for duplicates
            if self.check_duplicate_ids:
                duplicate_errors = self._check_duplicates(ids)
                errors.extend(duplicate_errors)
            
            # Check for missing vectors
            if self.check_missing_vectors:
                missing_errors = self._check_missing_vectors(ids, embeddings)
                errors.extend(missing_errors)
            
            # Check broken metadata
            if self.check_broken_metadata:
                metadata_errors, metadata_warnings = self._check_metadata(metadatas)
                errors.extend(metadata_errors)
                warnings.extend(metadata_warnings)
            
            # Check consistency
            if self.check_consistency:
                consistency_errors = self._check_consistency(
                    ids, embeddings, metadatas, documents
                )
                errors.extend(consistency_errors)
            
            # Calculate statistics
            statistics.update({
                'total_ids': len(ids),
                'total_embeddings': len(embeddings),
                'total_metadatas': len(metadatas),
                'total_documents': len(documents),
                'unique_ids': len(set(ids)),
                'error_count': len(errors),
                'warning_count': len(warnings)
            })
            
            is_valid = len(errors) == 0 or (not self.strict_mode and len(errors) < 10)
            
            self.logger.info(
                f"Validation complete: {len(errors)} errors, {len(warnings)} warnings"
            )
            
            return ValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                statistics=statistics
            )
        
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            errors.append(f"Validation exception: {str(e)}")
            
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                statistics=statistics
            )
    
    def _check_duplicates(self, ids: List[str]) -> List[str]:
        """
        Check for duplicate IDs.
        
        Args:
            ids: List of document IDs
            
        Returns:
            List of error messages
        """
        errors = []
        
        seen: Set[str] = set()
        duplicates: Set[str] = set()
        
        for doc_id in ids:
            if doc_id in seen:
                duplicates.add(doc_id)
            seen.add(doc_id)
        
        if duplicates:
            errors.append(f"Found {len(duplicates)} duplicate IDs")
            if len(duplicates) <= 5:
                errors.append(f"Duplicate IDs: {', '.join(list(duplicates))}")
        
        return errors
    
    def _check_missing_vectors(
        self,
        ids: List[str],
        embeddings: List[List[float]]
    ) -> List[str]:
        """
        Check for missing vectors.
        
        Args:
            ids: Document IDs
            embeddings: Embedding vectors
            
        Returns:
            List of error messages
        """
        errors = []
        
        if len(ids) != len(embeddings):
            errors.append(
                f"Mismatch: {len(ids)} IDs but {len(embeddings)} embeddings"
            )
        
        missing_count = 0
        
        for i, embedding in enumerate(embeddings):
            if embedding is None or len(embedding) == 0:
                missing_count += 1
        
        if missing_count > 0:
            errors.append(f"Found {missing_count} missing or empty embeddings")
        
        return errors
    
    def _check_metadata(
        self,
        metadatas: List[Dict[str, Any]]
    ) -> tuple[List[str], List[str]]:
        """
        Check metadata quality.
        
        Args:
            metadatas: List of metadata dictionaries
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        required_fields = ['chunk_id', 'document_id', 'source']
        
        missing_required = 0
        missing_optional = 0
        
        for i, metadata in enumerate(metadatas):
            if metadata is None:
                missing_required += 1
                continue
            
            # Check required fields
            for field in required_fields:
                if field not in metadata or metadata[field] is None:
                    missing_required += 1
                    break
        
        if missing_required > 0:
            errors.append(
                f"Found {missing_required} documents with missing required metadata"
            )
        
        return errors, warnings
    
    def _check_consistency(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        documents: List[str]
    ) -> List[str]:
        """
        Check consistency across collections.
        
        Args:
            ids: Document IDs
            embeddings: Embeddings
            metadatas: Metadata
            documents: Documents
            
        Returns:
            List of error messages
        """
        errors = []
        
        lengths = {
            'ids': len(ids),
            'embeddings': len(embeddings),
            'metadatas': len(metadatas),
            'documents': len(documents)
        }
        
        # Check if all arrays have same length
        unique_lengths = set(lengths.values())
        
        if len(unique_lengths) > 1:
            errors.append(
                f"Inconsistent array lengths: {lengths}"
            )
        
        return errors
    
    def validate_embeddings(
        self,
        embeddings: List[List[float]],
        expected_dimension: int
    ) -> ValidationResult:
        """
        Validate embedding vectors.
        
        Args:
            embeddings: List of embedding vectors
            expected_dimension: Expected dimension
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        statistics = {}
        
        statistics['total_embeddings'] = len(embeddings)
        statistics['expected_dimension'] = expected_dimension
        
        dimension_errors = 0
        nan_errors = 0
        inf_errors = 0
        zero_vectors = 0
        
        for i, embedding in enumerate(embeddings):
            # Check dimension
            if len(embedding) != expected_dimension:
                dimension_errors += 1
            
            # Check for NaN
            if any(x != x for x in embedding):  # NaN check
                nan_errors += 1
            
            # Check for infinity
            if any(abs(x) == float('inf') for x in embedding):
                inf_errors += 1
            
            # Check for zero vectors
            if all(x == 0 for x in embedding):
                zero_vectors += 1
        
        if dimension_errors > 0:
            errors.append(f"Found {dimension_errors} embeddings with wrong dimension")
        
        if nan_errors > 0:
            errors.append(f"Found {nan_errors} embeddings with NaN values")
        
        if inf_errors > 0:
            errors.append(f"Found {inf_errors} embeddings with infinity values")
        
        if zero_vectors > 0:
            warnings.append(f"Found {zero_vectors} zero vectors")
        
        statistics.update({
            'dimension_errors': dimension_errors,
            'nan_errors': nan_errors,
            'inf_errors': inf_errors,
            'zero_vectors': zero_vectors
        })
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            statistics=statistics
        )
    
    def generate_report(
        self,
        result: ValidationResult,
        output_path: Path
    ) -> None:
        """
        Generate validation report.
        
        Args:
            result: Validation result
            output_path: Output file path
        """
        import json
        
        report = {
            'is_valid': result.is_valid,
            'errors': result.errors,
            'warnings': result.warnings,
            'statistics': result.statistics,
            'timestamp': str(datetime.now())
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Validation report saved to: {output_path}")


from datetime import datetime
