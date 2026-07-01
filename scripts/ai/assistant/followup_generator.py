"""
Follow-up question generator.

Generates intelligent follow-up questions based on context and conversation.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger


class FollowupGenerator:
    """
    Generates intelligent follow-up questions.
    
    Features:
    - Context-aware question generation
    - Category-based questions
    - Conversation history analysis
    - Relevance scoring
    """
    
    # Question templates by category
    QUESTION_TEMPLATES = {
        'treatment': [
            "What are the treatment options for {topic}?",
            "How is {topic} typically treated?",
            "What medications are used for {topic}?",
            "Are there alternative treatments for {topic}?",
        ],
        'symptoms': [
            "What are the common symptoms of {topic}?",
            "How do symptoms of {topic} typically progress?",
            "What are early warning signs of {topic}?",
            "What symptoms should prompt immediate medical attention?",
        ],
        'prevention': [
            "How can {topic} be prevented?",
            "What lifestyle changes help prevent {topic}?",
            "Are there screening recommendations for {topic}?",
            "What preventive measures are recommended for {topic}?",
        ],
        'causes': [
            "What causes {topic}?",
            "What are the risk factors for {topic}?",
            "Is {topic} hereditary?",
            "What triggers {topic}?",
        ],
        'diagnosis': [
            "How is {topic} diagnosed?",
            "What tests are used to detect {topic}?",
            "What are the diagnostic criteria for {topic}?",
            "When should someone be screened for {topic}?",
        ],
        'complications': [
            "What are potential complications of {topic}?",
            "What are the long-term effects of {topic}?",
            "Can {topic} lead to other health conditions?",
            "What complications should be monitored?",
        ],
        'management': [
            "How is {topic} managed long-term?",
            "What follow-up care is needed for {topic}?",
            "How can symptoms of {topic} be managed?",
            "What lifestyle modifications help with {topic}?",
        ],
        'prognosis': [
            "What is the prognosis for {topic}?",
            "Can {topic} be cured?",
            "What is the typical course of {topic}?",
            "What factors affect outcomes for {topic}?",
        ],
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize followup generator.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Followup configuration
        followup_config = config.get('followup', {})
        self.enabled = followup_config.get('enabled', True)
        self.max_questions = followup_config.get('max_questions', 3)
        self.categories = followup_config.get('categories', [
            'treatment', 'symptoms', 'prevention', 'causes', 'diagnosis'
        ])
        
        self.logger.info(
            f"FollowupGenerator initialized: max={self.max_questions}, "
            f"categories={len(self.categories)}"
        )
    
    def generate_followup_questions(
        self,
        query: str,
        answer: str,
        retrieved_docs: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        categories: Optional[List[str]] = None
    ) -> List[str]:
        """
        Generate follow-up questions.
        
        Args:
            query: Original query
            answer: Assistant's answer
            retrieved_docs: Retrieved documents
            conversation_history: Previous conversation
            categories: Specific categories to generate for
            
        Returns:
            List of follow-up questions
        """
        if not self.enabled:
            return []
        
        try:
            # Extract topic from query
            topic = self._extract_topic(query)
            
            # Determine categories to use
            categories = categories or self.categories
            
            # Identify what has already been discussed
            discussed = self._get_discussed_aspects(
                query,
                answer,
                conversation_history
            )
            
            # Generate questions for each category
            questions = []
            
            for category in categories:
                if category in discussed:
                    continue
                
                if category in self.QUESTION_TEMPLATES:
                    # Get template for category
                    templates = self.QUESTION_TEMPLATES[category]
                    
                    # Pick first template
                    template = templates[0]
                    
                    # Format with topic
                    question = template.format(topic=topic)
                    
                    questions.append(question)
                    
                    # Stop if we have enough
                    if len(questions) >= self.max_questions:
                        break
            
            self.logger.debug(f"Generated {len(questions)} follow-up questions")
            
            return questions[:self.max_questions]
        
        except Exception as e:
            self.logger.error(f"Failed to generate follow-up questions: {e}")
            return []
    
    def _extract_topic(self, query: str) -> str:
        """
        Extract main topic from query.
        
        Args:
            query: User query
            
        Returns:
            Extracted topic
        """
        # Simple extraction: remove question words
        topic = query.lower()
        
        question_words = [
            'what', 'how', 'when', 'where', 'why', 'who',
            'is', 'are', 'can', 'could', 'should', 'would',
            'do', 'does', 'did', 'the', 'a', 'an'
        ]
        
        for word in question_words:
            topic = topic.replace(f"{word} ", "")
            topic = topic.replace(f" {word}", "")
        
        # Remove punctuation
        topic = topic.strip('?.,!;:')
        
        return topic.strip() or "this condition"
    
    def _get_discussed_aspects(
        self,
        query: str,
        answer: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[str]:
        """
        Identify aspects already discussed.
        
        Args:
            query: Current query
            answer: Current answer
            conversation_history: Previous conversation
            
        Returns:
            List of discussed categories
        """
        discussed = []
        
        # Combine all text
        text = (query + " " + answer).lower()
        
        if conversation_history:
            for msg in conversation_history:
                text += " " + msg.get('content', '').lower()
        
        # Check for keywords indicating each category
        category_keywords = {
            'treatment': ['treatment', 'treat', 'therapy', 'medication', 'drug', 'surgery'],
            'symptoms': ['symptom', 'sign', 'manifestation', 'presentation'],
            'prevention': ['prevent', 'prevention', 'avoid', 'reduce risk'],
            'causes': ['cause', 'caused by', 'due to', 'reason', 'etiology'],
            'diagnosis': ['diagnose', 'diagnosis', 'test', 'screening', 'detect'],
            'complications': ['complication', 'adverse', 'side effect', 'risk'],
            'management': ['manage', 'management', 'follow-up', 'monitoring'],
            'prognosis': ['prognosis', 'outcome', 'survival', 'cure', 'recovery'],
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    discussed.append(category)
                    break
        
        return discussed
    
    def generate_contextual_questions(
        self,
        retrieved_docs: List[Dict[str, Any]],
        max_questions: int = 3
    ) -> List[str]:
        """
        Generate questions based on retrieved context.
        
        Args:
            retrieved_docs: Retrieved documents
            max_questions: Maximum questions to generate
            
        Returns:
            List of questions
        """
        questions = []
        
        try:
            # Analyze retrieved documents for topics
            for doc in retrieved_docs[:max_questions]:
                content = doc.get('document', '')
                metadata = doc.get('metadata', {})
                
                # Extract section or topic
                section = metadata.get('section', '')
                
                if section and section not in ['summary', 'introduction']:
                    # Generate question about this section
                    question = f"Tell me more about {section.lower()}"
                    questions.append(question)
            
            return questions[:max_questions]
        
        except Exception as e:
            self.logger.error(f"Failed to generate contextual questions: {e}")
            return []
    
    def rank_questions(
        self,
        questions: List[str],
        query: str,
        answer: str
    ) -> List[str]:
        """
        Rank questions by relevance.
        
        Args:
            questions: List of questions
            query: Original query
            answer: Assistant's answer
            
        Returns:
            Ranked questions
        """
        # Simple ranking: prefer shorter, more specific questions
        scored = []
        
        for question in questions:
            score = 0
            
            # Prefer shorter questions
            score -= len(question) * 0.01
            
            # Prefer questions with specific medical terms
            medical_terms = [
                'treatment', 'symptom', 'diagnosis', 'prevention',
                'medication', 'disease', 'condition'
            ]
            
            for term in medical_terms:
                if term in question.lower():
                    score += 1
            
            scored.append((score, question))
        
        # Sort by score (descending)
        scored.sort(reverse=True, key=lambda x: x[0])
        
        return [q for _, q in scored]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get generator statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'enabled': self.enabled,
            'max_questions': self.max_questions,
            'categories': self.categories,
            'total_templates': sum(
                len(templates)
                for templates in self.QUESTION_TEMPLATES.values()
            )
        }
