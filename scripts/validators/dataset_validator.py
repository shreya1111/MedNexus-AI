"""
Dataset validation for MedNexus-AI Knowledge Ingestion Framework.

Validates downloaded datasets for integrity, completeness, and quality.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger
from utils.file_utils import (
    list_files_recursive,
    get_file_size,
    is_empty_file,
    get_file_extension,
)
from utils.hash_utils import find_duplicate_files


logger = get_logger(__name__)


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'missing', 'duplicate', 'empty', 'invalid', etc.
    message: str
    file_path: Optional[Path] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file_path": str(self.file_path) if self.file_path else None,
            "details": self.details,
        }


@dataclass
class ValidationReport:
    """Report from dataset validation."""
    
    dataset_name: str
    validation_date: str
    total_files: int = 0
    valid_files: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_errors(self) -> bool:
        """Check if report contains errors."""
        return any(issue.severity == 'error' for issue in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        """Check if report contains warnings."""
        return any(issue.severity == 'warning' for issue in self.issues)
    
    @property
    def error_count(self) -> int:
        """Count errors."""
        return sum(1 for issue in self.issues if issue.severity == 'error')
    
    @property
    def warning_count(self) -> int:
        """Count warnings."""
        return sum(1 for issue in self.issues if issue.severity == 'warning')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "validation_date": self.validation_date,
            "total_files": self.total_files,
            "valid_files": self.valid_files,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [issue.to_dict() for issue in self.issues],
            "statistics": self.statistics,
        }
    
    def save(self, output_path: Path) -> None:
        """Save report to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)


class DatasetValidator:
    """Validates datasets for integrity and quality."""
    
    def __init__(
        self,
        check_duplicates: bool = True,
        check_empty_files: bool = True,
        check_file_naming: bool = True,
        min_file_size_bytes: int = 100,
        allowed_extensions: Optional[List[str]] = None,
    ):
        """
        Initialize dataset validator.
        
        Args:
            check_duplicates: Whether to check for duplicate files
            check_empty_files: Whether to check for empty files
            check_file_naming: Whether to validate file names
            min_file_size_bytes: Minimum acceptable file size
            allowed_extensions: List of allowed file extensions
        """
        self.check_duplicates = check_duplicates
        self.check_empty_files = check_empty_files
        self.check_file_naming = check_file_naming
        self.min_file_size_bytes = min_file_size_bytes
        self.allowed_extensions = allowed_extensions or [
            '.pdf', '.txt', '.md', '.json', '.xml', '.html', '.csv'
        ]
        
        self.logger = logger
    
    def validate_dataset(
        self,
        dataset_dir: Path,
        dataset_name: str,
    ) -> ValidationReport:
        """
        Validate a dataset directory.
        
        Args:
            dataset_dir: Directory containing dataset
            dataset_name: Name of dataset
            
        Returns:
            ValidationReport with findings
        """
        self.logger.info(f"Validating dataset: {dataset_name} at {dataset_dir}")
        
        report = ValidationReport(
            dataset_name=dataset_name,
            validation_date=datetime.now().isoformat(),
        )
        
        if not dataset_dir.exists():
            report.issues.append(ValidationIssue(
                severity='error',
                category='missing',
                message=f"Dataset directory does not exist: {dataset_dir}",
            ))
            return report
        
        # Get all files
        files = list(list_files_recursive(dataset_dir))
        report.total_files = len(files)
        
        self.logger.info(f"Found {len(files)} files to validate")
        
        # Check empty files
        if self.check_empty_files:
            self._check_empty_files(files, report)
        
        # Check file extensions
        self._check_file_extensions(files, report)
        
        # Check file naming
        if self.check_file_naming:
            self._check_file_naming(files, report)
        
        # Check for duplicates
        if self.check_duplicates:
            self._check_duplicates(dataset_dir, report)
        
        # Calculate statistics
        self._calculate_statistics(files, report)
        
        # Calculate valid files
        report.valid_files = report.total_files - report.error_count
        
        self.logger.info(
            f"Validation complete: {report.valid_files}/{report.total_files} valid files, "
            f"{report.error_count} errors, {report.warning_count} warnings"
        )
        
        return report
    
    def _check_empty_files(self, files: List[Path], report: ValidationReport) -> None:
        """Check for empty or too small files."""
        self.logger.debug("Checking for empty files...")
        
        for file_path in files:
            if is_empty_file(file_path, self.min_file_size_bytes):
                size = get_file_size(file_path)
                report.issues.append(ValidationIssue(
                    severity='warning',
                    category='empty',
                    message=f"File is empty or too small ({size} bytes)",
                    file_path=file_path,
                    details={"size_bytes": size, "min_required": self.min_file_size_bytes},
                ))
    
    def _check_file_extensions(self, files: List[Path], report: ValidationReport) -> None:
        """Check if file extensions are allowed."""
        self.logger.debug("Checking file extensions...")
        
        for file_path in files:
            ext = get_file_extension(file_path)
            if ext not in self.allowed_extensions:
                report.issues.append(ValidationIssue(
                    severity='warning',
                    category='invalid',
                    message=f"File extension not in allowed list: {ext}",
                    file_path=file_path,
                    details={
                        "extension": ext,
                        "allowed_extensions": self.allowed_extensions,
                    },
                ))
    
    def _check_file_naming(self, files: List[Path], report: ValidationReport) -> None:
        """Check if file names are valid."""
        self.logger.debug("Checking file naming conventions...")
        
        import re
        pattern = r'^[a-zA-Z0-9_-]+\.[a-zA-Z0-9]+$'
        
        for file_path in files:
            if not re.match(pattern, file_path.name):
                report.issues.append(ValidationIssue(
                    severity='info',
                    category='naming',
                    message="File name contains special characters",
                    file_path=file_path,
                    details={"filename": file_path.name},
                ))
    
    def _check_duplicates(self, dataset_dir: Path, report: ValidationReport) -> None:
        """Check for duplicate files based on hash."""
        self.logger.debug("Checking for duplicate files...")
        
        try:
            duplicates = find_duplicate_files(dataset_dir)
            
            for file_hash, paths in duplicates.items():
                report.issues.append(ValidationIssue(
                    severity='warning',
                    category='duplicate',
                    message=f"Found {len(paths)} duplicate files",
                    details={
                        "hash": file_hash,
                        "files": [str(p) for p in paths],
                        "count": len(paths),
                    },
                ))
        except Exception as e:
            self.logger.error(f"Error checking duplicates: {e}")
    
    def _calculate_statistics(self, files: List[Path], report: ValidationReport) -> None:
        """Calculate dataset statistics."""
        self.logger.debug("Calculating statistics...")
        
        total_size = 0
        extensions = {}
        
        for file_path in files:
            try:
                size = get_file_size(file_path)
                total_size += size
                
                ext = get_file_extension(file_path)
                extensions[ext] = extensions.get(ext, 0) + 1
                
            except Exception:
                continue
        
        report.statistics = {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "extensions": extensions,
            "average_file_size_bytes": total_size / len(files) if files else 0,
        }
