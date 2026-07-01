"""
Admin schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr


class UserListItem(BaseModel):
    """User list item for admin."""
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime


class UserList(BaseModel):
    """Paginated user list."""
    users: List[UserListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class UserDetail(BaseModel):
    """Detailed user information for admin."""
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    statistics: Dict[str, Any]


class UserUpdateRequest(BaseModel):
    """Admin user update request."""
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class SystemStats(BaseModel):
    """System-wide statistics."""
    total_users: int
    active_users: int
    total_conversations: int
    total_messages: int
    total_documents: int
    total_reports: int
    total_searches: int
    avg_confidence: float
    avg_latency_ms: float


class SystemHealth(BaseModel):
    """System health status."""
    status: str
    database: str
    vector_db: str
    ai_service: str
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None


class ActivityLog(BaseModel):
    """Activity log entry."""
    id: int
    user_id: int
    user_email: str
    action: str
    endpoint: str
    status_code: int
    timestamp: datetime
    latency_ms: float


class ActivityLogList(BaseModel):
    """Paginated activity log list."""
    logs: List[ActivityLog]
    total: int
    page: int
    page_size: int
    has_more: bool
