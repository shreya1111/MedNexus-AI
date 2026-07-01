"""
Documents service for knowledge base management.

Handles document upload, processing, and management for the knowledge base.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import shutil
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_, or_
from fastapi import UploadFile

from app.database.models import User, Document
from app.core.config import settings
from app.core.exceptions import NotFoundError, ServiceError, ValidationError


def _load_document_processor():
    """
    Lazily import the document processor module from the scripts package.

    Imported on demand so the heavy AI/vector dependencies are not required
    just to start the FastAPI backend.
    """
    scripts_dir = str(Path(__file__).parent.parent.parent.parent / "scripts")
    if scripts_dir not in sys.path:
        sys.path.append(scripts_dir)
    from processors.document_processor import DocumentProcessor
    return DocumentProcessor


class DocumentsService:
    """
    Documents service for knowledge base management.
    
    Handles document upload, processing, indexing, and retrieval.
    """
    
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'text/plain',
        'text/markdown',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, db: AsyncSession):
        """
        Initialize documents service.

        Args:
            db: Database session
        """
        self.db = db

        # Initialize upload directory
        self.upload_dir = Path(settings.UPLOAD_DIR) / "documents"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self._processor = None

    def _get_processor(self):
        """Lazily initialize the document processor."""
        if self._processor is None:
            DocumentProcessor = _load_document_processor()
            processed_dir = self.upload_dir / "processed"
            metadata_dir = self.upload_dir / "metadata"
            self._processor = DocumentProcessor(
                output_dir=processed_dir,
                metadata_dir=metadata_dir,
                enable_cleaning=True
            )
        return self._processor
    
    async def upload_document(
        self,
        user: User,
        file: UploadFile,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload and process a document for knowledge base.
        
        Args:
            user: Current user
            file: Uploaded file
            source: Document source (e.g., 'manual_upload', 'api')
            
        Returns:
            Upload response with document ID and status
        """
        # Validate file
        if not file.filename:
            raise ValidationError("Filename is required")
        
        if file.content_type not in self.ALLOWED_MIME_TYPES:
            raise ValidationError(
                f"File type not allowed. Allowed types: {', '.join(self.ALLOWED_MIME_TYPES)}"
            )
        
        # Read file
        content = await file.read()
        file_size = len(content)
        
        if file_size > self.MAX_FILE_SIZE:
            raise ValidationError(f"File too large. Maximum size: {self.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        if file_size == 0:
            raise ValidationError("File is empty")
        
        try:
            # Generate unique filename
            file_ext = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = self.upload_dir / unique_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Create document record
            document = Document(
                user_id=user.id,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                mime_type=file.content_type,
                is_processed=False,
                processing_status="pending",
                metadata={"source": source or "manual_upload"}
            )
            
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            # Process document
            try:
                processing_result = self._get_processor().process_document(
                    input_path=file_path,
                    source=source or "knowledge_base",
                    preserve_structure=False
                )
                
                if processing_result.status in ['success', 'partial']:
                    document.is_processed = True
                    document.processing_status = "completed"
                    document.metadata = {
                        **document.metadata,
                        **processing_result.metadata
                    }
                else:
                    document.processing_status = "failed"
                    document.processing_error = processing_result.error_message
                
                await self.db.commit()
                
            except Exception as e:
                document.processing_status = "failed"
                document.processing_error = str(e)
                await self.db.commit()
            
            return {
                "id": document.id,
                "filename": document.filename,
                "status": document.processing_status,
                "message": "Document uploaded successfully"
            }
        
        except Exception as e:
            raise ServiceError(f"Upload failed: {str(e)}")
    
    async def get_documents(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        mime_type: Optional[str] = None,
        source: Optional[str] = None,
        is_processed: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get documents with filtering and pagination.
        
        Args:
            user: Current user
            page: Page number (1-indexed)
            page_size: Items per page
            mime_type: Filter by MIME type
            source: Filter by source
            is_processed: Filter by processing status
            date_from: Filter by creation date (from)
            date_to: Filter by creation date (to)
            
        Returns:
            Tuple of (documents list, total count)
        """
        # Build query
        query = select(Document).where(Document.user_id == user.id)
        count_query = select(func.count(Document.id)).where(Document.user_id == user.id)
        
        # Apply filters
        filters = []
        if mime_type:
            filters.append(Document.mime_type == mime_type)
        if source:
            filters.append(Document.metadata['source'].astext == source)
        if is_processed is not None:
            filters.append(Document.is_processed == is_processed)
        if date_from:
            filters.append(Document.created_at >= date_from)
        if date_to:
            filters.append(Document.created_at <= date_to)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        documents = result.scalars().all()
        
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "original_filename": doc.original_filename,
                "file_size": doc.file_size,
                "mime_type": doc.mime_type,
                "is_processed": doc.is_processed,
                "processing_status": doc.processing_status,
                "source": doc.metadata.get("source") if doc.metadata else None,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at
            }
            for doc in documents
        ], total
    
    async def get_document(
        self,
        user: User,
        document_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed document information.
        
        Args:
            user: Current user
            document_id: Document ID
            
        Returns:
            Detailed document information
        """
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user.id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Document not found")
        
        return {
            "id": document.id,
            "filename": document.filename,
            "original_filename": document.original_filename,
            "file_size": document.file_size,
            "mime_type": document.mime_type,
            "is_processed": document.is_processed,
            "processing_status": document.processing_status,
            "processing_error": document.processing_error,
            "source": document.metadata.get("source") if document.metadata else None,
            "metadata": document.metadata,
            "checksum": document.checksum,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }
    
    async def rename_document(
        self,
        user: User,
        document_id: int,
        new_filename: str
    ) -> Dict[str, Any]:
        """
        Rename a document.
        
        Args:
            user: Current user
            document_id: Document ID
            new_filename: New filename
            
        Returns:
            Updated document info
        """
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user.id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Document not found")
        
        # Update filename (keep extension)
        ext = Path(document.original_filename).suffix
        if not new_filename.endswith(ext):
            new_filename = f"{new_filename}{ext}"
        
        document.original_filename = new_filename
        document.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(document)
        
        return await self.get_document(user, document_id)
    
    async def delete_document(
        self,
        user: User,
        document_id: int
    ) -> None:
        """
        Delete a document.
        
        Args:
            user: Current user
            document_id: Document ID
        """
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user.id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Document not found")
        
        # Delete file
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete processed file if exists
        if document.metadata and "output_path" in document.metadata:
            processed_path = Path(document.metadata["output_path"])
            if processed_path.exists():
                processed_path.unlink()
        
        # Delete metadata file if exists
        if document.metadata and "metadata_path" in document.metadata:
            metadata_path = Path(document.metadata["metadata_path"])
            if metadata_path.exists():
                metadata_path.unlink()
        
        # Delete document record
        await self.db.delete(document)
        await self.db.commit()
    
    async def download_document(
        self,
        user: User,
        document_id: int
    ) -> Tuple[Path, str]:
        """
        Get document file path for download.
        
        Args:
            user: Current user
            document_id: Document ID
            
        Returns:
            Tuple of (file path, original filename)
        """
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user.id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Document not found")
        
        file_path = Path(document.file_path)
        if not file_path.exists():
            raise NotFoundError("Document file not found")
        
        return file_path, document.original_filename
    
    async def get_document_stats(self, user: User) -> Dict[str, Any]:
        """
        Get document statistics for user.
        
        Args:
            user: Current user
            
        Returns:
            Document statistics
        """
        # Total documents
        total_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.user_id == user.id)
        )
        total_documents = total_result.scalar_one()
        
        # Processed documents
        processed_result = await self.db.execute(
            select(func.count(Document.id)).where(
                Document.user_id == user.id,
                Document.is_processed == True
            )
        )
        processed_documents = processed_result.scalar_one()
        
        # Total size
        size_result = await self.db.execute(
            select(func.sum(Document.file_size)).where(Document.user_id == user.id)
        )
        total_size = size_result.scalar_one() or 0
        
        # By type
        type_result = await self.db.execute(
            select(
                Document.mime_type,
                func.count(Document.id)
            ).where(
                Document.user_id == user.id
            ).group_by(Document.mime_type)
        )
        by_type = {row[0]: row[1] for row in type_result.all()}
        
        return {
            "total_documents": total_documents,
            "processed_documents": processed_documents,
            "pending_documents": total_documents - processed_documents,
            "total_size_bytes": total_size,
            "by_type": by_type
        }
