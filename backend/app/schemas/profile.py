"""
Profile and Settings schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class ProfileResponse(BaseModel):
    """User profile response."""
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    statistics: Optional[Dict[str, Any]] = None


class ProfileUpdateRequest(BaseModel):
    """Profile update request."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)


class SettingsResponse(BaseModel):
    """User settings response."""
    theme: str = "system"
    language: str = "en"
    notifications_enabled: bool = True
    email_notifications: bool = True
    ai_model: str = "gemini-2.0-flash"
    retrieval_top_k: int = 5
    chunk_size: int = 512
    embedding_provider: str = "google"


class SettingsUpdateRequest(BaseModel):
    """Settings update request."""
    theme: Optional[str] = Field(None, pattern="^(light|dark|system)$")
    language: Optional[str] = Field(None, pattern="^[a-z]{2}$")
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    ai_model: Optional[str] = None
    retrieval_top_k: Optional[int] = Field(None, ge=1, le=20)
    chunk_size: Optional[int] = Field(None, ge=128, le=2048)
    embedding_provider: Optional[str] = None
