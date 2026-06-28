"""
Base downloader class for MedNexus-AI Knowledge Ingestion Framework.

Provides abstract base class for all downloaders with common functionality:
- Retry logic
- Resume capability
- Duplicate detection
- Checksum verification
- Metadata generation
- Progress tracking
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.hash_utils import compute_file_hash, verify_checksum
from utils.file_utils import get_file_size, get_file_metadata, ensure_directory
from utils.retry import RetryConfig, RetryManager
from utils.progress import ProgressTracker


logger = get_logger(__name__)


class DownloadStatus(Enum):
    """Status of download operation."""
    
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RESUMED = "resumed"


@dataclass
class DownloadResult:
    """Result of a download operation."""
    
    status: DownloadStatus
    file_path: Optional[Path] = None
    checksum: Optional[str] = None
    size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    download_time_seconds: float = 0.0
    attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "file_path": str(self.file_path) if self.file_path else None,
            "checksum": self.checksum,
            "size_bytes": self.size_bytes,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "download_time_seconds": self.download_time_seconds,
            "attempts": self.attempts,
        }


class BaseDownloader(ABC):
    """
    Abstract base class for all downloaders.
    
    Provides common functionality and enforces interface for specific downloaders.
    """
    
    def __init__(
        self,
        output_dir: Path,
        metadata_dir: Path,
        retry_config: Optional[RetryConfig] = None,
        verify_checksums: bool = True,
        skip_existing: bool = True,
    ):
        """
        Initialize base downloader.
        
        Args:
            output_dir: Directory to save downloaded files
            metadata_dir: Directory to save metadata
            retry_config: Retry configuration
            verify_checksums: Whether to verify file checksums
            skip_existing: Whether to skip already downloaded files
        """
        self.output_dir = ensure_directory(output_dir)
        self.metadata_dir = ensure_directory(metadata_dir)
        self.verify_checksums = verify_checksums
        self.skip_existing = skip_existing
        
        self.retry_config = retry_config or RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            backoff_multiplier=2.0,
            max_delay=60.0,
        )
        
        self.retry_manager = RetryManager(self.retry_config)
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get the name of the data source.
        
        Returns:
            Source name (e.g., 'MedQuAD', 'PubMed')
        """
        pass
    
    @abstractmethod
    def get_download_list(self) -> List[Dict[str, Any]]:
        """
        Get list of items to download.
        
        Returns:
            List of dictionaries containing download information.
            Each dict should have at least 'url' and 'filename' keys.
        """
        pass
    
    @abstractmethod
    def download_file(
        self,
        url: str,
        output_path: Path,
        **kwargs
    ) -> DownloadResult:
        """
        Download a single file.
        
        Args:
            url: URL to download from
            output_path: Path to save file
            **kwargs: Additional downloader-specific arguments
            
        Returns:
            DownloadResult with status and metadata
        """
        pass
    
    def should_download(self, file_path: Path, expected_checksum: Optional[str] = None) -> bool:
        """
        Check if file should be downloaded.
        
        Args:
            file_path: Path to check
            expected_checksum: Expected checksum (if known)
            
        Returns:
            True if file should be downloaded
        """
        # File doesn't exist
        if not file_path.exists():
            return True
        
        # Skip existing is disabled
        if not self.skip_existing:
            return True
        
        # Check if file is empty or corrupt
        try:
            size = get_file_size(file_path)
            if size == 0:
                self.logger.warning(f"File exists but is empty: {file_path}")
                return True
        except Exception as e:
            self.logger.error(f"Error checking file: {e}")
            return True
        
        # Verify checksum if provided
        if expected_checksum and self.verify_checksums:
            if not verify_checksum(file_path, expected_checksum):
                self.logger.warning(f"File exists but checksum mismatch: {file_path}")
                return True
        
        self.logger.debug(f"File already exists and is valid: {file_path}")
        return False
    
    def generate_metadata(
        self,
        file_path: Path,
        download_result: DownloadResult,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate metadata for downloaded file.
        
        Args:
            file_path: Path to downloaded file
            download_result: Download result
            additional_metadata: Additional metadata to include
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "filename": file_path.name,
            "source": self.get_source_name(),
            "download_date": datetime.now().isoformat(),
            "file_path": str(file_path),
            "status": download_result.status.value,
        }
        
        # Add file metadata if file exists
        if file_path.exists():
            try:
                file_meta = get_file_metadata(file_path)
                metadata.update({
                    "file_size_bytes": file_meta["size_bytes"],
                    "file_size_mb": file_meta["size_mb"],
                    "extension": file_meta["extension"],
                })
                
                # Add checksum
                if self.verify_checksums:
                    checksum = compute_file_hash(file_path, algorithm="sha256")
                    metadata["checksum"] = checksum
                    metadata["checksum_algorithm"] = "sha256"
                    
            except Exception as e:
                self.logger.error(f"Error generating file metadata: {e}")
        
        # Add download result metadata
        metadata.update(download_result.metadata)
        
        # Add additional metadata
        if additional_metadata:
            metadata.update(additional_metadata)
        
        # Add error if failed
        if download_result.status == DownloadStatus.FAILED:
            metadata["error_message"] = download_result.error_message
        
        return metadata
    
    def save_metadata(self, metadata: Dict[str, Any], filename: str) -> Path:
        """
        Save metadata to JSON file.
        
        Args:
            metadata: Metadata dictionary
            filename: Filename for metadata (without extension)
            
        Returns:
            Path to saved metadata file
        """
        metadata_path = self.metadata_dir / f"{filename}.json"
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved metadata to: {metadata_path}")
            return metadata_path
            
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
            raise
    
    def load_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load metadata from JSON file.
        
        Args:
            filename: Filename for metadata (without extension)
            
        Returns:
            Metadata dictionary or None if not found
        """
        metadata_path = self.metadata_dir / f"{filename}.json"
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading metadata: {e}")
            return None
    
    def download_all(
        self,
        max_files: Optional[int] = None,
        show_progress: bool = True,
    ) -> List[DownloadResult]:
        """
        Download all files from source.
        
        Args:
            max_files: Maximum number of files to download (None = all)
            show_progress: Whether to show progress bar
            
        Returns:
            List of DownloadResult objects
        """
        download_list = self.get_download_list()
        
        if max_files:
            download_list = download_list[:max_files]
        
        self.logger.info(
            f"Starting download of {len(download_list)} files from {self.get_source_name()}"
        )
        
        results = []
        
        if show_progress:
            progress = ProgressTracker(
                total=len(download_list),
                description=f"Downloading from {self.get_source_name()}",
            )
        
        for item in download_list:
            url = item.get('url')
            filename = item.get('filename')
            
            if not url or not filename:
                self.logger.error(f"Invalid download item: {item}")
                continue
            
            output_path = self.output_dir / filename
            
            # Check if should download
            if not self.should_download(output_path, item.get('checksum')):
                result = DownloadResult(
                    status=DownloadStatus.SKIPPED,
                    file_path=output_path,
                )
                results.append(result)
                
                if show_progress:
                    progress.skip()
                
                continue
            
            # Download file
            try:
                result = self.retry_manager.execute(
                    self.download_file,
                    url=url,
                    output_path=output_path,
                    **item
                )
                
                # Generate and save metadata
                metadata = self.generate_metadata(output_path, result, item)
                self.save_metadata(metadata, output_path.stem)
                
                results.append(result)
                
                if show_progress:
                    progress.update(success=(result.status == DownloadStatus.COMPLETED))
                
            except Exception as e:
                self.logger.error(f"Failed to download {url}: {e}")
                
                result = DownloadResult(
                    status=DownloadStatus.FAILED,
                    error_message=str(e),
                    attempts=self.retry_config.max_attempts,
                )
                results.append(result)
                
                if show_progress:
                    progress.fail()
        
        if show_progress:
            progress.finish()
        
        # Log summary
        successful = sum(1 for r in results if r.status == DownloadStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == DownloadStatus.FAILED)
        skipped = sum(1 for r in results if r.status == DownloadStatus.SKIPPED)
        
        self.logger.info(
            f"Download complete: {successful} successful, {failed} failed, {skipped} skipped"
        )
        
        return results
    
    def get_download_stats(self, results: List[DownloadResult]) -> Dict[str, Any]:
        """
        Calculate download statistics.
        
        Args:
            results: List of download results
            
        Returns:
            Statistics dictionary
        """
        total = len(results)
        completed = sum(1 for r in results if r.status == DownloadStatus.COMPLETED)
        failed = sum(1 for r in results if r.status == DownloadStatus.FAILED)
        skipped = sum(1 for r in results if r.status == DownloadStatus.SKIPPED)
        
        total_size = sum(
            r.size_bytes for r in results
            if r.size_bytes and r.status == DownloadStatus.COMPLETED
        )
        
        total_time = sum(r.download_time_seconds for r in results)
        
        return {
            "source": self.get_source_name(),
            "total_files": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": completed / total if total > 0 else 0,
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_time_seconds": total_time,
        }
