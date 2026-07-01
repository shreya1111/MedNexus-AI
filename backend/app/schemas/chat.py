"""
Chat schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Individual chat message."""
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response schema."""
    message: str
    session_id: str
    confidence: float
    followup_questions: List[str] = []
    citations: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    latency_ms: float


class ChatHistory(BaseModel):
    """Chat history schema."""
    session_id: str
    messages: List[ChatMessage]
    total_messages: int
    created_at: datetime
    last_accessed: datetime


class SessionInfo(BaseModel):
    """Session information schema."""
    session_id: str
    message_count: int
    created_at: datetime
    last_accessed: datetime
    is_active: bool
    metadata: Optional[Dict[str, Any]] = None


class ChatHistoryList(BaseModel):
    """List of chat sessions."""
    sessions: List[SessionInfo]
    total: int
