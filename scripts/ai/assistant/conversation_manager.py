"""
Conversation manager for multi-turn conversations.

Orchestrates memory, sessions, and conversation flow.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger
from ai.assistant.memory_manager import MemoryManager
from ai.assistant.session_manager import SessionManager


class ConversationManager:
    """
    Manages multi-turn conversations.
    
    Features:
    - Session management
    - Memory orchestration
    - Context assembly for prompts
    - Conversation history tracking
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize conversation manager.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize session manager
        self.session_manager = SessionManager(config)
        
        self.logger.info("ConversationManager initialized")
    
    def start_conversation(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new conversation.
        
        Args:
            session_id: Optional session ID
            metadata: Optional session metadata
            
        Returns:
            Session ID
        """
        session_id = self.session_manager.create_session(
            session_id=session_id,
            metadata=metadata
        )
        
        self.logger.info(f"Started conversation: {session_id}")
        
        return session_id
    
    def continue_conversation(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Continue an existing conversation.
        
        Args:
            session_id: Session ID
            user_message: User's message
            assistant_response: Assistant's response
            metadata: Optional metadata
        """
        # Get session
        session = self.session_manager.get_session(session_id)
        
        if not session:
            self.logger.warning(f"Session {session_id} not found, creating new")
            self.start_conversation(session_id)
            session = self.session_manager.get_session(session_id)
        
        # Get memory
        memory = session['memory']
        
        # Add messages to memory
        memory.add_message('user', user_message, metadata)
        memory.add_message('assistant', assistant_response, metadata)
        
        # Update message count
        session['message_count'] += 2
        
        # Save session
        self.session_manager.save_session(session_id)
        
        self.logger.debug(f"Updated conversation: {session_id}")
    
    def get_context_for_prompt(
        self,
        session_id: str,
        max_messages: int = 5,
        include_summary: bool = True
    ) -> str:
        """
        Get conversation context for prompt.
        
        Args:
            session_id: Session ID
            max_messages: Maximum recent messages
            include_summary: Include conversation summary
            
        Returns:
            Formatted conversation context
        """
        session = self.session_manager.get_session(session_id)
        
        if not session:
            return ""
        
        memory = session['memory']
        
        # Format memory for prompt
        context = memory.format_for_prompt(
            max_messages=max_messages,
            include_summary=include_summary
        )
        
        return context
    
    def get_conversation_history(
        self,
        session_id: str,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Args:
            session_id: Session ID
            max_messages: Maximum messages to return
            
        Returns:
            List of conversation messages
        """
        session = self.session_manager.get_session(session_id)
        
        if not session:
            return []
        
        memory = session['memory']
        
        return memory.get_conversation_history(max_messages)
    
    def clear_conversation(self, session_id: str):
        """
        Clear conversation history.
        
        Args:
            session_id: Session ID
        """
        session = self.session_manager.get_session(session_id, create_if_missing=False)
        
        if session:
            memory = session['memory']
            memory.clear()
            session['message_count'] = 0
            
            self.logger.info(f"Cleared conversation: {session_id}")
    
    def delete_conversation(self, session_id: str):
        """
        Delete a conversation.
        
        Args:
            session_id: Session ID
        """
        self.session_manager.delete_session(session_id)
        self.logger.info(f"Deleted conversation: {session_id}")
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all active conversations.
        
        Returns:
            List of conversation info
        """
        return self.session_manager.list_sessions()
    
    def get_session_statistics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session statistics.
        
        Args:
            session_id: Session ID
            
        Returns:
            Statistics dictionary
        """
        session = self.session_manager.get_session(session_id, create_if_missing=False)
        
        if not session:
            return None
        
        memory = session['memory']
        memory_stats = memory.get_statistics()
        
        return {
            'session_id': session_id,
            'message_count': session['message_count'],
            'created_at': session['created_at'].isoformat(),
            'last_accessed': session['last_accessed'].isoformat(),
            'metadata': session['metadata'],
            'memory': memory_stats
        }
    
    def cache_context(
        self,
        session_id: str,
        query: str,
        context: str,
        retrieved_docs: List[Dict[str, Any]]
    ):
        """
        Cache retrieved context for session.
        
        Args:
            session_id: Session ID
            query: Query
            context: Retrieved context
            retrieved_docs: Retrieved documents
        """
        session = self.session_manager.get_session(session_id)
        
        if session:
            memory = session['memory']
            memory.cache_context(query, context, retrieved_docs)
    
    def get_cached_context(
        self,
        session_id: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached context for query.
        
        Args:
            session_id: Session ID
            query: Query
            
        Returns:
            Cached context if found
        """
        session = self.session_manager.get_session(session_id, create_if_missing=False)
        
        if not session:
            return None
        
        memory = session['memory']
        
        return memory.get_cached_context(query)
    
    def cleanup_expired_sessions(self):
        """Cleanup expired sessions."""
        self.session_manager.cleanup_expired_sessions()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.session_manager.get_statistics()
