"""
Documents API endpoints.

Handles knowledge base document management.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, File, UploadFile, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.documents import (
    DocumentUploadResponse,
    DocumentInfo,
    DocumentDetail,
    DocumentList,
    DocumentRenameRequest
)
from app.services.documents_service import DocumentsService
from app.dependencies.auth import get_current_active_user
from app.database.models import User


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    source: Optional[str] = Query(None, description="Document source"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document to knowledge base.
    
    Accepts PDF, TXT, MD, DOC, and DOCX files up to 10MB.
    
    Args:
        file: Document file
        source: Optional source identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Upload response with document ID and processing status
    """
    service = DocumentsService(db)
    result = await service.upload_document(
        user=current_user,
        file=file,
        source=source
    )
    
    return DocumentUploadResponse(**result)


@router.get("", response_model=DocumentList)
async def get_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    is_processed: Optional[bool] = Query(None, description="Filter by processing status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get documents with filtering and pagination.
    
    Args:
        page: Page number
        page_size: Items per page
        mime_type: Optional MIME type filter
        source: Optional source filter
        is_processed: Optional processing status filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Paginated list of documents
    """
    service = DocumentsService(db)
    documents, total = await service.get_documents(
        user=current_user,
        page=page,
        page_size=page_size,
        mime_type=mime_type,
        source=source,
        is_processed=is_processed,
        date_from=date_from,
        date_to=date_to
    )
    
    has_more = (page * page_size) < total
    
    return DocumentList(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/stats")
async def get_document_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get document statistics.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Document statistics
    """
    service = DocumentsService(db)
    stats = await service.get_document_stats(user=current_user)
    return stats


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed document information.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Detailed document information
    """
    service = DocumentsService(db)
    document = await service.get_document(
        user=current_user,
        document_id=document_id
    )
    
    return DocumentDetail(**document)


@router.put("/{document_id}/rename", response_model=DocumentDetail)
async def rename_document(
    document_id: int,
    request: DocumentRenameRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Rename a document.
    
    Args:
        document_id: Document ID
        request: Rename request with new filename
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated document information
    """
    service = DocumentsService(db)
    document = await service.rename_document(
        user=current_user,
        document_id=document_id,
        new_filename=request.new_filename
    )
    
    return DocumentDetail(**document)


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download original document file.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        File download response
    """
    service = DocumentsService(db)
    file_path, original_filename = await service.download_document(
        user=current_user,
        document_id=document_id
    )
    
    return FileResponse(
        path=str(file_path),
        filename=original_filename,
        media_type='application/octet-stream'
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document.
    
    Permanently removes the document and all associated files.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user
        db: Database session
    """
    service = DocumentsService(db)
    await service.delete_document(
        user=current_user,
        document_id=document_id
    )
