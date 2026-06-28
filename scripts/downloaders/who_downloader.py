"""
WHO Guidelines downloader placeholder for MedNexus-AI Knowledge Ingestion Framework.

This is a framework placeholder. Actual implementation in Phase 2B.
"""

from pathlib import Path
from typing import List, Dict, Any

from .base_downloader import BaseDownloader, DownloadResult, DownloadStatus


class WHODownloader(BaseDownloader):
    """Downloader for WHO Clinical Guidelines (placeholder)."""
    
    def get_source_name(self) -> str:
        return "WHO_Guidelines"
    
    def get_download_list(self) -> List[Dict[str, Any]]:
        self.logger.warning("WHO downloader not yet implemented (placeholder)")
        return []
    
    def download_file(self, url: str, output_path: Path, **kwargs) -> DownloadResult:
        return DownloadResult(
            status=DownloadStatus.FAILED,
            error_message="Not implemented (placeholder)",
        )
