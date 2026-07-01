"""
Chat service.

Integrates with Phase 4A/4B Medical AI Assistant for conversational AI.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

# Add scripts directory to path to import Phase 4A/4B modules
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "scripts"))

from ai.assistant import MedicalAssistant, AssistantResponse
from app.database.models import User, Session, Conversation
from app.core.config import settings
from app.core.exceptions import NotFoundError, ServiceError


class ChatService:
    """
    Chat service for medical AI conversations.
    
    Integrates with Phase 4A Medical Assistant and Phase 4B Conversation Engine.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize chat service.
        
        Args:
            db: Database session
        """
        self.db = db
        
        # Initialize Medical AI Assistant (Phase 4A/4B)
        try:
            self.assistant = MedicalAssistant(
                config_path=str(Path(settings.UPLOAD_DIR).parent.parent / "config" / "assistant.yaml"),
                retrieval_config_path=str(Path(settings.UPLOAD_DIR).parent.parent / "config" / "retrieval.yaml"),
                embedding_config_path=str(Path(settings.UPLOAD_DIR).parent.parent / "config" / "embedding.yaml")
            )
        except Exception as e:
            raise ServiceError(f"Failed to initialize Medical Assistant: {str(e)}")
    
    async def send_message(
        self,
        user: User,
        message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message and get AI response.
        
        Args:
            user: Current user
            message: User message
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Response dictionary with answer, session_id, confidence, etc.
        """
        try:
            # Get or create session
            if session_id:
                session = await self._get_session(user.id, session_id)
                if not session:
                    raise NotFoundError("Session not found")
            else:
                session = await self._create_session(user.id)
                session_id = session.session_id
            
            # Get conversation history from database
            history = await self._get_conversation_history(session.id)
            
            # Call Phase 4A/4B Medical Assistant
            response: AssistantResponse = self.assistant.ask(
                query=message,
                conversation_history=history,
                session_id=session_id
            )
            
            # Save user message to database
            await self._save_message(
                user_id=user.id,
                session_id=session.id,
                role="user",
                content=message
            )
            
            # Save assistant response to database
            await self._save_message(
                user_id=user.id,
                session_id=session.id,
                role="assistant",
                content=response.answer,
                metadata={
                    "confidence": response.confidence,
                    "latency_ms": response.latency_ms,
                    "citations": [c.__dict__ if hasattr(c, '__dict__') else c for c in response.citations],
                    "followup_questions": response.followup_questions
                },
                tokens_used=response.token_usage.get("total", 0),
                latency_ms=response.latency_ms,
                confidence=response.confidence
            )
            
            # Update session
            session.message_count += 2
            session.last_accessed = datetime.utcnow()
            await self.db.commit()
            
            # Return response
            return {
                "message": response.answer,
                "session_id": session_id,
                "confidence": response.confidence,
                "followup_questions": response.followup_questions or [],
                "citations": [
                    {
                        "source": c.source if hasattr(c, 'source') else str(c),
                        "similarity": c.similarity if hasattr(c, 'similarity') else 0.0
                    }
                    for c in response.citations
                ],
                "metadata": {
                    "latency_ms": response.latency_ms,
                    "tokens_used": response.token_usage.get("total", 0),
                    "safety_check": response.safety_check.category if hasattr(response.safety_check, 'category') else "safe"
                },
                "latency_ms": response.latency_ms
            }
        
        except Exception as e:
            raise ServiceError(f"Chat service error: {str(e)}")
    
    async def get_chat_history(
        self,
        user: User,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a session.
        
        Args:
            user: Current user
            session_id: Session ID
            limit: Maximum messages to return
            
        Returns:
            List of messages
        """
        # Get session
        session = await self._get_session(user.id, session_id)
        if not session:
            raise NotFoundError("Session not found")
        
        # Get messages
        query = select(Conversation).where(
            Conversation.session_id == session.id
        ).order_by(Conversation.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        messages = result.scalars().all()
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.created_at,
                "metadata": msg.metadata
            }
            for msg in messages
        ]
    
    async def get_user_sessions(self, user: User) -> List[Dict[str, Any]]:
        """
        Get all sessions for a user.
        
        Args:
            user: Current user
            
        Returns:
            List of sessions
        """
        result = await self.db.execute(
            select(Session).where(
                Session.user_id == user.id,
                Session.is_active == True
            ).order_by(Session.last_accessed.desc())
        )
        sessions = result.scalars().all()
        
        return [
            {
                "session_id": session.session_id,
                "message_count": session.message_count,
                "created_at": session.created_at,
                "last_accessed": session.last_accessed,
                "is_active": session.is_active,
                "metadata": session.metadata
            }
            for session in sessions
        ]
    
    async def clear_chat_history(
        self,
        user: User,
        session_id: str
    ) -> None:
        """
        Clear chat history for a session.
        
        Args:
            user: Current user
            session_id: Session ID
        """
        # Get session
        session = await self._get_session(user.id, session_id)
        if not session:
            raise NotFoundError("Session not found")
        
        # Delete messages
        await self.db.execute(
            delete(Conversation).where(Conversation.session_id == session.id)
        )
        
        # Update session
        session.message_count = 0
        await self.db.commit()
        
        # Clear Phase 4B conversation memory
        try:
            self.assistant.clear_conversation(session_id)
        except Exception:
            pass  # Silent fail if assistant cleanup fails
    
    async def _create_session(self, user_id: int) -> Session:
        """Create a new session."""
        # Generate session ID using Phase 4B
        session_id = self.assistant.start_conversation()
        
        session = Session(
            user_id=user_id,
            session_id=session_id,
            message_count=0,
            is_active=True
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def _get_session(
        self,
        user_id: int,
        session_id: str
    ) -> Optional[Session]:
        """Get session by ID."""
        result = await self.db.execute(
            select(Session).where(
                Session.user_id == user_id,
                Session.session_id == session_id,
                Session.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def _save_message(
        self,
        user_id: int,
        session_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: Optional[int] = None,
        latency_ms: Optional[float] = None,
        confidence: Optional[float] = None
    ) -> Conversation:
        """Save a message to database."""
        message = Conversation(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            confidence=confidence
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def _get_conversation_history(
        self,
        session_id: int,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Get conversation history in format expected by Phase 4B."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.session_id == session_id
            ).order_by(Conversation.created_at.desc()).limit(limit)
        )
        messages = result.scalars().all()
        
        # Reverse to chronological order
        messages = list(reversed(messages))
        
        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in messages
        ]
    
    def __del__(self):
        """Cleanup assistant on service destruction."""
        try:
            if hasattr(self, 'assistant'):
                self.assistant.cleanup()
        except Exception:
            pass
