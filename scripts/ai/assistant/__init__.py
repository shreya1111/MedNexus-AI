"""
Medical AI Assistant module.

Provides RAG-based medical question answering with conversation capabilities.
"""

# Phase 4A: Core RAG Components
from ai.assistant.medical_assistant import MedicalAssistant, AssistantResponse
from ai.assistant.prompt_builder import PromptBuilder
from ai.assistant.context_builder import ContextBuilder
from ai.assistant.citation_manager import CitationManager, Citation
from ai.assistant.safety_guardrails import SafetyGuardrails, SafetyCheckResult
from ai.assistant.response_formatter import ResponseFormatter, FormattedResponse
from ai.assistant.medical_prompt_templates import MedicalPromptTemplates

# Phase 4B: Conversation & Reasoning Components
from ai.assistant.memory_manager import MemoryManager
from ai.assistant.session_manager import SessionManager
from ai.assistant.conversation_manager import ConversationManager
from ai.assistant.followup_generator import FollowupGenerator
from ai.assistant.hallucination_checker import HallucinationChecker, HallucinationCheckResult
from ai.assistant.output_validator import OutputValidator, ValidationResult
from ai.assistant.confidence_estimator import ConfidenceEstimator, ConfidenceScore, ConfidenceLevel


__all__ = [
    # Phase 4A
    'MedicalAssistant',
    'AssistantResponse',
    'PromptBuilder',
    'ContextBuilder',
    'CitationManager',
    'Citation',
    'SafetyGuardrails',
    'SafetyCheckResult',
    'ResponseFormatter',
    'FormattedResponse',
    'MedicalPromptTemplates',
    # Phase 4B
    'MemoryManager',
    'SessionManager',
    'ConversationManager',
    'FollowupGenerator',
    'HallucinationChecker',
    'HallucinationCheckResult',
    'OutputValidator',
    'ValidationResult',
    'ConfidenceEstimator',
    'ConfidenceScore',
    'ConfidenceLevel',
]
