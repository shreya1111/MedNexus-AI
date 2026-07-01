"""
Unit tests for Phase 4B conversation components.

Tests:
- MemoryManager
- SessionManager
- ConversationManager
- FollowupGenerator
- HallucinationChecker
- OutputValidator
- ConfidenceEstimator
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

sys.path.append(str(Path(__file__).parent.parent))

from ai.assistant.memory_manager import MemoryManager
from ai.assistant.session_manager import SessionManager
from ai.assistant.conversation_manager import ConversationManager
from ai.assistant.followup_generator import FollowupGenerator
from ai.assistant.hallucination_checker import HallucinationChecker, HallucinationCheckResult
from ai.assistant.output_validator import OutputValidator, ValidationResult
from ai.assistant.confidence_estimator import ConfidenceEstimator, ConfidenceLevel


class TestMemoryManager(unittest.TestCase):
    """Test MemoryManager."""
    
    def setUp(self):
        """Setup test configuration."""
        self.config = {
            'memory': {
                'type': 'conversation_buffer_window',
                'window_size': 5,
                'cache_retrieved_context': True,
                'context_cache_size': 10
            }
        }
        self.manager = MemoryManager(self.config)
    
    def test_initialization(self):
        """Test memory manager initialization."""
        self.assertEqual(self.manager.window_size, 5)
        self.assertEqual(len(self.manager.messages), 0)
    
    def test_add_message(self):
        """Test adding messages."""
        self.manager.add_message('user', 'Hello')
        self.manager.add_message('assistant', 'Hi there')
        
        self.assertEqual(len(self.manager.messages), 2)
    
    def test_window_size_limit(self):
        """Test sliding window enforcement."""
        for i in range(10):
            self.manager.add_message('user', f'Message {i}')
        
        # Should only keep last 5
        self.assertEqual(len(self.manager.messages), 5)
    
    def test_get_recent_messages(self):
        """Test retrieving recent messages."""
        for i in range(3):
            self.manager.add_message('user', f'Message {i}')
        
        recent = self.manager.get_recent_messages(2)
        self.assertEqual(len(recent), 2)
    
    def test_format_for_prompt(self):
        """Test formatting for prompt."""
        self.manager.add_message('user', 'Question 1')
        self.manager.add_message('assistant', 'Answer 1')
        
        formatted = self.manager.format_for_prompt(max_messages=2)
        
        self.assertIn('USER:', formatted)
        self.assertIn('ASSISTANT:', formatted)
    
    def test_cache_context(self):
        """Test context caching."""
        self.manager.cache_context(
            query='test query',
            context='test context',
            retrieved_docs=[]
        )
        
        self.assertEqual(len(self.manager.context_cache), 1)
    
    def test_clear(self):
        """Test clearing memory."""
        self.manager.add_message('user', 'Test')
        self.manager.clear()
        
        self.assertEqual(len(self.manager.messages), 0)


class TestSessionManager(unittest.TestCase):
    """Test SessionManager."""
    
    def setUp(self):
        """Setup test configuration."""
        self.config = {
            'memory': {
                'type': 'conversation_buffer_window',
                'window_size': 10,
                'session_timeout': 3600,
                'persist_sessions': False,  # Disable for tests
                'session_storage': 'test_storage/sessions'
            }
        }
        self.manager = SessionManager(self.config)
    
    def test_create_session(self):
        """Test session creation."""
        session_id = self.manager.create_session()
        
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.manager.sessions)
    
    def test_get_session(self):
        """Test getting session."""
        session_id = self.manager.create_session()
        session = self.manager.get_session(session_id)
        
        self.assertIsNotNone(session)
        self.assertEqual(session['id'], session_id)
    
    def test_delete_session(self):
        """Test deleting session."""
        session_id = self.manager.create_session()
        self.manager.delete_session(session_id)
        
        session = self.manager.get_session(session_id, create_if_missing=False)
        self.assertIsNone(session)
    
    def test_list_sessions(self):
        """Test listing sessions."""
        for i in range(3):
            self.manager.create_session()
        
        sessions = self.manager.list_sessions()
        self.assertEqual(len(sessions), 3)


class TestConversationManager(unittest.TestCase):
    """Test ConversationManager."""
    
    def setUp(self):
        """Setup test configuration."""
        self.config = {
            'memory': {
                'type': 'conversation_buffer_window',
                'window_size': 10,
                'session_timeout': 3600,
                'persist_sessions': False
            }
        }
        self.manager = ConversationManager(self.config)
    
    def test_start_conversation(self):
        """Test starting conversation."""
        session_id = self.manager.start_conversation()
        
        self.assertIsNotNone(session_id)
    
    def test_continue_conversation(self):
        """Test continuing conversation."""
        session_id = self.manager.start_conversation()
        
        self.manager.continue_conversation(
            session_id=session_id,
            user_message='Hello',
            assistant_response='Hi there'
        )
        
        history = self.manager.get_conversation_history(session_id)
        self.assertEqual(len(history), 2)
    
    def test_get_context_for_prompt(self):
        """Test getting context for prompt."""
        session_id = self.manager.start_conversation()
        
        self.manager.continue_conversation(
            session_id=session_id,
            user_message='Question',
            assistant_response='Answer'
        )
        
        context = self.manager.get_context_for_prompt(session_id)
        self.assertIn('USER:', context)
    
    def test_clear_conversation(self):
        """Test clearing conversation."""
        session_id = self.manager.start_conversation()
        
        self.manager.continue_conversation(
            session_id=session_id,
            user_message='Test',
            assistant_response='Response'
        )
        
        self.manager.clear_conversation(session_id)
        
        history = self.manager.get_conversation_history(session_id)
        self.assertEqual(len(history), 0)


class TestFollowupGenerator(unittest.TestCase):
    """Test FollowupGenerator."""
    
    def setUp(self):
        """Setup test configuration."""
        self.config = {
            'followup': {
                'enabled': True,
                'max_questions': 3,
                'categories': ['treatment', 'symptoms', 'prevention']
            }
        }
        self.generator = FollowupGenerator(self.config)
    
    def test_initialization(self):
        """Test generator initialization."""
        self.assertTrue(self.generator.enabled)
        self.assertEqual(self.generator.max_questions, 3)
    
    def test_generate_followup_questions(self):
        """Test generating follow-up questions."""
        questions = self.generator.generate_followup_questions(
            query='What is diabetes?',
            answer='Diabetes is a chronic condition...',
            retrieved_docs=[],
            conversation_history=[]
        )
        
        self.assertIsInstance(questions, list)
        self.assertLessEqual(len(questions), 3)
    
    def test_extract_topic(self):
        """Test topic extraction."""
        topic = self.generator._extract_topic('What is diabetes?')
        
        self.assertIn('diabetes', topic.lower())


class TestHallucinationChecker(unittest.TestCase):
    """Test HallucinationChecker."""
    
    def setUp(self):
        """Setup test configuration."""
        self.config = {
            'hallucination': {
                'enabled': True,
                'verify_context_usage': True,
                'verify_citations': True,
                'detect_unsupported_claims': True,
                'min_confidence': 0.3
            }
        }
        self.checker = HallucinationChecker(self.config)
    
    def test_initialization(self):
        """Test checker initialization."""
        self.assertTrue(self.checker.enabled)
    
    def test_check_response(self):
        """Test checking response."""
        result = self.checker.check_response(
            response='Diabetes is a condition that affects blood sugar.',
            context='Diabetes is a chronic disease characterized by high blood sugar levels.',
            citations=[Mock(source='test')],
            query='What is diabetes?'
        )
        
        self.assertIsInstance(result, HallucinationCheckResult)
        self.assertTrue(result.is_grounded)
    
    def test_context_coverage(self):
        """Test context coverage calculation."""
        coverage = self.checker._calculate_context_coverage(
            response='diabetes blood sugar levels',
            context='diabetes is a disease characterized by high blood sugar levels'
        )
        
        self.assertGreater(coverage, 0.5)


class TestOutputValidator(unittest.TestCase):
    """Test OutputValidator."""
    
    def setUp(self):
        """Setup test configuration."""
        self.config = {
            'citations': {
                'enabled': True
            },
            'safety': {
                'enabled': True
            },
            'response': {
                'min_length': 50,
                'max_output_tokens': 2000
            }
        }
        self.validator = OutputValidator(self.config)
    
    def test_initialization(self):
        """Test validator initialization."""
        self.assertTrue(self.validator.require_citations)
    
    def test_validate_response(self):
        """Test validating response."""
        response = """
        Diabetes is a chronic condition that affects how your body processes blood sugar.
        This information is for educational purposes only and should not replace professional 
        medical advice. Please consult a healthcare provider.
        """
        
        result = self.validator.validate_response(
            response=response,
            citations=[Mock()],
            query='What is diabetes?'
        )
        
        self.assertIsInstance(result, ValidationResult)
        self.assertGreater(result.score, 0.0)


class TestConfidenceEstimator(unittest.TestCase):
    """Test ConfidenceEstimator."""
    
    def setUp(self):
        """Setup test configuration."""
        self.config = {
            'hallucination': {
                'min_confidence': 0.3,
                'low_confidence_threshold': 0.5
            }
        }
        self.estimator = ConfidenceEstimator(self.config)
    
    def test_initialization(self):
        """Test estimator initialization."""
        self.assertEqual(self.estimator.min_confidence, 0.3)
    
    def test_estimate_confidence(self):
        """Test confidence estimation."""
        retrieved_docs = [
            {'similarity': 0.8, 'document': 'test content'},
            {'similarity': 0.7, 'document': 'more content'}
        ]
        
        citations = [Mock(source='test')]
        
        result = self.estimator.estimate_confidence(
            retrieved_docs=retrieved_docs,
            citations=citations,
            validation_result=Mock(score=0.8),
            hallucination_result=Mock(confidence=0.7),
            response_length=500
        )
        
        self.assertIsNotNone(result)
        self.assertIn(result.level, [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW])
        self.assertGreaterEqual(result.overall_score, 0.0)
        self.assertLessEqual(result.overall_score, 1.0)
    
    def test_should_warn_low_confidence(self):
        """Test low confidence warning."""
        low_confidence = Mock(level=ConfidenceLevel.LOW, overall_score=0.3)
        
        should_warn = self.estimator.should_warn_low_confidence(low_confidence)
        
        self.assertTrue(should_warn)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConversationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestFollowupGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestHallucinationChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestConfidenceEstimator))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
