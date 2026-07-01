"""
Database models for MedNexus-AI.

Defines all database tables and relationships.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, JSON
)
from sqlalchemy.orm import relationship
import enum

from app.database.base import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    PATIENT = "patient"
    DOCTOR = "doctor"
    RESEARCHER = "researcher"
    ADMINISTRATOR = "administrator"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PATIENT, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("MedicalReport", back_populates="user", cascade="all, delete-orphan")
    api_usage = relationship("APIUsage", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """User session model for conversation history."""
    
    __tablename__ = "sessions"
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Session data
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    metadata = Column(JSON, nullable=True)
    message_count = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="sessions")
    conversations = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation message model."""
    
    __tablename__ = "conversations"
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    
    # Message data
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    session = relationship("Session", back_populates="conversations")


class Document(Base):
    """Uploaded document model."""
    
    __tablename__ = "documents"
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Document data
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Processing
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_status = Column(String(50), default="pending", nullable=False)
    processing_error = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    checksum = Column(String(64), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="documents")


class MedicalReport(Base):
    """Medical report analysis model."""
    
    __tablename__ = "medical_reports"
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Report data
    report_type = Column(String(100), nullable=False)  # analysis, summary
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=False)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="reports")


class APIUsage(Base):
    """API usage tracking model."""
    
    __tablename__ = "api_usage"
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Request data
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    
    # Performance
    request_time = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=False)
    
    # Metadata
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)
    request_id = Column(String(36), nullable=True, index=True)
    
    # Tokens (for AI endpoints)
    tokens_used = Column(Integer, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="api_usage")


class RefreshToken(Base):
    """Refresh token model."""
    
    __tablename__ = "refresh_tokens"
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Token data
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Status
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Metadata
    user_agent = Column(String(512), nullable=True)
    ip_address = Column(String(45), nullable=True)
