"""
Safety guardrails for medical AI assistant.

Detects and handles unsafe or inappropriate queries.
"""

import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger


@dataclass
class SafetyCheckResult:
    """Result of safety check."""
    
    is_safe: bool
    category: str
    risk_level: str  # low, medium, high, critical
    message: Optional[str] = None
    recommended_action: Optional[str] = None


class SafetyGuardrails:
    """
    Safety layer for medical AI assistant.
    
    Detects and handles:
    - Emergency situations
    - Self-harm indicators
    - Medication misuse
    - Diagnosis requests
    - Unsafe dosage requests
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize safety guardrails.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Safety configuration
        safety_config = config.get('safety', {})
        self.enabled = safety_config.get('enabled', True)
        self.level = safety_config.get('level', 'strict')
        
        self.detect_emergency = safety_config.get('detect_emergency', True)
        self.detect_self_harm = safety_config.get('detect_self_harm', True)
        self.detect_medication_misuse = safety_config.get('detect_medication_misuse', True)
        self.detect_diagnosis_requests = safety_config.get('detect_diagnosis_requests', True)
        
        # Messages
        self.emergency_message = safety_config.get('emergency_message', '')
        self.disclaimer = safety_config.get('disclaimer', '')
        
        # Patterns
        self._compile_patterns()
        
        self.logger.info(f"SafetyGuardrails initialized (level: {self.level})")
    
    def _compile_patterns(self):
        """Compile detection patterns."""
        
        # Emergency patterns
        self.emergency_patterns = [
            r'\b(chest pain|heart attack|stroke|seizure|unconscious)\b',
            r'\b(severe bleeding|profuse bleeding|heavy bleeding)\b',
            r'\b(can\'?t breathe|difficulty breathing|choking)\b',
            r'\b(overdose|poisoning|poisoned)\b',
            r'\b(severe burn|major injury)\b',
            r'\b(emergency|911|urgent|critical condition)\b',
        ]
        
        # Self-harm patterns
        self.self_harm_patterns = [
            r'\b(kill myself|suicide|end my life|take my life)\b',
            r'\b(hurt myself|self harm|self-harm|cut myself)\b',
            r'\b(don\'?t want to live|want to die)\b',
            r'\b(suicidal|self-destructive)\b',
        ]
        
        # Medication misuse patterns
        self.medication_misuse_patterns = [
            r'\b(how many|how much).*(pills?|tablets?|dose).*(get high|overdose)\b',
            r'\b(abuse|misuse|recreational use).*(drug|medication|medicine)\b',
            r'\b(mix|combine).*(alcohol|drugs).*(medication|medicine)\b',
            r'\b(safe to (take|use)).*(expired|old)\b',
        ]
        
        # Diagnosis request patterns
        self.diagnosis_patterns = [
            r'\b(do I have|am I|could I have).*(disease|condition|disorder|cancer|diabetes)\b',
            r'\b(diagnose me|what\'?s wrong with me|is this)\b',
            r'\b(should I (see|go to)).*(doctor|hospital|emergency)\b',
            r'\b(test results|lab results).*(what does|mean|indicate)\b',
        ]
        
        # Dosage request patterns
        self.dosage_patterns = [
            r'\b(how (much|many)|what dose|dosage).*(should I take|can I take)\b',
            r'\b(safe to (take|increase|decrease|stop)).*(mg|mcg|ml|dose)\b',
            r'\b(can I (double|increase|take more)).*(dose|medication|pills?)\b',
        ]
    
    def check_safety(self, query: str) -> SafetyCheckResult:
        """
        Check if query is safe.
        
        Args:
            query: User query
            
        Returns:
            SafetyCheckResult
        """
        if not self.enabled:
            return SafetyCheckResult(
                is_safe=True,
                category='none',
                risk_level='low'
            )
        
        query_lower = query.lower()
        
        # Check for emergencies (highest priority)
        if self.detect_emergency:
            if self._matches_patterns(query_lower, self.emergency_patterns):
                return SafetyCheckResult(
                    is_safe=False,
                    category='emergency',
                    risk_level='critical',
                    message=self.emergency_message,
                    recommended_action='immediate_professional_help'
                )
        
        # Check for self-harm
        if self.detect_self_harm:
            if self._matches_patterns(query_lower, self.self_harm_patterns):
                return SafetyCheckResult(
                    is_safe=False,
                    category='self_harm',
                    risk_level='critical',
                    message=(
                        "I'm concerned about your safety. Please reach out to:\n"
                        "- National Suicide Prevention Lifeline: 988\n"
                        "- Crisis Text Line: Text HOME to 741741\n"
                        "- Emergency Services: 911\n\n"
                        "You deserve support. Please talk to someone who can help."
                    ),
                    recommended_action='crisis_support'
                )
        
        # Check for medication misuse
        if self.detect_medication_misuse:
            if self._matches_patterns(query_lower, self.medication_misuse_patterns):
                return SafetyCheckResult(
                    is_safe=False,
                    category='medication_misuse',
                    risk_level='high',
                    message=(
                        "I cannot provide information that could lead to medication misuse. "
                        "For safe medication use, please consult a healthcare provider or pharmacist."
                    ),
                    recommended_action='refuse_and_redirect'
                )
        
        # Check for diagnosis requests
        if self.detect_diagnosis_requests:
            if self._matches_patterns(query_lower, self.diagnosis_patterns):
                return SafetyCheckResult(
                    is_safe=True,  # Can answer, but with strong disclaimer
                    category='diagnosis_request',
                    risk_level='medium',
                    message=(
                        "I can provide educational information, but I cannot diagnose conditions. "
                        "For accurate diagnosis, please consult a qualified healthcare professional."
                    ),
                    recommended_action='educational_only'
                )
        
        # Check for dosage requests
        if self._matches_patterns(query_lower, self.dosage_patterns):
            return SafetyCheckResult(
                is_safe=True,  # Can provide general info, but with disclaimer
                category='dosage_request',
                risk_level='medium',
                message=(
                    "I can provide general information, but dosages must be determined by "
                    "a healthcare provider based on individual factors. Never adjust medications "
                    "without professional guidance."
                ),
                recommended_action='general_info_only'
            )
        
        # Query is safe
        return SafetyCheckResult(
            is_safe=True,
            category='safe',
            risk_level='low'
        )
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """
        Check if text matches any pattern.
        
        Args:
            text: Text to check
            patterns: List of regex patterns
            
        Returns:
            True if any pattern matches
        """
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def wrap_response(
        self,
        response: str,
        safety_result: SafetyCheckResult
    ) -> str:
        """
        Wrap response with appropriate disclaimers.
        
        Args:
            response: Original response
            safety_result: Safety check result
            
        Returns:
            Response with disclaimers
        """
        wrapped = response
        
        # Add category-specific disclaimers
        if safety_result.category == 'diagnosis_request':
            wrapped += "\n\n" + "---\n**Important**: This AI cannot provide medical diagnoses. " \
                       "For accurate diagnosis, please consult with a licensed healthcare professional."
        
        elif safety_result.category == 'dosage_request':
            wrapped += "\n\n" + "---\n**Medication Safety**: Dosage must be determined by a healthcare provider. " \
                       "Never adjust medications without professional medical supervision."
        
        # Add general disclaimer
        if self.disclaimer and safety_result.category != 'emergency':
            wrapped += "\n\n" + "---\n" + self.disclaimer
        
        return wrapped
    
    def should_refuse(self, safety_result: SafetyCheckResult) -> bool:
        """
        Determine if query should be refused.
        
        Args:
            safety_result: Safety check result
            
        Returns:
            True if should refuse to answer
        """
        return not safety_result.is_safe and safety_result.risk_level in ['high', 'critical']
    
    def get_refusal_message(self, safety_result: SafetyCheckResult) -> str:
        """
        Get refusal message.
        
        Args:
            safety_result: Safety check result
            
        Returns:
            Refusal message
        """
        if safety_result.message:
            return safety_result.message
        
        return (
            "I'm unable to provide information on this topic as it could be unsafe. "
            "Please consult with a qualified healthcare professional for assistance."
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get safety statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'enabled': self.enabled,
            'level': self.level,
            'checks_enabled': {
                'emergency': self.detect_emergency,
                'self_harm': self.detect_self_harm,
                'medication_misuse': self.detect_medication_misuse,
                'diagnosis_requests': self.detect_diagnosis_requests
            }
        }
