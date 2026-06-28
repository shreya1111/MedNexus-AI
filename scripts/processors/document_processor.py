"""
Document processor for MedNexus-AI Knowledge Ingestion Framework.

Orchestrates text extraction, cleaning, and metadata generation.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import time

import sys
sys.path.append(str(Path(__file__).parent.parent))

from processors.text_extractor import TextExtractor, ExtractionStatus
from processors.document_cleaner import DocumentCleaner
from utils.logger import get_logger
from utils.hash_utils import compute_file_hash
from utils.file_utils import get_file_size, ensure_directory


logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""
    status: str  # 'success', 'partial', 'failed'
    input_path: Path
    output_path: Optional[Path] = None
    metadata_path: Optional[Path] = None
    extraction_status: Optional[str] = None
    cleaning_applied: bool = False
    processing_time_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentProcessor:
    """Processes documents through extraction and cleaning pipeline."""
    
    def __init__(
        self,
        output_dir: Path,
        metadata_dir: Path,
        enable_cleaning: bool = True,
        extractor_kwargs: Optional[Dict[str, Any]] = None,
        cleaner_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize document processor.
        
        Args:
            output_dir: Directory for processed documents
            metadata_dir: Directory for metadata
            enable_cleaning: Whether to clean extracted text
            extractor_kwargs: Arguments for TextExtractor
            cleaner_kwargs: Arguments for DocumentCleaner
        """
        self.output_dir = ensure_directory(output_dir)
        self.metadata_dir = ensure_directory(metadata_dir)
        self.enable_cleaning = enable_cleaning
        
        self.extractor = TextExtractor(**(extractor_kwargs or {}))
        self.cleaner = DocumentCleaner(**(cleaner_kwargs or {})) if enable_cleaning else None
        
        self.logger = get_logger(__name__)
    
    def process_document(
        self,
        input_path: Path,
        source: str,
        preserve_structure: bool = True,
    ) -> ProcessingResult:
        """
        Process a single document.
        
        Args:
            input_path: Path to input document
            source: Source name (e.g., 'MedQuAD', 'PubMed')
            preserve_structure: Preserve directory structure
            
        Returns:
            ProcessingResult
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Processing document: {input_path}")
            
            # Step 1: Extract text
            extraction_result = self.extractor.extract(input_path)
            
            if extraction_result.status == ExtractionStatus.FAILED:
                return ProcessingResult(
                    status='failed',
                    input_path=input_path,
                    extraction_status=extraction_result.status.value,
                    error_message=extraction_result.error_message,
                    processing_time_seconds=time.time() - start_time
                )
            
            if extraction_result.status == ExtractionStatus.EMPTY:
                self.logger.warning(f"No text extracted from {input_path}")
                return ProcessingResult(
                    status='failed',
                    input_path=input_path,
                    extraction_status=extraction_result.status.value,
                    error_message="No text extracted",
                    processing_time_seconds=time.time() - start_time
                )
            
            # Step 2: Clean text (if enabled)
            final_text = extraction_result.text
            cleaning_result = None
            
            if self.enable_cleaning and self.cleaner:
                cleaning_result = self.cleaner.clean(extraction_result.text)
                final_text = cleaning_result.cleaned_text
            
            # Step 3: Determine output path
            output_path = self._get_output_path(input_path, preserve_structure)
            
            # Step 4: Write output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_text)
            
            # Step 5: Generate metadata
            metadata = self._generate_metadata(
                input_path=input_path,
                output_path=output_path,
                source=source,
                extraction_result=extraction_result,
                cleaning_result=cleaning_result
            )
            
            # Step 6: Save metadata
            metadata_path = self._save_metadata(output_path, metadata)
            
            processing_time = time.time() - start_time
            
            self.logger.info(
                f"Successfully processed {input_path.name} "
                f"({extraction_result.char_count} chars, {processing_time:.2f}s)"
            )
            
            status = 'partial' if extraction_result.status == ExtractionStatus.PARTIAL else 'success'
            
            return ProcessingResult(
                status=status,
                input_path=input_path,
                output_path=output_path,
                metadata_path=metadata_path,
                extraction_status=extraction_result.status.value,
                cleaning_applied=self.enable_cleaning,
                processing_time_seconds=processing_time,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error processing document {input_path}: {e}")
            return ProcessingResult(
                status='failed',
                input_path=input_path,
                error_message=str(e),
                processing_time_seconds=time.time() - start_time
            )
    
    def process_batch(
        self,
        input_paths: list[Path],
        source: str,
        preserve_structure: bool = True,
        show_progress: bool = True,
    ) -> list[ProcessingResult]:
        """
        Process multiple documents.
        
        Args:
            input_paths: List of input paths
            source: Source name
            preserve_structure: Preserve directory structure
            show_progress: Show progress bar
            
        Returns:
            List of ProcessingResult objects
        """
        results = []
        
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(input_paths, desc=f"Processing {source}")
            except ImportError:
                iterator = input_paths
        else:
            iterator = input_paths
        
        for input_path in iterator:
            result = self.process_document(input_path, source, preserve_structure)
            results.append(result)
        
        # Log summary
        successful = sum(1 for r in results if r.status == 'success')
        partial = sum(1 for r in results if r.status == 'partial')
        failed = sum(1 for r in results if r.status == 'failed')
        
        self.logger.info(
            f"Batch processing complete: {successful} success, "
            f"{partial} partial, {failed} failed"
        )
        
        return results
    
    def _get_output_path(self, input_path: Path, preserve_structure: bool) -> Path:
        """Determine output path for processed document."""
        if preserve_structure:
            # Try to preserve relative path structure
            output_path = self.output_dir / input_path.name
        else:
            output_path = self.output_dir / input_path.name
        
        # Change extension to .txt
        output_path = output_path.with_suffix('.txt')
        
        # Handle name conflicts
        if output_path.exists():
            base = output_path.stem
            suffix = output_path.suffix
            counter = 1
            while output_path.exists():
                output_path = output_path.parent / f"{base}_{counter}{suffix}"
                counter += 1
        
        return output_path
    
    def _generate_metadata(
        self,
        input_path: Path,
        output_path: Path,
        source: str,
        extraction_result,
        cleaning_result,
    ) -> Dict[str, Any]:
        """Generate metadata for processed document."""
        metadata = {
            # Basic info
            'filename': output_path.name,
            'original_filename': input_path.name,
            'source': source,
            'processing_date': datetime.now().isoformat(),
            
            # Paths
            'input_path': str(input_path),
            'output_path': str(output_path),
            
            # File info
            'original_size_bytes': get_file_size(input_path),
            'processed_size_bytes': get_file_size(output_path),
            'original_extension': input_path.suffix,
            
            # Extraction info
            'extraction_status': extraction_result.status.value,
            'extraction_method': extraction_result.method,
            'extraction_time_seconds': extraction_result.extraction_time_seconds,
            'char_count': extraction_result.char_count,
            'word_count': extraction_result.word_count,
        }
        
        # Add page count if available
        if extraction_result.page_count:
            metadata['page_count'] = extraction_result.page_count
        
        # Add cleaning info if applied
        if cleaning_result:
            metadata['cleaning_applied'] = True
            metadata['cleaning_reduction_percent'] = cleaning_result.reduction_percent
            metadata['cleaning_operations'] = cleaning_result.operations_applied
        else:
            metadata['cleaning_applied'] = False
        
        # Add checksum
        metadata['checksum'] = compute_file_hash(output_path, algorithm='sha256')
        metadata['checksum_algorithm'] = 'sha256'
        
        return metadata
    
    def _save_metadata(self, output_path: Path, metadata: Dict[str, Any]) -> Path:
        """Save metadata to JSON file."""
        metadata_path = self.metadata_dir / f"{output_path.stem}.json"
        
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return metadata_path
