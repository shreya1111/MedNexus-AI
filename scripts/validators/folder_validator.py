"""
Folder structure validation for MedNexus-AI Knowledge Ingestion Framework.
"""

from pathlib import Path
from typing import List, Dict
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class FolderValidator:
    """Validates folder structure."""
    
    def __init__(self, required_folders: List[Path]):
        self.required_folders = required_folders
        self.logger = logger
    
    def validate(self) -> Dict[str, bool]:
        """Validate all required folders exist."""
        results = {}
        for folder in self.required_folders:
            exists = folder.exists() and folder.is_dir()
            results[str(folder)] = exists
            if not exists:
                self.logger.warning(f"Missing folder: {folder}")
        return results
