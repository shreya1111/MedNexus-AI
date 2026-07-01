"""
Confidence estimator for response quality assessment.

Calculates multi-factor confidence scores for assistant responses.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger


class ConfidenceLevel(str, Enum):
    """Confidence level categories."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ConfidenceScore:
    """Confidence score result."""
    
    overall_score: float
    level: ConfidenceLevel
    factors: Dict[str, float]
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'overall_score': self.overall_score,
            'level': self.level.value,
            'factors': self.factors,
            'explanation': self.explanation
        }


class ConfidenceEstimator:
    """
    Estimates confidence in assistant responses.
    
    Factors:
    - Retrieval similarity
    - Context completeness
    - Citation coverage
    - Response validation
    - Hallucination check
    """
    
    # Confidence thresholds
    HIGH_THRESHOLD = 0.75
    MEDIUM_THRESHOLD = 0.50
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize confidence estimator.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Hallucination configuration
        hallucination_config = config.get('hallucination', {})
        self.min_confidence = hallucination_config.get('min_confidence', 0.3)
        self.low_threshold = hallucination_config.get('low_confidence_threshold', 0.5)
        
        # Factor weights
        self.weights = {
            'retrieval_quality': 0.25,
            'context_completeness': 0.20,
            'citation_coverage': 0.15,
            'validation_score': 0.20,
            'hallucination_score': 0.20
        }
        
        self.logger.info("ConfidenceEstimator initialized")
    
    def estimate_confidence(
        self,
        retrieved_docs: List[Dict[str, Any]],
        citations: List[Any],
        validation_result: Optional[Any] = None,
        hallucination_result: Optional[Any] = None,
        response_length: int = 0
    ) -> ConfidenceScore:
        """
        Estimate confidence in response.
        
        Args:
            retrieved_docs: Retrieved documents
            citations: Citations used
            validation_result: Output validation result
            hallucination_result: Hallucination check result
            response_length: Length of response
            
        Returns:
            ConfidenceScore
        """
        try:
            factors = {}
            
            # 1. Retrieval quality
            factors['retrieval_quality'] = self._calculate_retrieval_quality(
                retrieved_docs
            )
            
            # 2. Context completeness
            factors['context_completeness'] = self._calculate_context_completeness(
                retrieved_docs
            )
            
            # 3. Citation coverage
            factors['citation_coverage'] = self._calculate_citation_coverage(
                citations,
                response_length
            )
            
            # 4. Validation score
            if validation_result:
                factors['validation_score'] = validation_result.score
            else:
                factors['validation_score'] = 0.7  # Neutral
            
            # 5. Hallucination score
            if hallucination_result:
                factors['hallucination_score'] = hallucination_result.confidence
            else:
                factors['hallucination_score'] = 0.7  # Neutral
            
            # Calculate weighted overall score
            overall_score = sum(
                factors[factor] * self.weights[factor]
                for factor in factors
            )
            
            # Determine confidence level
            if overall_score >= self.HIGH_THRESHOLD:
                level = ConfidenceLevel.HIGH
                explanation = "High confidence - well-supported response with strong evidence"
            elif overall_score >= self.MEDIUM_THRESHOLD:
                level = ConfidenceLevel.MEDIUM
                explanation = "Medium confidence - adequate support with some limitations"
            else:
                level = ConfidenceLevel.LOW
                explanation = "Low confidence - limited evidence or context"
            
            # Create detailed explanation
            detailed_explanation = self._build_explanation(factors, level)
            
            result = ConfidenceScore(
                overall_score=overall_score,
                level=level,
                factors=factors,
                explanation=detailed_explanation
            )
            
            self.logger.debug(
                f"Confidence: {level.value} ({overall_score:.2f}) - {explanation}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Confidence estimation failed: {e}")
            
            return ConfidenceScore(
                overall_score=0.0,
                level=ConfidenceLevel.LOW,
                factors={},
                explanation="Confidence estimation failed"
            )
    
    def _calculate_retrieval_quality(
        self,
        retrieved_docs: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate retrieval quality score.
        
        Args:
            retrieved_docs: Retrieved documents
            
        Returns:
            Quality score (0-1)
        """
        if not retrieved_docs:
            return 0.0
        
        # Average similarity score
        similarities = [
            doc.get('similarity', 0.0)
            for doc in retrieved_docs
        ]
        
        avg_similarity = sum(similarities) / len(similarities)
        
        # Bonus for multiple high-quality documents
        high_quality = sum(1 for s in similarities if s > 0.7)
        quality_bonus = min(high_quality * 0.1, 0.2)
        
        score = min(avg_similarity + quality_bonus, 1.0)
        
        return score
    
    def _calculate_context_completeness(
        self,
        retrieved_docs: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate context completeness.
        
        Args:
            retrieved_docs: Retrieved documents
            
        Returns:
            Completeness score (0-1)
        """
        if not retrieved_docs:
            return 0.0
        
        # Check document count
        doc_count_score = min(len(retrieved_docs) / 5, 1.0)
        
        # Check for diverse sources
        sources = set(
            doc.get('metadata', {}).get('source', 'unknown')
            for doc in retrieved_docs
        )
        source_diversity = min(len(sources) / 3, 1.0)
        
        # Check total content length
        total_length = sum(
            len(doc.get('document', ''))
            for doc in retrieved_docs
        )
        length_score = min(total_length / 5000, 1.0)
        
        # Weighted average
        score = (
            doc_count_score * 0.4 +
            source_diversity * 0.3 +
            length_score * 0.3
        )
        
        return score
    
    def _calculate_citation_coverage(
        self,
        citations: List[Any],
        response_length: int
    ) -> float:
        """
        Calculate citation coverage.
        
        Args:
            citations: List of citations
            response_length: Length of response
            
        Returns:
            Coverage score (0-1)
        """
        if not citations:
            return 0.0
        
        # Citation density (citations per 500 chars)
        if response_length == 0:
            return 0.0
        
        density = len(citations) / (response_length / 500)
        density_score = min(density, 1.0)
        
        # Citation diversity (unique sources)
        unique_sources = set(
            getattr(c, 'source', 'unknown')
            for c in citations
        )
        diversity_score = min(len(unique_sources) / 3, 1.0)
        
        # Weighted average
        score = density_score * 0.6 + diversity_score * 0.4
        
        return score
    
    def _build_explanation(
        self,
        factors: Dict[str, float],
        level: ConfidenceLevel
    ) -> str:
        """
        Build detailed explanation.
        
        Args:
            factors: Factor scores
            level: Confidence level
            
        Returns:
            Explanation text
        """
        lines = []
        
        # Overall assessment
        if level == ConfidenceLevel.HIGH:
            lines.append("High confidence: The response is well-supported by retrieved evidence.")
        elif level == ConfidenceLevel.MEDIUM:
            lines.append("Medium confidence: The response has adequate support but some limitations.")
        else:
            lines.append("Low confidence: Limited evidence available to support this response.")
        
        # Factor breakdown
        lines.append("\nFactors:")
        
        for factor, score in factors.items():
            # Format factor name
            factor_name = factor.replace('_', ' ').title()
            
            # Categorize score
            if score >= 0.75:
                category = "Strong"
            elif score >= 0.5:
                category = "Adequate"
            else:
                category = "Weak"
            
            lines.append(f"  • {factor_name}: {score:.2f} ({category})")
        
        return "\n".join(lines)
    
    def should_warn_low_confidence(
        self,
        confidence_score: ConfidenceScore
    ) -> bool:
        """
        Check if low confidence warning should be shown.
        
        Args:
            confidence_score: Confidence score
            
        Returns:
            True if warning should be shown
        """
        return (
            confidence_score.level == ConfidenceLevel.LOW or
            confidence_score.overall_score < self.low_threshold
        )
    
    def get_confidence_message(
        self,
        confidence_score: ConfidenceScore
    ) -> str:
        """
        Get user-friendly confidence message.
        
        Args:
            confidence_score: Confidence score
            
        Returns:
            Message text
        """
        if confidence_score.level == ConfidenceLevel.HIGH:
            return (
                "This answer is well-supported by multiple reliable sources "
                "in the knowledge base."
            )
        elif confidence_score.level == ConfidenceLevel.MEDIUM:
            return (
                "This answer is based on available information, but may benefit "
                "from additional verification."
            )
        else:
            return (
                "⚠️ Limited information was available to answer this question. "
                "The supporting evidence is insufficient. Please consult additional "
                "sources or a healthcare professional for more comprehensive information."
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get estimator statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'min_confidence': self.min_confidence,
            'low_threshold': self.low_threshold,
            'high_threshold': self.HIGH_THRESHOLD,
            'medium_threshold': self.MEDIUM_THRESHOLD,
            'weights': self.weights
        }
