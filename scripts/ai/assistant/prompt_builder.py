"""
Prompt builder for medical AI assistant.

Dynamically builds prompts based on query type and context.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger
from ai.assistant.medical_prompt_templates import MedicalPromptTemplates, SYSTEM_INSTRUCTION


class PromptBuilder:
    """
    Builds prompts for LLM based on query and context.
    
    Features:
    - Template selection
    - Context injection
    - Conversation history
    - System instructions
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize prompt builder.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Load prompt templates
        self.templates = MedicalPromptTemplates()
        
        # Prompt configuration
        prompt_config = config.get('prompts', {})
        self.default_template = prompt_config.get('default_template', 'medical_qa')
        self.system_instruction = prompt_config.get('system_instruction', SYSTEM_INSTRUCTION)
        
        self.logger.info("PromptBuilder initialized")
    
    def build_prompt(
        self,
        query: str,
        context: str,
        template_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """
        Build complete prompt.
        
        Args:
            query: User query
            context: Retrieved context
            template_name: Template to use (default if None)
            conversation_history: Previous conversation messages
            **kwargs: Additional template variables
            
        Returns:
            Formatted prompt string
        """
        # Select template
        template_name = template_name or self.default_template
        
        # Detect query type for automatic template selection
        if not template_name or template_name == 'medical_qa':
            template_name = self._detect_query_type(query)
        
        try:
            template = self.templates.get_template(template_name)
        except ValueError:
            self.logger.warning(f"Unknown template: {template_name}, using default")
            template = self.templates.get_template('medical_qa')
        
        # Build template variables
        template_vars = {
            'context': context,
            'question': query,
            **kwargs
        }
        
        # Add conversation history if provided
        if conversation_history and template_name == 'conversation_continuation':
            history_text = self._format_conversation_history(conversation_history)
            template_vars['conversation_history'] = history_text
        
        # Format prompt
        try:
            prompt = self._format_with_system_instruction(
                template.format(**template_vars)
            )
        except KeyError as e:
            self.logger.error(f"Missing template variable: {e}")
            # Fallback to basic template
            basic_template = self.templates.get_template('medical_qa')
            prompt = self._format_with_system_instruction(
                basic_template.format(context=context, question=query)
            )
        
        self.logger.debug(f"Built prompt using template: {template_name}")
        
        return prompt
    
    def _detect_query_type(self, query: str) -> str:
        """
        Detect query type from question text.
        
        Args:
            query: User query
            
        Returns:
            Template name
        """
        query_lower = query.lower()
        
        # Disease explanation patterns
        if any(phrase in query_lower for phrase in [
            'what is', 'explain', 'tell me about', 'describe'
        ]):
            # Check if asking about a disease/condition
            if any(term in query_lower for term in [
                'disease', 'condition', 'disorder', 'syndrome',
                'diabetes', 'hypertension', 'cancer', 'infection'
            ]):
                return 'disease_explanation'
        
        # Drug information patterns
        if any(phrase in query_lower for phrase in [
            'drug', 'medication', 'medicine', 'prescription',
            'metformin', 'insulin', 'aspirin', 'antibiotic'
        ]):
            if any(phrase in query_lower for phrase in [
                'what is', 'tell me about', 'information about'
            ]):
                return 'drug_information'
        
        # Clinical guidelines patterns
        if any(phrase in query_lower for phrase in [
            'guideline', 'protocol', 'recommendation', 'standard of care',
            'best practice', 'clinical practice'
        ]):
            return 'clinical_guidelines'
        
        # Medical definition patterns
        if any(phrase in query_lower for phrase in [
            'define', 'definition', 'what does', 'meaning of',
            'what is the term'
        ]):
            return 'medical_definition'
        
        # Research question patterns
        if any(phrase in query_lower for phrase in [
            'research', 'study', 'evidence', 'clinical trial',
            'findings', 'scientific'
        ]):
            return 'research_question'
        
        # Default to medical Q&A
        return 'medical_qa'
    
    def _format_with_system_instruction(self, prompt: str) -> str:
        """
        Add system instruction to prompt.
        
        Args:
            prompt: Base prompt
            
        Returns:
            Prompt with system instruction
        """
        return f"{self.system_instruction}\n\n{prompt}"
    
    def _format_conversation_history(
        self,
        history: List[Dict[str, str]],
        max_messages: int = 5
    ) -> str:
        """
        Format conversation history.
        
        Args:
            history: List of messages
            max_messages: Maximum messages to include
            
        Returns:
            Formatted history string
        """
        lines = []
        
        # Take last N messages
        recent_history = history[-max_messages:] if len(history) > max_messages else history
        
        for msg in recent_history:
            role = msg.get('role', 'user').upper()
            content = msg.get('content', '')
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def estimate_prompt_tokens(self, prompt: str) -> int:
        """
        Estimate token count for prompt.
        
        Args:
            prompt: Prompt text
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(prompt) // 4
    
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validate prompt structure.
        
        Args:
            prompt: Prompt to validate
            
        Returns:
            True if valid
        """
        # Check if prompt contains key sections
        has_context = 'Context' in prompt or 'Document' in prompt
        has_question = 'Question' in prompt or 'question' in prompt.lower()
        has_instruction = 'Instruction' in prompt or 'CRITICAL RULES' in prompt
        
        return has_context and has_question and has_instruction
