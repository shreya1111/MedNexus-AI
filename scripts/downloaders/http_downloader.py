"""
HTTP downloader base class for MedNexus-AI Knowledge Ingestion Framework.

Provides common HTTP download functionality with resume, progress, and retry support.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import time

from .base_downloader import BaseDownloader, DownloadResult, DownloadStatus

try:
    import requests
    from tqdm import tqdm
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False


class HTTPDownloader(BaseDownloader):
    """Base class for HTTP-based downloaders with resume and progress support."""
    
    def __init__(
        self,
        output_dir: Path,
        metadata_dir: Path,
        user_agent: Optional[str] = None,
        timeout: int = 300,
        **kwargs
    ):
        """
        Initialize HTTP downloader.
        
        Args:
            output_dir: Directory to save downloaded files
            metadata_dir: Directory to save metadata
            user_agent: Custom user agent string
            timeout: Request timeout in seconds
            **kwargs: Additional arguments for BaseDownloader
        """
        super().__init__(output_dir, metadata_dir, **kwargs)
        
        self.user_agent = user_agent or "MedNexus-AI-KnowledgeBot/1.0"
        self.timeout = timeout
        
        if not DEPS_AVAILABLE:
            self.logger.error(
                "Required packages not installed. Run: pip install requests tqdm"
            )
    
    def download_http_file(
        self,
        url: str,
        output_path: Path,
        resume: bool = True,
        show_progress: bool = True,
    ) -> DownloadResult:
        """
        Download a file via HTTP with resume and progress support.
        
        Args:
            url: URL to download
            output_path: Path to save file
            resume: Whether to resume interrupted downloads
            show_progress: Whether to show progress bar
            
        Returns:
            DownloadResult
        """
        if not DEPS_AVAILABLE:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error_message="requests or tqdm not installed"
            )
        
        start_time = time.time()
        
        try:
            # Prepare headers
            headers = {
                'User-Agent': self.user_agent
            }
            
            # Check if file exists and get resume position
            resume_pos = 0
            mode = 'wb'
            
            if resume and output_path.exists():
                resume_pos = output_path.stat().st_size
                headers['Range'] = f'bytes={resume_pos}-'
                mode = 'ab'
                self.logger.info(f"Resuming download from byte {resume_pos}")
            
            # Make request
            response = requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Check if resume is supported
            if resume_pos > 0 and response.status_code not in [206, 200]:
                self.logger.warning(
                    f"Resume not supported (status {response.status_code}), "
                    "starting from beginning"
                )
                resume_pos = 0
                mode = 'wb'
                response = requests.get(
                    url,
                    headers={'User-Agent': self.user_agent},
                    stream=True,
                    timeout=self.timeout,
                    allow_redirects=True
                )
            
            response.raise_for_status()
            
            # Get total size
            total_size = int(response.headers.get('content-length', 0))
            if resume_pos > 0:
                total_size += resume_pos
            
            # Download with progress bar
            chunk_size = 8192
            downloaded = resume_pos
            
            progress_bar = None
            if show_progress and total_size > 0:
                progress_bar = tqdm(
                    total=total_size,
                    initial=resume_pos,
                    unit='B',
                    unit_scale=True,
                    desc=output_path.name
                )
            
            with open(output_path, mode) as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_bar:
                            progress_bar.update(len(chunk))
            
            if progress_bar:
                progress_bar.close()
            
            elapsed_time = time.time() - start_time
            
            # Calculate download speed
            download_speed_mbps = (downloaded / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
            
            self.logger.info(
                f"Downloaded {url} ({downloaded / (1024*1024):.2f} MB "
                f"in {elapsed_time:.2f}s, {download_speed_mbps:.2f} MB/s)"
            )
            
            status = DownloadStatus.RESUMED if resume_pos > 0 else DownloadStatus.COMPLETED
            
            return DownloadResult(
                status=status,
                file_path=output_path,
                size_bytes=downloaded,
                download_time_seconds=elapsed_time,
                metadata={
                    'url': url,
                    'download_speed_mbps': download_speed_mbps,
                    'resumed_from_byte': resume_pos if resume_pos > 0 else None,
                }
            )
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP error downloading {url}: {e}")
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error_message=f"HTTP error: {str(e)}",
                download_time_seconds=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error downloading {url}: {e}")
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error_message=str(e),
                download_time_seconds=time.time() - start_time
            )
    
    def download_file(self, url: str, output_path: Path, **kwargs) -> DownloadResult:
        """
        Download a single file (delegates to download_http_file).
        
        Args:
            url: URL to download
            output_path: Path to save file
            **kwargs: Additional arguments
            
        Returns:
            DownloadResult
        """
        return self.download_http_file(
            url,
            output_path,
            resume=kwargs.get('resume', True),
            show_progress=kwargs.get('show_progress', True)
        )
