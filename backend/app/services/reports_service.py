"""
Medical Reports service.

Handles medical report upload, processing, and AI-powered analysis.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import UploadFile

from app.database.models import User, Document, MedicalReport
from app.core.config import settings
from app.core.exceptions import NotFoundError, ServiceError, ValidationError


def _load_processing_stack():
    """
    Lazily import the document processing and AI assistant modules.

    Imported on demand so the heavy AI/vector dependencies (chromadb,
    sentence-transformers, google-generativeai, etc.) are not required just
    to start the FastAPI backend.
    """
    scripts_dir = str(Path(__file__).parent.parent.parent.parent / "scripts")
    if scripts_dir not in sys.path:
        sys.path.append(scripts_dir)
    from processors.document_processor import DocumentProcessor
    from ai.assistant import MedicalAssistant
    return DocumentProcessor, MedicalAssistant


class ReportsService:
    """
    Medical Reports service for document upload and AI analysis.
    
    Integrates with Phase 3 document processing and Phase 4A Medical Assistant.
    """
    
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, db: AsyncSession):
        """
        Initialize reports service.

        Args:
            db: Database session
        """
        self.db = db

        # Initialize upload directory
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self._processor = None
        self._assistant = None

    def _get_processor(self):
        """Lazily initialize the document processor (Phase 3)."""
        if self._processor is None:
            DocumentProcessor, _ = _load_processing_stack()
            processed_dir = self.upload_dir / "processed"
            metadata_dir = self.upload_dir / "metadata"
            self._processor = DocumentProcessor(
                output_dir=processed_dir,
                metadata_dir=metadata_dir,
                enable_cleaning=True
            )
        return self._processor

    def _get_assistant(self):
        """Lazily initialize the Medical AI Assistant (Phase 4A)."""
        if self._assistant is None:
            try:
                _, MedicalAssistant = _load_processing_stack()
                config_dir = Path(__file__).parent.parent.parent.parent / "config"
                self._assistant = MedicalAssistant(
                    config_path=str(config_dir / "assistant.yaml"),
                    retrieval_config_path=str(config_dir / "retrieval.yaml"),
                    embedding_config_path=str(config_dir / "embedding.yaml")
                )
            except Exception as e:
                raise ServiceError(f"Failed to initialize Medical Assistant: {str(e)}")
        return self._assistant
    
    async def upload_report(
        self,
        user: User,
        file: UploadFile
    ) -> Dict[str, Any]:
        """
        Upload and process a medical report.
        
        Args:
            user: Current user
            file: Uploaded file
            
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
                processing_status="pending"
            )
            
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            # Process document asynchronously (in production, use background task)
            try:
                # Process with Phase 3 document processor
                processing_result = self._get_processor().process_document(
                    input_path=file_path,
                    source="medical_report",
                    preserve_structure=False
                )
                
                if processing_result.status in ['success', 'partial']:
                    document.is_processed = True
                    document.processing_status = "completed"
                    document.metadata = processing_result.metadata
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
                "message": "Report uploaded successfully"
            }
        
        except Exception as e:
            raise ServiceError(f"Upload failed: {str(e)}")
    
    async def get_reports(self, user: User) -> List[Dict[str, Any]]:
        """
        Get all reports for a user.
        
        Args:
            user: Current user
            
        Returns:
            List of report information
        """
        result = await self.db.execute(
            select(Document).where(
                Document.user_id == user.id
            ).order_by(Document.created_at.desc())
        )
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
                "created_at": doc.created_at,
                "updated_at": doc.updated_at
            }
            for doc in documents
        ]
    
    async def get_report(
        self,
        user: User,
        report_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed report information including analysis.
        
        Args:
            user: Current user
            report_id: Report ID
            
        Returns:
            Detailed report with analysis
        """
        # Get document
        result = await self.db.execute(
            select(Document).where(
                Document.id == report_id,
                Document.user_id == user.id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Report not found")
        
        # Get analysis if exists
        analysis_result = await self.db.execute(
            select(MedicalReport).where(
                MedicalReport.user_id == user.id,
                MedicalReport.metadata['document_id'].astext == str(report_id)
            ).order_by(MedicalReport.created_at.desc())
        )
        analysis_record = analysis_result.scalar_one_or_none()
        
        analysis = None
        if analysis_record and analysis_record.metadata:
            analysis = {
                "summary": analysis_record.output_text,
                "findings": analysis_record.metadata.get("findings", []),
                "recommendations": analysis_record.metadata.get("recommendations", []),
                "risks": analysis_record.metadata.get("risks", []),
                "confidence": analysis_record.confidence or 0.0
            }
        
        return {
            "id": document.id,
            "filename": document.filename,
            "original_filename": document.original_filename,
            "file_size": document.file_size,
            "mime_type": document.mime_type,
            "is_processed": document.is_processed,
            "processing_status": document.processing_status,
            "processing_error": document.processing_error,
            "analysis": analysis,
            "metadata": document.metadata,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }
    
    async def analyze_report(
        self,
        user: User,
        report_id: int,
        include_recommendations: bool = True,
        include_risks: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a medical report using AI.
        
        Args:
            user: Current user
            report_id: Report ID
            include_recommendations: Include recommendations
            include_risks: Include risk assessment
            
        Returns:
            Analysis result
        """
        # Get document
        result = await self.db.execute(
            select(Document).where(
                Document.id == report_id,
                Document.user_id == user.id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Report not found")
        
        if not document.is_processed:
            raise ValidationError("Report is still processing")
        
        if document.processing_status == "failed":
            raise ValidationError("Report processing failed")
        
        try:
            # Read processed text
            processed_path = Path(document.metadata.get("output_path", ""))
            if not processed_path.exists():
                raise ServiceError("Processed file not found")
            
            with open(processed_path, 'r', encoding='utf-8') as f:
                report_text = f.read()
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(
                report_text,
                include_recommendations,
                include_risks
            )
            
            # Get AI analysis
            start_time = datetime.now()
            response = self._get_assistant().ask(
                query=prompt,
                conversation_history=[],
                session_id=f"report_analysis_{report_id}"
            )
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Parse response
            analysis_result = self._parse_analysis_response(response.answer)
            
            # Save analysis to database
            medical_report = MedicalReport(
                user_id=user.id,
                report_type="analysis",
                input_text=report_text[:5000],  # Store first 5000 chars
                output_text=analysis_result["summary"],
                metadata={
                    "document_id": report_id,
                    "findings": analysis_result["findings"],
                    "recommendations": analysis_result["recommendations"],
                    "risks": analysis_result["risks"]
                },
                confidence=response.confidence,
                tokens_used=response.token_usage.get("total", 0),
                processing_time_ms=processing_time
            )
            
            self.db.add(medical_report)
            await self.db.commit()
            
            return {
                "summary": analysis_result["summary"],
                "findings": analysis_result["findings"],
                "recommendations": analysis_result["recommendations"],
                "risks": analysis_result["risks"],
                "confidence": response.confidence
            }
        
        except Exception as e:
            raise ServiceError(f"Analysis failed: {str(e)}")
    
    async def delete_report(
        self,
        user: User,
        report_id: int
    ) -> None:
        """
        Delete a report.
        
        Args:
            user: Current user
            report_id: Report ID
        """
        # Get document
        result = await self.db.execute(
            select(Document).where(
                Document.id == report_id,
                Document.user_id == user.id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise NotFoundError("Report not found")
        
        # Delete file
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete processed file if exists
        if document.metadata and "output_path" in document.metadata:
            processed_path = Path(document.metadata["output_path"])
            if processed_path.exists():
                processed_path.unlink()
        
        # Delete related medical reports
        await self.db.execute(
            delete(MedicalReport).where(
                MedicalReport.user_id == user.id,
                MedicalReport.metadata['document_id'].astext == str(report_id)
            )
        )
        
        # Delete document record
        await self.db.delete(document)
        await self.db.commit()
    
    def _create_analysis_prompt(
        self,
        report_text: str,
        include_recommendations: bool,
        include_risks: bool
    ) -> str:
        """Create analysis prompt for AI."""
        prompt = f"""Analyze the following medical report and provide:

1. A clear summary of the key findings
2. List of specific medical findings
"""
        
        if include_recommendations:
            prompt += "3. Clinical recommendations based on the findings\n"
        
        if include_risks:
            prompt += "4. Identified risk factors or concerns\n"
        
        prompt += f"\nMedical Report:\n{report_text}\n\nProvide a structured analysis."
        
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        # Simple parsing - in production, use more sophisticated NLP
        lines = response.split('\n')
        
        summary = []
        findings = []
        recommendations = []
        risks = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            lower_line = line.lower()
            if 'summary' in lower_line:
                current_section = 'summary'
                continue
            elif 'finding' in lower_line:
                current_section = 'findings'
                continue
            elif 'recommendation' in lower_line:
                current_section = 'recommendations'
                continue
            elif 'risk' in lower_line:
                current_section = 'risks'
                continue
            
            # Add content to sections
            if current_section == 'summary':
                summary.append(line)
            elif current_section == 'findings':
                if line.startswith(('-', '*', '•')) or line[0].isdigit():
                    findings.append(line.lstrip('-*•0123456789. '))
            elif current_section == 'recommendations':
                if line.startswith(('-', '*', '•')) or line[0].isdigit():
                    recommendations.append(line.lstrip('-*•0123456789. '))
            elif current_section == 'risks':
                if line.startswith(('-', '*', '•')) or line[0].isdigit():
                    risks.append(line.lstrip('-*•0123456789. '))
        
        # If no sections found, use whole response as summary
        if not summary and not findings:
            summary = [response]
        
        return {
            "summary": ' '.join(summary) if summary else response,
            "findings": findings,
            "recommendations": recommendations,
            "risks": risks
        }
    
    def __del__(self):
        """Cleanup on service destruction."""
        try:
            if self._assistant is not None:
                self._assistant.cleanup()
        except Exception:
            pass
