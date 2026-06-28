"""
PubMed downloader placeholder for MedNexus-AI Knowledge Ingestion Framework.

This is a framework placeholder. Actual implementation in Phase 2B.
"""

from pathlib import Path
from typing import List, Dict, Any

from .base_downloader import BaseDownloader, DownloadResult, DownloadStatus


class PubMedDownloader(BaseDownloader):
    """Downloader for PubMed Central and PubMed datasets (placeholder)."""
    
    def get_source_name(self) -> str:
        return "PubMed"
    
    def get_download_list(self) -> List[Dict[str, Any]]:
        self.logger.warning("PubMed downloader not yet implemented (placeholder)")
        return []
    
    def download_file(self, url: str, output_path: Path, **kwargs) -> DownloadResult:
        return DownloadResult(
            status=DownloadStatus.FAILED,
            error_message="Not implemented (placeholder)",
        )
