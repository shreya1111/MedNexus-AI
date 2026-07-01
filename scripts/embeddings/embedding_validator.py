"""
Embedding validator for MedNexus-AI.

Validates embedding quality and consistency.
"""

import sys
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


@dataclass
class ValidationResult:
    """Result of embedding validation."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    checks_passed: int
    checks_failed: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class EmbeddingValidator:
    """Validates embeddings for quality and consistency."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize validator.
        
        Args:
            config: Validation configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.strict_mode = config.get('strict_mode', True)
        
        # Validation checks
        self.checks = config.get('checks', {})
        self.thresholds = config.get('thresholds', {})
        
        # Statistics
        self.total_validated = 0
        self.total_passed = 0
        self.total_failed = 0
    
    def validate_embedding(
        self,
        embedding: List[float],
        expected_dimension: int,
        chunk_id: str = ""
    ) -> ValidationResult:
        """
        Validate a single embedding.
        
        Args:
            embedding: Embedding vector to validate
            expected_dimension: Expected dimension
            chunk_id: Chunk identifier for error messages
            
        Returns:
            ValidationResult object
        """
        errors = []
        warnings = []
        passed = 0
        failed = 0
        
        # Check 1: Dimension
        if self.checks.get('dimension', True):
            if len(embedding) != expected_dimension:
                errors.append(
                    f"Dimension mismatch: expected {expected_dimension}, "
                    f"got {len(embedding)}"
                )
                failed += 1
            else:
                passed += 1
        
        # Check 2: NaN values
        if self.checks.get('nan_values', True):
            if any(math.isnan(x) for x in embedding):
                errors.append("Contains NaN values")
                failed += 1
            else:
                passed += 1
        
        # Check 3: Infinite values
        if self.checks.get('inf_values', True):
            if any(math.isinf(x) for x in embedding):
                errors.append("Contains infinite values")
                failed += 1
            else:
                passed += 1
        
        # Check 4: Zero vector
        if self.checks.get('zero_vectors', True):
            if all(x == 0 for x in embedding):
                errors.append("Zero vector detected")
                failed += 1
            else:
                passed += 1
        
        # Check 5: Vector norm
        norm = math.sqrt(sum(x * x for x in embedding))
        
        min_norm = self.thresholds.get('min_norm', 0.01)
        max_norm = self.thresholds.get('max_norm', 100.0)
        
        if norm < min_norm:
            warnings.append(f"Low vector norm: {norm:.6f} < {min_norm}")
        elif norm > max_norm:
            warnings.append(f"High vector norm: {norm:.6f} > {max_norm}")
        
        # Check 6: Zero ratio
        max_zero_ratio = self.thresholds.get('max_zero_ratio', 0.1)
        zero_count = sum(1 for x in embedding if x == 0)
        zero_ratio = zero_count / len(embedding)
        
        if zero_ratio > max_zero_ratio:
            warnings.append(
                f"High zero ratio: {zero_ratio:.2%} > {max_zero_ratio:.2%}"
            )
        
        # Update statistics
        self.total_validated += 1
        is_valid = len(errors) == 0
        
        if is_valid:
            self.total_passed += 1
        else:
            self.total_failed += 1
            if chunk_id:
                self.logger.warning(f"Validation failed for {chunk_id}: {errors}")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            checks_passed=passed,
            checks_failed=failed
        )
    
    def validate_metadata(
        self,
        metadata: Dict[str, Any],
        required_fields: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate embedding metadata.
        
        Args:
            metadata: Metadata dictionary
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, errors)
        """
        if not self.checks.get('metadata_consistency', True):
            return True, []
        
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")
            elif metadata[field] is None:
                errors.append(f"Required field is None: {field}")
        
        # Check dimension
        if 'dimension' in metadata:
            dim = metadata['dimension']
            if not isinstance(dim, int) or dim <= 0:
                errors.append(f"Invalid dimension: {dim}")
        
        # Check checksums
        if self.checks.get('checksum_match', True):
            if 'checksum' in metadata and not metadata['checksum']:
                errors.append("Empty checksum")
            if 'chunk_checksum' in metadata and not metadata['chunk_checksum']:
                errors.append("Empty chunk_checksum")
        
        return len(errors) == 0, errors
    
    def detect_duplicates(
        self,
        embeddings: List[List[float]],
        chunk_ids: List[str]
    ) -> List[Tuple[int, int, float]]:
        """
        Detect duplicate embeddings using cosine similarity.
        
        Args:
            embeddings: List of embedding vectors
            chunk_ids: List of chunk IDs (for logging)
            
        Returns:
            List of (index1, index2, similarity) tuples for duplicates
        """
        if not self.checks.get('duplicates', True):
            return []
        
        duplicates = []
        threshold = self.thresholds.get('duplicate_tolerance', 0.9999)
        
        # Convert to numpy for efficient computation
        try:
            embeddings_np = np.array(embeddings)
            
            # Normalize vectors
            norms = np.linalg.norm(embeddings_np, axis=1, keepdims=True)
            embeddings_norm = embeddings_np / (norms + 1e-10)
            
            # Compute cosine similarity matrix
            similarity_matrix = np.dot(embeddings_norm, embeddings_norm.T)
            
            # Find duplicates
            n = len(embeddings)
            for i in range(n):
                for j in range(i + 1, n):
                    sim = similarity_matrix[i, j]
                    if sim >= threshold:
                        duplicates.append((i, j, float(sim)))
                        self.logger.warning(
                            f"Duplicate detected: {chunk_ids[i]} ~ {chunk_ids[j]} "
                            f"(similarity: {sim:.4f})"
                        )
        
        except Exception as e:
            self.logger.error(f"Duplicate detection failed: {e}")
        
        return duplicates
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get validation statistics.
        
        Returns:
            Dictionary containing validation stats
        """
        return {
            'total_validated': self.total_validated,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'pass_rate': (
                self.total_passed / self.total_validated * 100
                if self.total_validated > 0 else 0
            ),
            'strict_mode': self.strict_mode
        }
