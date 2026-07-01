"""
Hallucination checker for verifying response accuracy.

Detects unsupported claims and ensures context grounding.
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger


@dataclass
class HallucinationCheckResult:
    """Result of hallucination check."""
    
    is_grounded: bool
    confidence: float
    unsupported_claims: List[str]
    context_coverage: float
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_grounded': self.is_grounded,
            'confidence': self.confidence,
            'unsupported_claims': self.unsupported_claims,
            'context_coverage': self.context_coverage,
            'warnings': self.warnings
        }


class HallucinationChecker:
    """
    Checks responses for hallucinations.
    
    Features:
    - Context grounding verification
    - Unsupported claim detection
    - Citation verification
    - Confidence estimation
    """
    
    # Claim indicators (statements that should be backed by context)
    CLAIM_PATTERNS = [
        r'(is|are|was|were) (a|an|the)? ?\w+',
        r'(causes|treats|prevents|reduces|increases)',
        r'\d+%|\d+ percent',
        r'studies (show|indicate|suggest)',
        r'research (shows|indicates|suggests)',
        r'according to',
    ]
    
    # Hedging phrases (uncertainty indicators)
    HEDGING_PHRASES = [
        'may', 'might', 'could', 'possibly', 'potentially',
        'likely', 'probably', 'generally', 'typically',
        'appears to', 'seems to', 'suggests that',
        'based on the available information',
        'according to the sources',
        'the retrieved information'
    ]
    
    # Absolute statements (should be flagged)
    ABSOLUTE_PHRASES = [
        'always', 'never', 'all', 'none', 'every',
        'completely', 'definitely', 'certainly',
        'guaranteed', 'proven', 'fact'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize hallucination checker.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Hallucination configuration
        hallucination_config = config.get('hallucination', {})
        self.enabled = hallucination_config.get('enabled', True)
        self.verify_context = hallucination_config.get('verify_context_usage', True)
        self.verify_citations = hallucination_config.get('verify_citations', True)
        self.detect_claims = hallucination_config.get('detect_unsupported_claims', True)
        self.min_confidence = hallucination_config.get('min_confidence', 0.3)
        
        self.logger.info("HallucinationChecker initialized")
    
    def check_response(
        self,
        response: str,
        context: str,
        citations: List[Any],
        query: str
    ) -> HallucinationCheckResult:
        """
        Check response for hallucinations.
        
        Args:
            response: Assistant's response
            context: Retrieved context
            citations: Citations used
            query: Original query
            
        Returns:
            HallucinationCheckResult
        """
        if not self.enabled:
            return HallucinationCheckResult(
                is_grounded=True,
                confidence=1.0,
                unsupported_claims=[],
                context_coverage=1.0,
                warnings=[]
            )
        
        try:
            warnings = []
            unsupported_claims = []
            
            # 1. Check context grounding
            coverage = self._calculate_context_coverage(response, context)
            
            if coverage < 0.5:
                warnings.append(f"Low context coverage: {coverage:.2%}")
            
            # 2. Detect unsupported claims
            if self.detect_claims:
                claims = self._detect_claims(response)
                unsupported = self._verify_claims(claims, context)
                unsupported_claims.extend(unsupported)
            
            # 3. Check for absolute statements
            absolute = self._detect_absolute_statements(response)
            if absolute:
                warnings.append(f"Found {len(absolute)} absolute statements")
            
            # 4. Verify citations
            if self.verify_citations and not citations:
                warnings.append("No citations provided")
            
            # 5. Check hedging (good for medical info)
            hedging_score = self._calculate_hedging_score(response)
            if hedging_score < 0.1:
                warnings.append("Response lacks appropriate uncertainty language")
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(
                coverage,
                len(unsupported_claims),
                len(absolute),
                hedging_score,
                len(citations)
            )
            
            # Determine if grounded
            is_grounded = (
                confidence >= self.min_confidence and
                len(unsupported_claims) == 0 and
                coverage >= 0.3
            )
            
            result = HallucinationCheckResult(
                is_grounded=is_grounded,
                confidence=confidence,
                unsupported_claims=unsupported_claims,
                context_coverage=coverage,
                warnings=warnings
            )
            
            self.logger.debug(
                f"Hallucination check: grounded={is_grounded}, "
                f"confidence={confidence:.2f}, claims={len(unsupported_claims)}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Hallucination check failed: {e}")
            
            return HallucinationCheckResult(
                is_grounded=False,
                confidence=0.0,
                unsupported_claims=[],
                context_coverage=0.0,
                warnings=[f"Check failed: {str(e)}"]
            )
    
    def _calculate_context_coverage(
        self,
        response: str,
        context: str
    ) -> float:
        """
        Calculate how much of response is covered by context.
        
        Args:
            response: Response text
            context: Context text
            
        Returns:
            Coverage ratio (0-1)
        """
        if not context:
            return 0.0
        
        # Tokenize (simple word-based)
        response_words = set(response.lower().split())
        context_words = set(context.lower().split())
        
        # Remove common words
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were'
        }
        
        response_words -= common_words
        context_words -= common_words
        
        if not response_words:
            return 0.0
        
        # Calculate overlap
        overlap = response_words & context_words
        coverage = len(overlap) / len(response_words)
        
        return coverage
    
    def _detect_claims(self, response: str) -> List[str]:
        """
        Detect factual claims in response.
        
        Args:
            response: Response text
            
        Returns:
            List of detected claims
        """
        claims = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', response)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if sentence contains claim patterns
            for pattern in self.CLAIM_PATTERNS:
                if re.search(pattern, sentence.lower()):
                    claims.append(sentence)
                    break
        
        return claims
    
    def _verify_claims(
        self,
        claims: List[str],
        context: str
    ) -> List[str]:
        """
        Verify claims against context.
        
        Args:
            claims: List of claims
            context: Context text
            
        Returns:
            List of unsupported claims
        """
        unsupported = []
        context_lower = context.lower()
        
        for claim in claims:
            # Extract key terms from claim
            claim_lower = claim.lower()
            
            # Remove common words
            words = claim_lower.split()
            key_words = [
                w for w in words
                if len(w) > 3 and w not in self.HEDGING_PHRASES
            ]
            
            # Check if key terms appear in context
            support_count = sum(1 for word in key_words if word in context_lower)
            
            # If less than 30% of key words found, mark as unsupported
            if key_words and support_count / len(key_words) < 0.3:
                unsupported.append(claim)
        
        return unsupported
    
    def _detect_absolute_statements(self, response: str) -> List[str]:
        """
        Detect absolute statements.
        
        Args:
            response: Response text
            
        Returns:
            List of absolute statements
        """
        absolute = []
        
        sentences = re.split(r'[.!?]+', response)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_lower = sentence.lower()
            
            for phrase in self.ABSOLUTE_PHRASES:
                if phrase in sentence_lower:
                    absolute.append(sentence)
                    break
        
        return absolute
    
    def _calculate_hedging_score(self, response: str) -> float:
        """
        Calculate hedging score.
        
        Args:
            response: Response text
            
        Returns:
            Hedging score (0-1)
        """
        response_lower = response.lower()
        
        hedging_count = sum(
            1 for phrase in self.HEDGING_PHRASES
            if phrase in response_lower
        )
        
        # Normalize by response length (sentences)
        sentences = len(re.split(r'[.!?]+', response))
        
        if sentences == 0:
            return 0.0
        
        # Target: at least 1 hedging phrase per 3 sentences
        score = min(hedging_count / (sentences / 3), 1.0)
        
        return score
    
    def _calculate_confidence(
        self,
        coverage: float,
        unsupported_count: int,
        absolute_count: int,
        hedging_score: float,
        citation_count: int
    ) -> float:
        """
        Calculate overall confidence.
        
        Args:
            coverage: Context coverage
            unsupported_count: Number of unsupported claims
            absolute_count: Number of absolute statements
            hedging_score: Hedging score
            citation_count: Number of citations
            
        Returns:
            Confidence score (0-1)
        """
        # Start with context coverage
        confidence = coverage * 0.4
        
        # Penalize unsupported claims
        confidence -= unsupported_count * 0.1
        
        # Penalize absolute statements
        confidence -= absolute_count * 0.05
        
        # Reward hedging
        confidence += hedging_score * 0.2
        
        # Reward citations
        confidence += min(citation_count * 0.1, 0.3)
        
        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get checker statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'enabled': self.enabled,
            'verify_context': self.verify_context,
            'verify_citations': self.verify_citations,
            'detect_claims': self.detect_claims,
            'min_confidence': self.min_confidence,
            'claim_patterns': len(self.CLAIM_PATTERNS),
            'hedging_phrases': len(self.HEDGING_PHRASES),
            'absolute_phrases': len(self.ABSOLUTE_PHRASES)
        }
