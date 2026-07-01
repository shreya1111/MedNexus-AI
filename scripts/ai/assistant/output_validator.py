"""
Output validator for response quality assurance.

Validates citations, disclaimers, formatting, and completeness.
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger


@dataclass
class ValidationResult:
    """Result of output validation."""
    
    is_valid: bool
    score: float
    issues: List[str]
    warnings: List[str]
    checks: Dict[str, bool]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'score': self.score,
            'issues': self.issues,
            'warnings': self.warnings,
            'checks': self.checks
        }


class OutputValidator:
    """
    Validates assistant output.
    
    Features:
    - Citation presence check
    - Disclaimer verification
    - Formatting validation
    - Completeness check
    - Quality scoring
    """
    
    # Required disclaimer keywords
    DISCLAIMER_KEYWORDS = [
        'educational',
        'not replace',
        'consult',
        'healthcare provider',
        'medical advice',
        'professional'
    ]
    
    # Emergency keywords that should trigger warnings
    EMERGENCY_KEYWORDS = [
        'emergency',
        'urgent',
        'immediate',
        'severe',
        'critical',
        'life-threatening',
        'call 911'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output validator.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Citation configuration
        citation_config = config.get('citations', {})
        self.require_citations = citation_config.get('enabled', True)
        
        # Safety configuration
        safety_config = config.get('safety', {})
        self.require_disclaimer = safety_config.get('enabled', True)
        
        # Response configuration
        response_config = config.get('response', {})
        self.min_length = response_config.get('min_length', 100)
        self.max_length = response_config.get('max_output_tokens', 2048)
        
        self.logger.info("OutputValidator initialized")
    
    def validate_response(
        self,
        response: str,
        citations: List[Any],
        query: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validate assistant response.
        
        Args:
            response: Assistant's response
            citations: Citations used
            query: Original query
            metadata: Optional metadata
            
        Returns:
            ValidationResult
        """
        try:
            issues = []
            warnings = []
            checks = {}
            
            # 1. Check length
            length_ok = self._check_length(response)
            checks['length'] = length_ok
            
            if not length_ok:
                if len(response) < self.min_length:
                    issues.append(f"Response too short: {len(response)} chars")
                elif len(response) > self.max_length:
                    warnings.append(f"Response very long: {len(response)} chars")
            
            # 2. Check citations
            citations_ok = self._check_citations(response, citations)
            checks['citations'] = citations_ok
            
            if not citations_ok and self.require_citations:
                issues.append("Missing or insufficient citations")
            
            # 3. Check disclaimer
            disclaimer_ok = self._check_disclaimer(response)
            checks['disclaimer'] = disclaimer_ok
            
            if not disclaimer_ok and self.require_disclaimer:
                issues.append("Missing medical disclaimer")
            
            # 4. Check formatting
            formatting_ok = self._check_formatting(response)
            checks['formatting'] = formatting_ok
            
            if not formatting_ok:
                warnings.append("Response formatting could be improved")
            
            # 5. Check completeness
            completeness_ok = self._check_completeness(response, query)
            checks['completeness'] = completeness_ok
            
            if not completeness_ok:
                warnings.append("Response may not fully address the query")
            
            # 6. Check for emergency keywords
            emergency_check = self._check_emergency_keywords(response)
            checks['emergency_handled'] = emergency_check
            
            if not emergency_check:
                warnings.append("Response contains emergency keywords without proper warning")
            
            # 7. Check for unsupported diagnosis/treatment
            diagnosis_check = self._check_diagnosis_treatment(response)
            checks['no_diagnosis'] = diagnosis_check
            
            if not diagnosis_check:
                issues.append("Response may provide diagnosis or treatment recommendations")
            
            # Calculate score
            score = self._calculate_score(checks)
            
            # Determine validity
            is_valid = len(issues) == 0 and score >= 0.6
            
            result = ValidationResult(
                is_valid=is_valid,
                score=score,
                issues=issues,
                warnings=warnings,
                checks=checks
            )
            
            self.logger.debug(
                f"Validation: valid={is_valid}, score={score:.2f}, "
                f"issues={len(issues)}, warnings={len(warnings)}"
            )
            
            return result
        
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            
            return ValidationResult(
                is_valid=False,
                score=0.0,
                issues=[f"Validation error: {str(e)}"],
                warnings=[],
                checks={}
            )
    
    def _check_length(self, response: str) -> bool:
        """Check response length."""
        length = len(response)
        return self.min_length <= length <= self.max_length * 1.5
    
    def _check_citations(
        self,
        response: str,
        citations: List[Any]
    ) -> bool:
        """Check citation presence."""
        if not self.require_citations:
            return True
        
        # Check for citation markers
        citation_markers = re.findall(r'\[\d+\]|\(\d+\)', response)
        
        # Should have citations if claims are made
        has_citations = len(citations) > 0 or len(citation_markers) > 0
        
        return has_citations
    
    def _check_disclaimer(self, response: str) -> bool:
        """Check disclaimer presence."""
        if not self.require_disclaimer:
            return True
        
        response_lower = response.lower()
        
        # Check for disclaimer keywords
        found_keywords = sum(
            1 for keyword in self.DISCLAIMER_KEYWORDS
            if keyword in response_lower
        )
        
        # Need at least 2 disclaimer keywords
        return found_keywords >= 2
    
    def _check_formatting(self, response: str) -> bool:
        """Check response formatting."""
        # Check for basic structure
        has_paragraphs = '\n\n' in response or len(response.split('\n')) > 2
        
        # Check for proper capitalization
        sentences = re.split(r'[.!?]+', response)
        capitalized = sum(
            1 for s in sentences
            if s.strip() and s.strip()[0].isupper()
        )
        
        capitalization_ok = len(sentences) == 0 or capitalized / len(sentences) > 0.8
        
        return has_paragraphs and capitalization_ok
    
    def _check_completeness(self, response: str, query: str) -> bool:
        """Check if response addresses query."""
        # Extract key terms from query
        query_words = set(query.lower().split())
        
        # Remove common words
        common_words = {
            'what', 'how', 'when', 'where', 'why', 'who',
            'is', 'are', 'the', 'a', 'an', 'and', 'or', 'for', 'to'
        }
        
        query_words -= common_words
        
        # Check if key terms appear in response
        response_lower = response.lower()
        
        addressed = sum(1 for word in query_words if word in response_lower)
        
        # At least 50% of key terms should be addressed
        return len(query_words) == 0 or addressed / len(query_words) >= 0.5
    
    def _check_emergency_keywords(self, response: str) -> bool:
        """Check for emergency keywords with proper handling."""
        response_lower = response.lower()
        
        # Find emergency keywords
        found_emergency = any(
            keyword in response_lower
            for keyword in self.EMERGENCY_KEYWORDS
        )
        
        if not found_emergency:
            return True
        
        # If emergency keywords found, check for proper warning
        has_warning = (
            '911' in response or
            'emergency services' in response_lower or
            'immediate medical attention' in response_lower
        )
        
        return has_warning
    
    def _check_diagnosis_treatment(self, response: str) -> bool:
        """Check for inappropriate diagnosis or treatment advice."""
        response_lower = response.lower()
        
        # Problematic phrases
        diagnosis_phrases = [
            'you have',
            'you are diagnosed',
            'this means you have',
            'you should take',
            'i recommend taking',
            'the dose should be',
            'take this medication'
        ]
        
        # Check for problematic phrases
        has_diagnosis = any(
            phrase in response_lower
            for phrase in diagnosis_phrases
        )
        
        # If found, check if properly hedged
        if has_diagnosis:
            hedging = [
                'may', 'might', 'could', 'consult',
                'talk to', 'ask your doctor', 'healthcare provider'
            ]
            
            has_hedging = any(hedge in response_lower for hedge in hedging)
            return has_hedging
        
        return True
    
    def _calculate_score(self, checks: Dict[str, bool]) -> float:
        """
        Calculate validation score.
        
        Args:
            checks: Dictionary of check results
            
        Returns:
            Score (0-1)
        """
        if not checks:
            return 0.0
        
        # Weight different checks
        weights = {
            'length': 0.1,
            'citations': 0.2,
            'disclaimer': 0.2,
            'formatting': 0.1,
            'completeness': 0.2,
            'emergency_handled': 0.1,
            'no_diagnosis': 0.1
        }
        
        score = 0.0
        total_weight = 0.0
        
        for check_name, passed in checks.items():
            weight = weights.get(check_name, 0.1)
            total_weight += weight
            
            if passed:
                score += weight
        
        # Normalize
        if total_weight > 0:
            score /= total_weight
        
        return score
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get validator statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'require_citations': self.require_citations,
            'require_disclaimer': self.require_disclaimer,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'disclaimer_keywords': len(self.DISCLAIMER_KEYWORDS),
            'emergency_keywords': len(self.EMERGENCY_KEYWORDS)
        }
