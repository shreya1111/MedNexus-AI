"""
Documents schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    id: int
    filename: str
    status: str  # pending, processing, completed, failed
    message: str


class DocumentInfo(BaseModel):
    """Document information."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    is_processed: bool
    processing_status: str
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentDetail(BaseModel):
    """Detailed document information."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    is_processed: bool
    processing_status: str
    processing_error: Optional[str] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentList(BaseModel):
    """List of documents with pagination."""
    documents: List[DocumentInfo]
    total: int
    page: int
    page_size: int
    has_more: bool


class DocumentRenameRequest(BaseModel):
    """Request to rename document."""
    new_filename: str = Field(..., min_length=1, max_length=255)


class DocumentFilterParams(BaseModel):
    """Document filtering parameters."""
    mime_type: Optional[str] = None
    source: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_processed: Optional[bool] = None
