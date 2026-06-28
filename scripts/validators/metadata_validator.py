"""
Metadata validation for MedNexus-AI Knowledge Ingestion Framework.
"""

from pathlib import Path
from typing import Dict, List, Any
import json
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class MetadataValidator:
    """Validates metadata files."""
    
    def __init__(self, required_fields: List[str]):
        self.required_fields = required_fields
        self.logger = logger
    
    def validate_file(self, metadata_path: Path) -> Dict[str, Any]:
        """Validate a single metadata file."""
        if not metadata_path.exists():
            return {"valid": False, "error": "File not found"}
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            missing = [f for f in self.required_fields if f not in metadata]
            
            return {
                "valid": len(missing) == 0,
                "missing_fields": missing,
                "metadata": metadata,
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
