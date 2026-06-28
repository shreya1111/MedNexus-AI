"""
MedQuAD downloader for MedNexus-AI Knowledge Ingestion Framework.

Downloads the MedQuAD medical question-answering dataset from GitHub.
"""

from pathlib import Path
from typing import List, Dict, Any
import time

from .base_downloader import BaseDownloader, DownloadResult, DownloadStatus

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


class MedQuADDownloader(BaseDownloader):
    """Downloader for MedQuAD dataset (GitHub repository)."""
    
    REPO_URL = "https://github.com/abachaa/MedQuAD.git"
    
    def __init__(self, output_dir: Path, metadata_dir: Path, **kwargs):
        """
        Initialize MedQuAD downloader.
        
        Args:
            output_dir: Directory to save downloaded files
            metadata_dir: Directory to save metadata
            **kwargs: Additional arguments for BaseDownloader
        """
        super().__init__(output_dir, metadata_dir, **kwargs)
        
        if not GIT_AVAILABLE:
            self.logger.error("GitPython not installed. Run: pip install gitpython")
    
    def get_source_name(self) -> str:
        """Get source name."""
        return "MedQuAD"
    
    def get_download_list(self) -> List[Dict[str, Any]]:
        """
        Get list of items to download.
        
        For MedQuAD, we clone the entire repository.
        
        Returns:
            List with single item (the repository)
        """
        return [{
            'url': self.REPO_URL,
            'filename': 'medquad_repo',
            'description': 'MedQuAD GitHub repository',
        }]
    
    def download_file(self, url: str, output_path: Path, **kwargs) -> DownloadResult:
        """
        Download (clone) the MedQuAD repository.
        
        Args:
            url: Repository URL
            output_path: Output directory path
            **kwargs: Additional arguments
            
        Returns:
            DownloadResult
        """
        if not GIT_AVAILABLE:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error_message="GitPython not installed"
            )
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Cloning MedQuAD repository to {output_path}")
            
            # Check if already cloned
            if output_path.exists() and (output_path / '.git').exists():
                self.logger.info("Repository already exists, pulling latest changes")
                repo = git.Repo(output_path)
                origin = repo.remotes.origin
                origin.pull()
                status = DownloadStatus.RESUMED
            else:
                # Clone repository
                git.Repo.clone_from(
                    url,
                    output_path,
                    progress=None  # Could add custom progress handler
                )
                status = DownloadStatus.COMPLETED
            
            # Calculate size
            total_size = sum(
                f.stat().st_size for f in output_path.rglob('*') if f.is_file()
            )
            
            elapsed_time = time.time() - start_time
            
            self.logger.info(
                f"Successfully cloned MedQuAD repository "
                f"({total_size / (1024*1024):.2f} MB in {elapsed_time:.2f}s)"
            )
            
            return DownloadResult(
                status=status,
                file_path=output_path,
                size_bytes=total_size,
                download_time_seconds=elapsed_time,
                metadata={
                    'repository_url': url,
                    'clone_method': 'git',
                }
            )
            
        except git.GitCommandError as e:
            self.logger.error(f"Git error cloning repository: {e}")
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error_message=f"Git error: {str(e)}",
                download_time_seconds=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error cloning repository: {e}")
            return DownloadResult(
                status=DownloadStatus.FAILED,
                error_message=str(e),
                download_time_seconds=time.time() - start_time
            )
