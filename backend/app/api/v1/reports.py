"""
Medical Reports API endpoints.

Handles medical report upload, processing, and AI-powered analysis.
"""

from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.reports import (
    ReportUploadResponse,
    ReportInfo,
    ReportDetail,
    ReportList,
    ReportAnalysis
)
from app.services.reports_service import ReportsService
from app.dependencies.auth import get_current_active_user
from app.database.models import User


router = APIRouter(prefix="/reports", tags=["Medical Reports"])


@router.post("/upload", response_model=ReportUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a medical report for processing.
    
    Accepts PDF, TXT, DOC, and DOCX files up to 10MB.
    
    Args:
        file: Medical report file
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Upload response with document ID and processing status
    """
    service = ReportsService(db)
    result = await service.upload_report(
        user=current_user,
        file=file
    )
    
    return ReportUploadResponse(**result)


@router.get("", response_model=ReportList)
async def get_reports(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all medical reports for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of reports with basic information
    """
    service = ReportsService(db)
    reports = await service.get_reports(user=current_user)
    
    return ReportList(
        reports=reports,
        total=len(reports)
    )


@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific report.
    
    Includes analysis results if available.
    
    Args:
        report_id: Report ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Detailed report information with analysis
    """
    service = ReportsService(db)
    report = await service.get_report(
        user=current_user,
        report_id=report_id
    )
    
    return ReportDetail(**report)


@router.post("/{report_id}/analyze", response_model=ReportAnalysis)
async def analyze_report(
    report_id: int,
    include_recommendations: bool = True,
    include_risks: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a medical report using AI.
    
    Generates summary, findings, recommendations, and risk assessment.
    
    Args:
        report_id: Report ID
        include_recommendations: Include clinical recommendations
        include_risks: Include risk assessment
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        AI-powered analysis of the medical report
    """
    service = ReportsService(db)
    analysis = await service.analyze_report(
        user=current_user,
        report_id=report_id,
        include_recommendations=include_recommendations,
        include_risks=include_risks
    )
    
    return ReportAnalysis(**analysis)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a medical report.
    
    Permanently removes the report and all associated data.
    
    Args:
        report_id: Report ID
        current_user: Current authenticated user
        db: Database session
    """
    service = ReportsService(db)
    await service.delete_report(
        user=current_user,
        report_id=report_id
    )
