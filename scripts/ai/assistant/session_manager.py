"""
Session manager for conversation persistence.

Manages conversation sessions with expiration and storage.
"""

import sys
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger
from ai.assistant.memory_manager import MemoryManager


class SessionManager:
    """
    Manages conversation sessions.
    
    Features:
    - Session creation and retrieval
    - Session persistence
    - Session expiration
    - Memory management per session
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize session manager.
        
        Args:
            config: Assistant configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Session configuration
        memory_config = config.get('memory', {})
        self.session_timeout = memory_config.get('session_timeout', 3600)  # 1 hour
        self.persist_sessions = memory_config.get('persist_sessions', True)
        self.storage_path = Path(memory_config.get('session_storage', 'storage/sessions'))
        
        # Create storage directory
        if self.persist_sessions:
            self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Active sessions: session_id -> {memory, metadata}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info(
            f"SessionManager initialized: timeout={self.session_timeout}s, "
            f"persist={self.persist_sessions}"
        )
    
    def create_session(
        self,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID (generated if None)
            metadata: Optional session metadata
            
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Check if session already exists
        if session_id in self.sessions:
            self.logger.warning(f"Session {session_id} already exists")
            return session_id
        
        # Create session
        session = {
            'id': session_id,
            'memory': MemoryManager(self.config),
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'metadata': metadata or {},
            'message_count': 0
        }
        
        self.sessions[session_id] = session
        
        self.logger.info(f"Created session: {session_id}")
        
        return session_id
    
    def get_session(
        self,
        session_id: str,
        create_if_missing: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
            create_if_missing: Create if doesn't exist
            
        Returns:
            Session dictionary or None
        """
        # Check if session exists
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Check expiration
            if self._is_expired(session):
                self.logger.info(f"Session {session_id} expired")
                self.delete_session(session_id)
                
                if create_if_missing:
                    return self.get_session(self.create_session(session_id))
                return None
            
            # Update last accessed
            session['last_accessed'] = datetime.now()
            
            return session
        
        # Try to load from storage
        if self.persist_sessions:
            loaded = self._load_session(session_id)
            if loaded:
                self.sessions[session_id] = loaded
                return loaded
        
        # Create new session if requested
        if create_if_missing:
            new_id = self.create_session(session_id)
            return self.sessions[new_id]
        
        return None
    
    def delete_session(self, session_id: str):
        """
        Delete a session.
        
        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            # Clear memory
            self.sessions[session_id]['memory'].clear()
            
            # Remove from active sessions
            del self.sessions[session_id]
            
            self.logger.info(f"Deleted session: {session_id}")
        
        # Delete from storage
        if self.persist_sessions:
            self._delete_session_file(session_id)
    
    def save_session(self, session_id: str):
        """
        Save session to storage.
        
        Args:
            session_id: Session ID
        """
        if not self.persist_sessions:
            return
        
        session = self.sessions.get(session_id)
        if not session:
            self.logger.warning(f"Session {session_id} not found")
            return
        
        try:
            # Prepare serializable session data
            session_data = {
                'id': session['id'],
                'created_at': session['created_at'].isoformat(),
                'last_accessed': session['last_accessed'].isoformat(),
                'metadata': session['metadata'],
                'message_count': session['message_count'],
                'memory': {
                    'messages': list(session['memory'].messages),
                    'summary': session['memory'].summary
                }
            }
            
            # Save to file
            session_file = self.storage_path / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            self.logger.debug(f"Saved session: {session_id}")
        
        except Exception as e:
            self.logger.error(f"Failed to save session {session_id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session from storage."""
        try:
            session_file = self.storage_path / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Reconstruct session
            memory = MemoryManager(self.config)
            
            # Restore messages
            for msg in session_data['memory']['messages']:
                memory.messages.append(msg)
            
            # Restore summary
            if session_data['memory']['summary']:
                memory.update_summary(session_data['memory']['summary'])
            
            session = {
                'id': session_data['id'],
                'memory': memory,
                'created_at': datetime.fromisoformat(session_data['created_at']),
                'last_accessed': datetime.fromisoformat(session_data['last_accessed']),
                'metadata': session_data['metadata'],
                'message_count': session_data['message_count']
            }
            
            self.logger.debug(f"Loaded session: {session_id}")
            
            return session
        
        except Exception as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def _delete_session_file(self, session_id: str):
        """Delete session file from storage."""
        try:
            session_file = self.storage_path / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                self.logger.debug(f"Deleted session file: {session_id}")
        
        except Exception as e:
            self.logger.error(f"Failed to delete session file {session_id}: {e}")
    
    def _is_expired(self, session: Dict[str, Any]) -> bool:
        """Check if session is expired."""
        elapsed = (datetime.now() - session['last_accessed']).total_seconds()
        return elapsed > self.session_timeout
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        expired = []
        
        for session_id, session in self.sessions.items():
            if self._is_expired(session):
                expired.append(session_id)
        
        for session_id in expired:
            self.delete_session(session_id)
        
        if expired:
            self.logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active sessions.
        
        Returns:
            List of session info dicts
        """
        sessions_info = []
        
        for session_id, session in self.sessions.items():
            info = {
                'id': session_id,
                'created_at': session['created_at'].isoformat(),
                'last_accessed': session['last_accessed'].isoformat(),
                'message_count': session['message_count'],
                'metadata': session['metadata']
            }
            sessions_info.append(info)
        
        return sessions_info
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get session statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'active_sessions': len(self.sessions),
            'persist_enabled': self.persist_sessions,
            'session_timeout': self.session_timeout,
            'storage_path': str(self.storage_path) if self.persist_sessions else None
        }
