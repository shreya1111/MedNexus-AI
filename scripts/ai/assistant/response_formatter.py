"""
Response formatter for medical AI assistant.

Formats responses into structured, user-friendly output.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger
from ai.assistant.citation_manager import Citation


@dataclass
class FormattedResponse:
    """Formatted response structure."""
    
    summary: str
    detailed_explanation: str
    key_points: List[str]
    sources: List[str]
    confidence: float
    disclaimer: str
    raw_text: str


class ResponseFormatter:
    """
    Formats assistant responses for different output formats.
    
    Supports:
    - Markdown (CLI)
    - Plain text
    - Structured JSON
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize response formatter.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Response configuration
        response_config = config.get('response', {})
        self.format_type = response_config.get('format', 'structured')
        self.use_markdown = response_config.get('use_markdown', True)
        self.max_length = response_config.get('max_length', 2000)
        
        self.logger.info("ResponseFormatter initialized")
    
    def format_response(
        self,
        answer: str,
        citations: List[Citation],
        confidence: float,
        context_metadata: Dict[str, Any],
        output_format: str = 'markdown'
    ) -> str:
        """
        Format response for output.
        
        Args:
            answer: Raw answer from LLM
            citations: List of citations
            confidence: Confidence score
            context_metadata: Context metadata
            output_format: Output format (markdown, plain, json)
            
        Returns:
            Formatted response string
        """
        if output_format == 'json':
            return self._format_json(
                answer, citations, confidence, context_metadata
            )
        elif output_format == 'plain':
            return self._format_plain(
                answer, citations, confidence
            )
        else:  # markdown (default)
            return self._format_markdown(
                answer, citations, confidence, context_metadata
            )
    
    def _format_markdown(
        self,
        answer: str,
        citations: List[Citation],
        confidence: float,
        context_metadata: Dict[str, Any]
    ) -> str:
        """Format as markdown."""
        sections = []
        
        # Main answer
        sections.append(f"{answer}\n")
        
        # Confidence indicator
        if confidence >= 0.7:
            confidence_text = "🟢 High Confidence"
        elif confidence >= 0.4:
            confidence_text = "🟡 Medium Confidence"
        else:
            confidence_text = "🔴 Low Confidence"
        
        sections.append(f"\n**Confidence**: {confidence_text} ({confidence:.0%})")
        
        # Sources section
        if citations:
            sections.append("\n## 📚 Sources\n")
            sources = set(c.source for c in citations)
            for source in sorted(sources):
                sections.append(f"- {source}")
        
        # Metadata
        if context_metadata:
            num_docs = context_metadata.get('num_docs', 0)
            sections.append(f"\n*Retrieved from {num_docs} document(s)*")
        
        return "\n".join(sections)
    
    def _format_plain(
        self,
        answer: str,
        citations: List[Citation],
        confidence: float
    ) -> str:
        """Format as plain text."""
        sections = []
        
        # Main answer
        sections.append(answer)
        
        # Confidence
        sections.append(f"\nConfidence: {confidence:.0%}")
        
        # Sources
        if citations:
            sections.append("\nSources:")
            sources = set(c.source for c in citations)
            for source in sorted(sources):
                sections.append(f"  - {source}")
        
        return "\n".join(sections)
    
    def _format_json(
        self,
        answer: str,
        citations: List[Citation],
        confidence: float,
        context_metadata: Dict[str, Any]
    ) -> str:
        """Format as JSON."""
        import json
        
        data = {
            'answer': answer,
            'confidence': confidence,
            'citations': [
                {
                    'source': c.source,
                    'chunk_id': c.chunk_id,
                    'similarity': c.similarity
                }
                for c in citations
            ],
            'metadata': context_metadata
        }
        
        return json.dumps(data, indent=2)
    
    def extract_key_points(self, answer: str) -> List[str]:
        """
        Extract key points from answer.
        
        Args:
            answer: Answer text
            
        Returns:
            List of key points
        """
        key_points = []
        
        # Look for bullet points
        lines = answer.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                point = line.lstrip('•-* ').strip()
                if point:
                    key_points.append(point)
        
        return key_points
    
    def truncate_if_needed(self, text: str, max_length: int = None) -> str:
        """
        Truncate text if too long.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        max_length = max_length or self.max_length
        
        if len(text) <= max_length:
            return text
        
        # Truncate at sentence boundary if possible
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.8:
            return truncated[:last_period + 1] + "\n\n[Response truncated]"
        
        return truncated + "...\n\n[Response truncated]"
    
    def add_disclaimer(
        self,
        response: str,
        disclaimer_type: str = 'medical'
    ) -> str:
        """
        Add medical disclaimer to response.
        
        Args:
            response: Response text
            disclaimer_type: Type of disclaimer
            
        Returns:
            Response with disclaimer
        """
        disclaimers = {
            'medical': (
                "\n\n---\n"
                "**Medical Disclaimer**: This information is for educational purposes only "
                "and should not replace professional medical advice, diagnosis, or treatment. "
                "Always consult a qualified healthcare provider for personalized medical guidance."
            ),
            'emergency': (
                "\n\n---\n"
                "⚠️ **EMERGENCY WARNING**: If this is a medical emergency, please call "
                "emergency services immediately (911 in the US) or go to the nearest emergency room."
            )
        }
        
        disclaimer = disclaimers.get(disclaimer_type, disclaimers['medical'])
        return response + disclaimer
