"""
Unit tests for medical AI assistant.

Tests prompt building, context assembly, citations, safety, and response formatting.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from ai.assistant.prompt_builder import PromptBuilder
from ai.assistant.context_builder import ContextBuilder
from ai.assistant.citation_manager import CitationManager, Citation
from ai.assistant.safety_guardrails import SafetyGuardrails, SafetyCheckResult
from ai.assistant.response_formatter import ResponseFormatter


class TestPromptBuilder:
    """Tests for PromptBuilder."""
    
    def test_initialization(self):
        """Test prompt builder initialization."""
        config = {
            'prompts': {
                'default_template': 'medical_qa',
                'system_instruction': 'Test instruction'
            }
        }
        
        builder = PromptBuilder(config)
        
        assert builder.default_template == 'medical_qa'
        assert 'Test instruction' in builder.system_instruction
    
    def test_build_basic_prompt(self):
        """Test building basic prompt."""
        config = {'prompts': {}}
        builder = PromptBuilder(config)
        
        prompt = builder.build_prompt(
            query="What causes diabetes?",
            context="Diabetes is caused by..."
        )
        
        assert "What causes diabetes?" in prompt
        assert "Diabetes is caused by..." in prompt
        assert "Context" in prompt or "Document" in prompt
    
    def test_detect_disease_explanation(self):
        """Test automatic detection of disease explanation queries."""
        config = {'prompts': {}}
        builder = PromptBuilder(config)
        
        template_name = builder._detect_query_type("What is diabetes?")
        
        assert template_name == 'disease_explanation'
    
    def test_detect_drug_information(self):
        """Test automatic detection of drug information queries."""
        config = {'prompts': {}}
        builder = PromptBuilder(config)
        
        template_name = builder._detect_query_type("Tell me about metformin")
        
        assert template_name == 'drug_information'
    
    def test_detect_clinical_guidelines(self):
        """Test automatic detection of clinical guideline queries."""
        config = {'prompts': {}}
        builder = PromptBuilder(config)
        
        template_name = builder._detect_query_type("What are the guidelines for diabetes management?")
        
        assert template_name == 'clinical_guidelines'
    
    def test_estimate_prompt_tokens(self):
        """Test token estimation."""
        config = {'prompts': {}}
        builder = PromptBuilder(config)
        
        prompt = "This is a test prompt" * 100
        tokens = builder.estimate_prompt_tokens(prompt)
        
        assert tokens > 0
        assert tokens < len(prompt)  # Should be less than character count


class TestContextBuilder:
    """Tests for ContextBuilder."""
    
    def test_initialization(self):
        """Test context builder initialization."""
        config = {
            'context': {
                'max_tokens': 4000,
                'deduplicate': True,
                'sort_by_relevance': True
            }
        }
        
        builder = ContextBuilder(config)
        
        assert builder.max_tokens == 4000
        assert builder.deduplicate
        assert builder.sort_by_relevance
    
    def test_build_context(self):
        """Test context building."""
        config = {'context': {}}
        builder = ContextBuilder(config)
        
        docs = [
            {
                'chunk_id': 'doc1',
                'document': 'Diabetes is a disease.',
                'metadata': {'source': 'medquad'},
                'similarity': 0.9
            },
            {
                'chunk_id': 'doc2',
                'document': 'Hypertension is high blood pressure.',
                'metadata': {'source': 'medquad'},
                'similarity': 0.8
            }
        ]
        
        context, metadata = builder.build_context(docs)
        
        assert 'Diabetes' in context
        assert 'Hypertension' in context
        assert metadata['num_docs'] == 2
    
    def test_deduplicate_documents(self):
        """Test document deduplication."""
        config = {'context': {'deduplicate': True}}
        builder = ContextBuilder(config)
        
        docs = [
            {'chunk_id': 'doc1', 'document': 'Same content'},
            {'chunk_id': 'doc1', 'document': 'Same content'},  # Duplicate ID
            {'chunk_id': 'doc2', 'document': 'Different content'}
        ]
        
        unique = builder._deduplicate_documents(docs)
        
        assert len(unique) == 2
    
    def test_sort_by_relevance(self):
        """Test sorting by relevance score."""
        config = {'context': {}}
        builder = ContextBuilder(config)
        
        docs = [
            {'chunk_id': 'doc1', 'similarity': 0.5},
            {'chunk_id': 'doc2', 'similarity': 0.9},
            {'chunk_id': 'doc3', 'similarity': 0.7}
        ]
        
        sorted_docs = builder._sort_by_relevance(docs)
        
        assert sorted_docs[0]['similarity'] == 0.9
        assert sorted_docs[2]['similarity'] == 0.5


class TestCitationManager:
    """Tests for CitationManager."""
    
    def test_initialization(self):
        """Test citation manager initialization."""
        config = {
            'citations': {
                'enabled': True,
                'format': 'inline'
            }
        }
        
        manager = CitationManager(config)
        
        assert manager.enabled
        assert manager.format == 'inline'
    
    def test_generate_citations(self):
        """Test citation generation."""
        config = {'citations': {}}
        manager = CitationManager(config)
        
        docs = [
            {
                'chunk_id': 'chunk1',
                'metadata': {
                    'source': 'medquad',
                    'document_id': 'doc1',
                    'section': 'symptoms'
                },
                'similarity': 0.9
            }
        ]
        
        citations = manager.generate_citations(docs)
        
        assert len(citations) == 1
        assert citations[0].source == 'medquad'
        assert citations[0].similarity == 0.9
    
    def test_format_inline_citation(self):
        """Test inline citation formatting."""
        config = {'citations': {'format': 'inline'}}
        manager = CitationManager(config)
        
        citation = Citation(
            chunk_id='chunk1',
            source='MedQuAD',
            document_id='doc1',
            section='symptoms'
        )
        
        formatted = manager.format_citation(citation)
        
        assert 'MedQuAD' in formatted
        assert '[' in formatted and ']' in formatted
    
    def test_extract_source_list(self):
        """Test source list extraction."""
        config = {'citations': {}}
        manager = CitationManager(config)
        
        citations = [
            Citation('c1', 'Source A', 'd1'),
            Citation('c2', 'Source B', 'd2'),
            Citation('c3', 'Source A', 'd3')
        ]
        
        sources = manager.extract_source_list(citations)
        
        assert len(sources) == 2
        assert 'Source A' in sources
        assert 'Source B' in sources


class TestSafetyGuardrails:
    """Tests for SafetyGuardrails."""
    
    def test_initialization(self):
        """Test safety guardrails initialization."""
        config = {
            'safety': {
                'enabled': True,
                'level': 'strict',
                'detect_emergency': True
            }
        }
        
        guardrails = SafetyGuardrails(config)
        
        assert guardrails.enabled
        assert guardrails.level == 'strict'
        assert guardrails.detect_emergency
    
    def test_detect_emergency(self):
        """Test emergency detection."""
        config = {
            'safety': {
                'enabled': True,
                'detect_emergency': True,
                'emergency_message': 'Call 911'
            }
        }
        
        guardrails = SafetyGuardrails(config)
        
        result = guardrails.check_safety("I'm having chest pain")
        
        assert not result.is_safe
        assert result.category == 'emergency'
        assert result.risk_level == 'critical'
    
    def test_detect_self_harm(self):
        """Test self-harm detection."""
        config = {
            'safety': {
                'enabled': True,
                'detect_self_harm': True
            }
        }
        
        guardrails = SafetyGuardrails(config)
        
        result = guardrails.check_safety("I want to hurt myself")
        
        assert not result.is_safe
        assert result.category == 'self_harm'
        assert result.risk_level == 'critical'
    
    def test_detect_medication_misuse(self):
        """Test medication misuse detection."""
        config = {
            'safety': {
                'enabled': True,
                'detect_medication_misuse': True
            }
        }
        
        guardrails = SafetyGuardrails(config)
        
        result = guardrails.check_safety("How many pills to get high?")
        
        assert not result.is_safe
        assert result.category == 'medication_misuse'
    
    def test_detect_diagnosis_request(self):
        """Test diagnosis request detection."""
        config = {
            'safety': {
                'enabled': True,
                'detect_diagnosis_requests': True
            }
        }
        
        guardrails = SafetyGuardrails(config)
        
        result = guardrails.check_safety("Do I have diabetes?")
        
        assert result.is_safe  # Can answer with disclaimer
        assert result.category == 'diagnosis_request'
        assert result.risk_level == 'medium'
    
    def test_safe_query(self):
        """Test safe query."""
        config = {'safety': {'enabled': True}}
        guardrails = SafetyGuardrails(config)
        
        result = guardrails.check_safety("What are the symptoms of diabetes?")
        
        assert result.is_safe
        assert result.category == 'safe'
        assert result.risk_level == 'low'
    
    def test_should_refuse(self):
        """Test refusal logic."""
        config = {'safety': {}}
        guardrails = SafetyGuardrails(config)
        
        # High risk should be refused
        high_risk = SafetyCheckResult(
            is_safe=False,
            category='emergency',
            risk_level='high'
        )
        assert guardrails.should_refuse(high_risk)
        
        # Low risk should not be refused
        low_risk = SafetyCheckResult(
            is_safe=True,
            category='safe',
            risk_level='low'
        )
        assert not guardrails.should_refuse(low_risk)


class TestResponseFormatter:
    """Tests for ResponseFormatter."""
    
    def test_initialization(self):
        """Test response formatter initialization."""
        config = {
            'response': {
                'format': 'structured',
                'use_markdown': True
            }
        }
        
        formatter = ResponseFormatter(config)
        
        assert formatter.format_type == 'structured'
        assert formatter.use_markdown
    
    def test_format_markdown(self):
        """Test markdown formatting."""
        config = {'response': {'use_markdown': True}}
        formatter = ResponseFormatter(config)
        
        citations = [
            Citation('c1', 'MedQuAD', 'd1', similarity=0.9)
        ]
        
        formatted = formatter.format_response(
            answer="Diabetes is a disease.",
            citations=citations,
            confidence=0.8,
            context_metadata={'num_docs': 1},
            output_format='markdown'
        )
        
        assert 'Diabetes is a disease' in formatted
        assert 'Confidence' in formatted or 'confidence' in formatted
        assert 'Sources' in formatted or 'MedQuAD' in formatted
    
    def test_format_plain(self):
        """Test plain text formatting."""
        config = {'response': {}}
        formatter = ResponseFormatter(config)
        
        formatted = formatter.format_response(
            answer="Test answer",
            citations=[],
            confidence=0.7,
            context_metadata={},
            output_format='plain'
        )
        
        assert 'Test answer' in formatted
        assert isinstance(formatted, str)
    
    def test_truncate_if_needed(self):
        """Test text truncation."""
        config = {'response': {'max_length': 100}}
        formatter = ResponseFormatter(config)
        
        long_text = "This is a test. " * 50
        truncated = formatter.truncate_if_needed(long_text)
        
        assert len(truncated) <= len(long_text)
        if len(truncated) < len(long_text):
            assert 'truncated' in truncated.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
