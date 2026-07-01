"""
Chat API endpoints.

Handles conversational AI interactions with the Medical AI Assistant.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistory,
    ChatHistoryList
)
from app.services.chat_service import ChatService
from app.dependencies.auth import get_current_active_user
from app.database.models import User


router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to the AI assistant and get a response.
    
    Args:
        request: Chat request with message and optional session_id
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AI response with answer, citations, follow-up questions, etc.
    """
    service = ChatService(db)
    response = await service.send_message(
        user=current_user,
        message=request.message,
        session_id=request.session_id
    )
    
    return ChatResponse(**response)


@router.get("/history", response_model=ChatHistoryList)
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chat sessions for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of chat sessions
    """
    service = ChatService(db)
    sessions = await service.get_user_sessions(current_user)
    
    return ChatHistoryList(
        sessions=sessions,
        total=len(sessions)
    )


@router.get("/history/{session_id}", response_model=ChatHistory)
async def get_session_history(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat history for a specific session.
    
    Args:
        session_id: Session ID
        limit: Maximum number of messages to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Chat history with messages
    """
    service = ChatService(db)
    messages = await service.get_chat_history(
        user=current_user,
        session_id=session_id,
        limit=limit
    )
    
    # Get session info
    sessions = await service.get_user_sessions(current_user)
    session_info = next(
        (s for s in sessions if s["session_id"] == session_id),
        None
    )
    
    if not session_info:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Session not found")
    
    return ChatHistory(
        session_id=session_id,
        messages=messages,
        total_messages=len(messages),
        created_at=session_info["created_at"],
        last_accessed=session_info["last_accessed"]
    )


@router.delete("/history/{session_id}", status_code=204)
async def clear_session_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Clear chat history for a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
    """
    service = ChatService(db)
    await service.clear_chat_history(
        user=current_user,
        session_id=session_id
    )
