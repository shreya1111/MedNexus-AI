"""
Medical Reports schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReportAnalysis(BaseModel):
    """Medical report analysis result."""
    summary: str
    findings: List[str] = []
    recommendations: List[str] = []
    risks: List[str] = []
    confidence: float


class ReportUploadResponse(BaseModel):
    """Response after report upload."""
    id: int
    filename: str
    status: str  # processing, completed, failed
    message: str


class ReportInfo(BaseModel):
    """Basic report information."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    is_processed: bool
    processing_status: str
    created_at: datetime
    updated_at: datetime


class ReportDetail(BaseModel):
    """Detailed report with analysis."""
    id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    is_processed: bool
    processing_status: str
    processing_error: Optional[str] = None
    analysis: Optional[ReportAnalysis] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ReportList(BaseModel):
    """List of reports."""
    reports: List[ReportInfo]
    total: int


class ReportAnalysisRequest(BaseModel):
    """Request to analyze a report."""
    report_id: int = Field(..., gt=0)
    include_recommendations: bool = True
    include_risks: bool = True
