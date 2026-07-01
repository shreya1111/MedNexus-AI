"""
Memory manager for conversation history.

Implements sliding window memory and conversation summarization.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger


class MemoryManager:
    """
    Manages conversation memory for the assistant.
    
    Features:
    - Sliding window memory
    - Conversation summaries
    - Token budget management
    - Memory cleanup
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize memory manager.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Memory configuration
        memory_config = config.get('memory', {})
        self.memory_type = memory_config.get('type', 'conversation_buffer_window')
        self.window_size = memory_config.get('window_size', 10)
        self.cache_enabled = memory_config.get('cache_retrieved_context', True)
        
        # Initialize message buffer (deque for efficient sliding window)
        self.messages = deque(maxlen=self.window_size)
        
        # Context cache
        self.context_cache = deque(maxlen=memory_config.get('context_cache_size', 100))
        
        # Conversation summary
        self.summary = ""
        self.summary_token_count = 0
        
        self.logger.info(
            f"MemoryManager initialized: type={self.memory_type}, "
            f"window={self.window_size}"
        )
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a message to memory.
        
        Args:
            role: Message role (user, assistant)
            content: Message content
            metadata: Optional metadata
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.messages.append(message)
        
        self.logger.debug(f"Added {role} message to memory (total: {len(self.messages)})")
    
    def get_recent_messages(
        self,
        n: Optional[int] = None,
        include_system: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages.
        
        Args:
            n: Number of messages (None for all in window)
            include_system: Include system messages
            
        Returns:
            List of recent messages
        """
        n = n or len(self.messages)
        
        recent = list(self.messages)[-n:]
        
        if not include_system:
            recent = [m for m in recent if m['role'] != 'system']
        
        return recent
    
    def get_conversation_history(
        self,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation history in simple format.
        
        Args:
            max_messages: Maximum messages to return
            
        Returns:
            List of {role, content} dicts
        """
        messages = self.get_recent_messages(max_messages)
        
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in messages
        ]
    
    def format_for_prompt(
        self,
        max_messages: int = 5,
        include_summary: bool = True
    ) -> str:
        """
        Format memory for prompt inclusion.
        
        Args:
            max_messages: Maximum recent messages to include
            include_summary: Include conversation summary
            
        Returns:
            Formatted conversation history
        """
        lines = []
        
        # Add summary if available
        if include_summary and self.summary:
            lines.append("Conversation Summary:")
            lines.append(self.summary)
            lines.append("\nRecent Messages:")
        
        # Add recent messages
        recent = self.get_recent_messages(max_messages)
        
        for msg in recent:
            role = msg['role'].upper()
            content = msg['content']
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def cache_context(
        self,
        query: str,
        context: str,
        retrieved_docs: List[Dict[str, Any]]
    ):
        """
        Cache retrieved context for reuse.
        
        Args:
            query: Original query
            context: Retrieved context
            retrieved_docs: Retrieved document list
        """
        if not self.cache_enabled:
            return
        
        cache_entry = {
            'query': query,
            'context': context,
            'docs': retrieved_docs,
            'timestamp': datetime.now().isoformat()
        }
        
        self.context_cache.append(cache_entry)
        
        self.logger.debug(f"Cached context for query: {query[:50]}...")
    
    def get_cached_context(
        self,
        query: str,
        similarity_threshold: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached context for similar query.
        
        Args:
            query: Query to search for
            similarity_threshold: Similarity threshold
            
        Returns:
            Cached context if found
        """
        if not self.cache_enabled or not self.context_cache:
            return None
        
        # Simple exact match for now
        # In production, use embedding similarity
        query_lower = query.lower()
        
        for entry in reversed(self.context_cache):
            if entry['query'].lower() == query_lower:
                self.logger.debug("Found cached context")
                return entry
        
        return None
    
    def update_summary(self, summary: str):
        """
        Update conversation summary.
        
        Args:
            summary: New summary text
        """
        self.summary = summary
        self.summary_token_count = len(summary) // 4  # Rough estimate
        
        self.logger.debug(f"Updated summary ({self.summary_token_count} tokens)")
    
    def clear(self):
        """Clear all memory."""
        self.messages.clear()
        self.context_cache.clear()
        self.summary = ""
        self.summary_token_count = 0
        
        self.logger.info("Memory cleared")
    
    def get_message_count(self) -> int:
        """Get current message count."""
        return len(self.messages)
    
    def get_token_estimate(self) -> int:
        """
        Estimate total tokens in memory.
        
        Returns:
            Estimated token count
        """
        # Summary tokens
        total = self.summary_token_count
        
        # Message tokens (rough: 1 token ≈ 4 characters)
        for msg in self.messages:
            total += len(msg['content']) // 4
        
        return total
    
    def should_summarize(
        self,
        token_threshold: int = 2000
    ) -> bool:
        """
        Check if conversation should be summarized.
        
        Args:
            token_threshold: Token threshold for summarization
            
        Returns:
            True if should summarize
        """
        return self.get_token_estimate() > token_threshold
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'message_count': len(self.messages),
            'window_size': self.window_size,
            'cache_size': len(self.context_cache),
            'has_summary': bool(self.summary),
            'estimated_tokens': self.get_token_estimate(),
            'memory_type': self.memory_type
        }
