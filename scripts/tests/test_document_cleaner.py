"""
Unit tests for document cleaning module.
"""

import pytest
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from processors.document_cleaner import DocumentCleaner


class TestDocumentCleaner:
    """Test cases for DocumentCleaner."""
    
    @pytest.fixture
    def cleaner(self):
        """Create DocumentCleaner instance."""
        return DocumentCleaner()
    
    def test_remove_excessive_whitespace(self, cleaner):
        """Test removing excessive whitespace."""
        text = "This  has    too   many     spaces.\n"
        result = cleaner.clean(text)
        
        assert "too many spaces" in result.cleaned_text
        assert "    " not in result.cleaned_text
    
    def test_normalize_line_endings(self, cleaner):
        """Test normalizing line endings."""
        text = "Line 1\r\nLine 2\rLine 3\n"
        result = cleaner.clean(text)
        
        assert "\r" not in result.cleaned_text
        assert result.cleaned_text.count("\n") == 2
    
    def test_remove_duplicate_lines(self, cleaner):
        """Test removing consecutive duplicate lines."""
        text = "Line 1\nLine 1\nLine 2\nLine 2\nLine 2\nLine 3\n"
        result = cleaner.clean(text)
        
        # Count occurrences of "Line 1"
        line1_count = result.cleaned_text.count("Line 1")
        assert line1_count == 1
    
    def test_limit_consecutive_newlines(self, cleaner):
        """Test limiting consecutive newlines."""
        text = "Paragraph 1\n\n\n\n\n\nParagraph 2\n"
        result = cleaner.clean(text)
        
        # Should limit to max 3 consecutive newlines
        assert "\n\n\n\n" not in result.cleaned_text
    
    def test_preserve_structure(self, cleaner):
        """Test preserving structural elements."""
        text = "# Heading\n\n1. Item one\n2. Item two\n\n- Bullet\n"
        result = cleaner.clean(text)
        
        assert "# Heading" in result.cleaned_text
        assert "1. Item one" in result.cleaned_text
        assert "- Bullet" in result.cleaned_text
    
    def test_unicode_normalization(self, cleaner):
        """Test Unicode normalization."""
        # Test common problematic characters
        text = "café\u00A0 —test— "it's" …\n"
        result = cleaner.clean(text)
        
        # Non-breaking space should be regular space
        assert "\u00A0" not in result.cleaned_text
    
    def test_empty_text(self, cleaner):
        """Test cleaning empty text."""
        result = cleaner.clean("")
        
        assert result.cleaned_text == ""
        assert result.cleaned_length == 0
    
    def test_reduction_calculation(self, cleaner):
        """Test reduction percentage calculation."""
        text = "Text  with    extra     spaces\n\n\n\n\n"
        result = cleaner.clean(text)
        
        assert result.original_length > result.cleaned_length
        assert result.reduction_percent > 0
        assert result.reduction_percent <= 100
    
    def test_operations_applied(self, cleaner):
        """Test that operations are tracked."""
        text = "Some text\n"
        result = cleaner.clean(text)
        
        assert len(result.operations_applied) > 0
        assert "normalize_line_endings" in result.operations_applied


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
