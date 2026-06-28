"""
Document cleaning module for MedNexus-AI Knowledge Ingestion Framework.

Cleans extracted text while preserving structure and meaningful content.
"""

from pathlib import Path
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass
import re
import unicodedata

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger

try:
    import ftfy
    FTFY_AVAILABLE = True
except ImportError:
    FTFY_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class CleaningResult:
    """Result of document cleaning operation."""
    cleaned_text: str
    original_length: int
    cleaned_length: int
    reduction_percent: float
    operations_applied: list
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DocumentCleaner:
    """Cleans extracted text while preserving structure."""
    
    def __init__(
        self,
        remove_excessive_whitespace: bool = True,
        normalize_unicode: bool = True,
        remove_duplicate_lines: bool = True,
        preserve_structure: bool = True,
        min_line_length: int = 2,
        max_consecutive_newlines: int = 3,
    ):
        """
        Initialize document cleaner.
        
        Args:
            remove_excessive_whitespace: Remove extra spaces and tabs
            normalize_unicode: Normalize Unicode characters
            remove_duplicate_lines: Remove consecutive duplicate lines
            preserve_structure: Preserve headings, lists, and tables
            min_line_length: Minimum line length to keep
            max_consecutive_newlines: Maximum consecutive blank lines
        """
        self.remove_excessive_whitespace = remove_excessive_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_duplicate_lines = remove_duplicate_lines
        self.preserve_structure = preserve_structure
        self.min_line_length = min_line_length
        self.max_consecutive_newlines = max_consecutive_newlines
        self.logger = get_logger(__name__)
    
    def clean(self, text: str) -> CleaningResult:
        """
        Clean document text.
        
        Args:
            text: Text to clean
            
        Returns:
            CleaningResult
        """
        original_length = len(text)
        operations = []
        
        cleaned = text
        
        # 1. Fix Unicode issues
        if self.normalize_unicode:
            if FTFY_AVAILABLE:
                cleaned = ftfy.fix_text(cleaned)
                operations.append("fix_unicode_ftfy")
            else:
                cleaned = self._normalize_unicode(cleaned)
                operations.append("normalize_unicode_manual")
        
        # 2. Normalize line endings
        cleaned = self._normalize_line_endings(cleaned)
        operations.append("normalize_line_endings")
        
        # 3. Remove excessive whitespace
        if self.remove_excessive_whitespace:
            cleaned = self._remove_excessive_whitespace(cleaned)
            operations.append("remove_excessive_whitespace")
        
        # 4. Remove duplicate lines
        if self.remove_duplicate_lines:
            cleaned = self._remove_duplicate_lines(cleaned)
            operations.append("remove_duplicate_lines")
        
        # 5. Remove very short lines (likely artifacts)
        cleaned = self._remove_short_lines(cleaned, self.min_line_length)
        operations.append("remove_short_lines")
        
        # 6. Limit consecutive newlines
        cleaned = self._limit_consecutive_newlines(cleaned, self.max_consecutive_newlines)
        operations.append("limit_newlines")
        
        # 7. Final cleanup
        cleaned = cleaned.strip()
        
        cleaned_length = len(cleaned)
        reduction_percent = ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0
        
        return CleaningResult(
            cleaned_text=cleaned,
            original_length=original_length,
            cleaned_length=cleaned_length,
            reduction_percent=reduction_percent,
            operations_applied=operations,
            metadata={
                'lines_before': text.count('\n'),
                'lines_after': cleaned.count('\n'),
            }
        )
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters."""
        # Normalize to NFC form (composed)
        text = unicodedata.normalize('NFC', text)
        
        # Replace common problematic characters
        replacements = {
            '\u00A0': ' ',  # Non-breaking space
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201C': '"',  # Left double quote
            '\u201D': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...',# Ellipsis
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _normalize_line_endings(self, text: str) -> str:
        """Normalize line endings to \n."""
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        return text
    
    def _remove_excessive_whitespace(self, text: str) -> str:
        """Remove excessive whitespace."""
        lines = []
        
        for line in text.split('\n'):
            # Replace tabs with spaces
            line = line.replace('\t', ' ')
            
            # Replace multiple spaces with single space
            line = re.sub(r' {2,}', ' ', line)
            
            # Strip leading/trailing whitespace
            line = line.strip()
            
            lines.append(line)
        
        return '\n'.join(lines)
    
    def _remove_duplicate_lines(self, text: str) -> str:
        """Remove consecutive duplicate lines."""
        lines = text.split('\n')
        cleaned_lines = []
        prev_line = None
        
        for line in lines:
            # Keep line if it's different from previous or if it's empty
            if line != prev_line or not line.strip():
                cleaned_lines.append(line)
                prev_line = line if line.strip() else None
        
        return '\n'.join(cleaned_lines)
    
    def _remove_short_lines(self, text: str, min_length: int) -> str:
        """Remove very short lines that are likely artifacts."""
        lines = []
        
        for line in text.split('\n'):
            # Keep empty lines (for structure)
            if not line.strip():
                lines.append(line)
                continue
            
            # Keep lines that look like headers/lists
            if self.preserve_structure and self._is_structural_element(line):
                lines.append(line)
                continue
            
            # Keep lines longer than minimum
            if len(line.strip()) >= min_length:
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _is_structural_element(self, line: str) -> bool:
        """Check if line is a structural element (heading, list, etc.)."""
        stripped = line.strip()
        
        # Markdown headings
        if stripped.startswith('#'):
            return True
        
        # Numbered lists
        if re.match(r'^\d+[\.\)]\s', stripped):
            return True
        
        # Bullet lists
        if re.match(r'^[-*•]\s', stripped):
            return True
        
        # All caps headings
        if stripped.isupper() and len(stripped) < 100:
            return True
        
        return False
    
    def _limit_consecutive_newlines(self, text: str, max_newlines: int) -> str:
        """Limit consecutive newlines."""
        pattern = r'\n{' + str(max_newlines + 1) + r',}'
        replacement = '\n' * max_newlines
        return re.sub(pattern, replacement, text)
    
    def clean_file(
        self,
        input_path: Path,
        output_path: Path,
        encoding: str = 'utf-8'
    ) -> CleaningResult:
        """
        Clean a text file.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            encoding: Text encoding
            
        Returns:
            CleaningResult
        """
        try:
            # Read input
            with open(input_path, 'r', encoding=encoding, errors='replace') as f:
                text = f.read()
            
            # Clean
            result = self.clean(text)
            
            # Write output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.cleaned_text)
            
            self.logger.info(
                f"Cleaned {input_path.name}: "
                f"{result.original_length} -> {result.cleaned_length} chars "
                f"({result.reduction_percent:.1f}% reduction)"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error cleaning file {input_path}: {e}")
            raise
