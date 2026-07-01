"""
Medical AI Assistant - Core orchestrator.

Integrates all components into a complete RAG pipeline.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger
from utils.config_loader import load_yaml_config

# Import vector retrieval components
from vector_db.collection_manager import CollectionManager
from vector_db.retriever import VectorRetriever
from vector_db.hybrid_retriever import HybridRetriever
from vector_db.bm25_retriever import BM25Retriever
from vector_db.query_processor import QueryProcessor

# Import embedding components
from embeddings.provider_factory import ProviderFactory

# Import assistant components
from ai.assistant.medical_prompt_templates import MedicalPromptTemplates, get_disclaimer
from ai.assistant.safety_guardrails import SafetyGuardrails, SafetyCheckResult
from ai.assistant.context_builder import ContextBuilder
from ai.assistant.citation_manager import CitationManager, Citation
from ai.assistant.prompt_builder import PromptBuilder
from ai.assistant.response_formatter import ResponseFormatter

# Import Phase 4B components
from ai.assistant.conversation_manager import ConversationManager
from ai.assistant.followup_generator import FollowupGenerator
from ai.assistant.hallucination_checker import HallucinationChecker, HallucinationCheckResult
from ai.assistant.output_validator import OutputValidator, ValidationResult
from ai.assistant.confidence_estimator import ConfidenceEstimator, ConfidenceScore


@dataclass
class AssistantResponse:
    """Assistant response."""
    
    query: str
    answer: str
    citations: List[Citation]
    context_metadata: Dict[str, Any]
    safety_check: SafetyCheckResult
    latency_ms: float
    token_usage: Dict[str, int]
    confidence: float = 0.0
    followup_questions: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert citations to dicts
        data['citations'] = [asdict(c) for c in self.citations]
        data['safety_check'] = asdict(self.safety_check)
        return data


class MedicalAssistant:
    """
    Medical AI Assistant orchestrator.
    
    Integrates:
    - Vector retrieval
    - LLM generation (Gemini)
    - Safety guardrails
    - Citation management
    - Context assembly
    - Response formatting
    """
    
    def __init__(
        self,
        config_path: str = "config/assistant.yaml",
        retrieval_config_path: str = "config/retrieval.yaml",
        embedding_config_path: str = "config/embedding.yaml"
    ):
        """
        Initialize medical assistant.
        
        Args:
            config_path: Path to assistant configuration
            retrieval_config_path: Path to retrieval configuration
            embedding_config_path: Path to embedding configuration
        """
        self.logger = get_logger(__name__)
        
        # Load configurations
        self.config = load_yaml_config(Path(config_path))
        self.retrieval_config = load_yaml_config(Path(retrieval_config_path))
        self.embedding_config = load_yaml_config(Path(embedding_config_path))
        
        # Initialize components
        self._initialize_components()
        
        self.logger.info("MedicalAssistant initialized")
    
    def _initialize_components(self):
        """Initialize all assistant components."""
        
        # Initialize retrieval components
        self.collection_manager = CollectionManager(self.retrieval_config)
        self.collection_manager.get_or_create_collection()
        
        self.query_processor = QueryProcessor(self.retrieval_config)
        
        # Initialize vector retriever
        self.vector_retriever = VectorRetriever(
            self.retrieval_config,
            self.collection_manager
        )
        
        # Initialize embedder for queries
        provider_config = self.embedding_config.get('provider', {})
        active_provider = provider_config.get('active', 'sentence-transformers')
        provider_settings = provider_config.get(active_provider, {})
        
        self.embedder = ProviderFactory.create_embedder(
            active_provider,
            provider_settings
        )
        self.embedder.initialize()
        
        # Initialize assistant components
        self.prompt_templates = MedicalPromptTemplates()
        self.prompt_builder = PromptBuilder(self.config)
        self.safety_guardrails = SafetyGuardrails(self.config)
        self.context_builder = ContextBuilder(self.config)
        self.citation_manager = CitationManager(self.config)
        self.response_formatter = ResponseFormatter(self.config)
        
        # Initialize Phase 4B components
        self.conversation_manager = ConversationManager(self.config)
        self.followup_generator = FollowupGenerator(self.config)
        self.hallucination_checker = HallucinationChecker(self.config)
        self.output_validator = OutputValidator(self.config)
        self.confidence_estimator = ConfidenceEstimator(self.config)
        
        # Initialize LLM (Gemini)
        self._initialize_llm()
        
        self.logger.info("All components initialized")
    
    def _initialize_llm(self):
        """Initialize Gemini LLM."""
        import google.generativeai as genai
        import os
        
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        
        # Get LLM config
        llm_config = self.config.get('llm', {})
        model_name = llm_config.get('model', 'gemini-2.0-flash-exp')
        
        # Generation config
        self.generation_config = {
            'temperature': llm_config.get('temperature', 0.1),
            'top_p': llm_config.get('top_p', 0.95),
            'top_k': llm_config.get('top_k', 40),
            'max_output_tokens': llm_config.get('max_output_tokens', 2048),
        }
        
        # Initialize model
        self.llm = genai.GenerativeModel(
            model_name=model_name,
            generation_config=self.generation_config
        )
        
        self.logger.info(f"Gemini LLM initialized: {model_name}")
    
    def ask(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
        session_id: Optional[str] = None,
        stream: bool = False
    ) -> AssistantResponse:
        """
        Ask a question to the medical assistant.
        
        Args:
            query: User query
            conversation_history: Previous conversation messages
            session_id: Optional session ID for conversation tracking
            stream: Whether to stream response
            
        Returns:
            AssistantResponse
        """
        start_time = time.time()
        
        try:
            # 1. Safety check
            safety_result = self.safety_guardrails.check_safety(query)
            
            if self.safety_guardrails.should_refuse(safety_result):
                # Return refusal message
                refusal_message = self.safety_guardrails.get_refusal_message(safety_result)
                
                return AssistantResponse(
                    query=query,
                    answer=refusal_message,
                    citations=[],
                    context_metadata={},
                    safety_check=safety_result,
                    latency_ms=(time.time() - start_time) * 1000,
                    token_usage={'input': 0, 'output': 0},
                    confidence=0.0
                )
            
            # 2. Process query
            processed_query = self.query_processor.process(query)
            
            # 3. Generate query embedding
            query_embedding = self.embedder.embed_batch([processed_query])[0]
            
            # 4. Retrieve relevant documents
            retrieval_config = self.config.get('retrieval', {})
            top_k = retrieval_config.get('top_k', 5)
            
            retrieved_docs = self.vector_retriever.search(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            # 5. Build context
            context, context_metadata = self.context_builder.build_context(
                retrieved_docs,
                query=query
            )
            
            # 6. Generate citations
            citations = self.citation_manager.generate_citations(retrieved_docs)
            
            # 7. Build prompt using PromptBuilder
            prompt = self.prompt_builder.build_prompt(
                query=query,
                context=context,
                conversation_history=conversation_history
            )
            
            # 8. Generate response
            answer, token_usage = self._generate_response(prompt, stream)
            
            # 9. Add citations to answer
            answer = self.citation_manager.embed_citations(answer, citations)
            
            # 10. Wrap with safety disclaimers
            answer = self.safety_guardrails.wrap_response(answer, safety_result)
            
            # 11. Validate output
            validation_result = self.output_validator.validate_response(
                response=answer,
                citations=citations,
                query=query
            )
            
            # 12. Check for hallucinations
            hallucination_result = self.hallucination_checker.check_response(
                response=answer,
                context=context,
                citations=citations,
                query=query
            )
            
            # 13. Estimate confidence
            confidence_score = self.confidence_estimator.estimate_confidence(
                retrieved_docs=retrieved_docs,
                citations=citations,
                validation_result=validation_result,
                hallucination_result=hallucination_result,
                response_length=len(answer)
            )
            
            # 14. Add low confidence warning if needed
            if self.confidence_estimator.should_warn_low_confidence(confidence_score):
                confidence_msg = self.confidence_estimator.get_confidence_message(confidence_score)
                answer = f"{answer}\n\n{confidence_msg}"
            
            # 15. Generate follow-up questions
            followup_questions = self.followup_generator.generate_followup_questions(
                query=query,
                answer=answer,
                retrieved_docs=retrieved_docs,
                conversation_history=conversation_history
            )
            
            # 16. Update conversation if session provided
            if session_id:
                self.conversation_manager.continue_conversation(
                    session_id=session_id,
                    user_message=query,
                    assistant_response=answer
                )
                
                # Cache context
                self.conversation_manager.cache_context(
                    session_id=session_id,
                    query=query,
                    context=context,
                    retrieved_docs=retrieved_docs
                )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Build response
            response = AssistantResponse(
                query=query,
                answer=answer,
                citations=citations,
                context_metadata=context_metadata,
                safety_check=safety_result,
                latency_ms=latency_ms,
                token_usage=token_usage,
                confidence=confidence_score.overall_score,
                followup_questions=followup_questions
            )
            
            self.logger.info(
                f"Query answered in {latency_ms:.0f}ms "
                f"({token_usage['input']}+{token_usage['output']} tokens)"
            )
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            
            # Return error response
            return AssistantResponse(
                query=query,
                answer=f"I encountered an error processing your question: {str(e)}",
                citations=[],
                context_metadata={},
                safety_check=SafetyCheckResult(
                    is_safe=True,
                    category='error',
                    risk_level='low'
                ),
                latency_ms=(time.time() - start_time) * 1000,
                token_usage={'input': 0, 'output': 0},
                confidence=0.0
            )
    
    def _build_prompt(
        self,
        query: str,
        context: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Build prompt for LLM.
        
        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous messages
            
        Returns:
            Formatted prompt
        """
        # Get prompt template
        template_name = self.config.get('prompts', {}).get('default_template', 'medical_qa')
        template = self.prompt_templates.get_template(template_name)
        
        # Format prompt
        if conversation_history:
            # Use conversation continuation template
            history_text = self._format_conversation_history(conversation_history)
            prompt = template.format(
                conversation_history=history_text,
                context=context,
                question=query
            )
        else:
            # Use standard template
            prompt = template.format(
                context=context,
                question=query
            )
        
        return prompt
    
    def _format_conversation_history(
        self,
        history: List[Dict[str, str]]
    ) -> str:
        """Format conversation history."""
        lines = []
        for msg in history[-5:]:  # Last 5 messages
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            lines.append(f"{role.upper()}: {content}")
        
        return "\n".join(lines)
    
    def _generate_response(
        self,
        prompt: str,
        stream: bool = False
    ) -> tuple[str, Dict[str, int]]:
        """
        Generate response using LLM.
        
        Args:
            prompt: Formatted prompt
            stream: Whether to stream
            
        Returns:
            Tuple of (response_text, token_usage)
        """
        try:
            # Generate response
            response = self.llm.generate_content(prompt)
            
            # Extract text
            answer = response.text
            
            # Extract token usage
            token_usage = {
                'input': getattr(response.usage_metadata, 'prompt_token_count', 0),
                'output': getattr(response.usage_metadata, 'candidates_token_count', 0),
                'total': getattr(response.usage_metadata, 'total_token_count', 0)
            }
            
            return answer, token_usage
        
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return f"I encountered an error generating a response: {str(e)}", {'input': 0, 'output': 0, 'total': 0}
    
    def _calculate_confidence(
        self,
        context_metadata: Dict[str, Any],
        citations: List[Citation]
    ) -> float:
        """
        Calculate confidence score.
        
        Args:
            context_metadata: Context metadata
            citations: Citations
            
        Returns:
            Confidence score (0-1)
        """
        if not citations:
            return 0.0
        
        # Based on average similarity and number of sources
        avg_similarity = sum(c.similarity for c in citations) / len(citations)
        num_sources = len(set(c.source for c in citations))
        
        # Weight by coverage
        confidence = avg_similarity * 0.7 + min(num_sources / 3, 1.0) * 0.3
        
        return confidence
    
    def start_conversation(self, session_id: Optional[str] = None) -> str:
        """
        Start a new conversation.
        
        Args:
            session_id: Optional session ID
            
        Returns:
            Session ID
        """
        return self.conversation_manager.start_conversation(session_id)
    
    def get_conversation_history(
        self,
        session_id: str,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Args:
            session_id: Session ID
            max_messages: Maximum messages
            
        Returns:
            Conversation history
        """
        return self.conversation_manager.get_conversation_history(session_id, max_messages)
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history."""
        self.conversation_manager.clear_conversation(session_id)
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all active conversations."""
        return self.conversation_manager.list_conversations()
    
    def cleanup(self):
        """Cleanup resources."""
        if self.embedder:
            self.embedder.cleanup()
        
        # Cleanup expired sessions
        self.conversation_manager.cleanup_expired_sessions()
        
        self.logger.info("Assistant cleanup complete")
