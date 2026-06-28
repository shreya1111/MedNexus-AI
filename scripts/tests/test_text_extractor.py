"""
Unit tests for text extraction module.
"""

import pytest
from pathlib import Path
import tempfile
import os

import sys
sys.path.append(str(Path(__file__).parent.parent))

from processors.text_extractor import TextExtractor, ExtractionStatus


class TestTextExtractor:
    """Test cases for TextExtractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create TextExtractor instance."""
        return TextExtractor()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_extract_plain_text(self, extractor, temp_dir):
        """Test extracting from plain text file."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_content = "This is a test document.\nIt has multiple lines.\n"
        test_file.write_text(test_content, encoding='utf-8')
        
        # Extract
        result = extractor.extract(test_file)
        
        # Verify
        assert result.status == ExtractionStatus.SUCCESS
        assert result.text == test_content
        assert result.char_count == len(test_content)
        assert result.word_count > 0
        assert result.method == "text"
    
    def test_extract_markdown(self, extractor, temp_dir):
        """Test extracting from Markdown file."""
        # Create test file
        test_file = temp_dir / "test.md"
        test_content = "# Heading\n\nThis is **bold** text.\n"
        test_file.write_text(test_content, encoding='utf-8')
        
        # Extract
        result = extractor.extract(test_file)
        
        # Verify
        assert result.status == ExtractionStatus.SUCCESS
        assert result.text == test_content
        assert result.method == "markdown"
    
    def test_extract_empty_file(self, extractor, temp_dir):
        """Test extracting from empty file."""
        # Create empty file
        test_file = temp_dir / "empty.txt"
        test_file.write_text("", encoding='utf-8')
        
        # Extract
        result = extractor.extract(test_file)
        
        # Verify
        assert result.status == ExtractionStatus.EMPTY
        assert result.text == ""
    
    def test_extract_nonexistent_file(self, extractor, temp_dir):
        """Test extracting from nonexistent file."""
        test_file = temp_dir / "nonexistent.txt"
        
        # Extract
        result = extractor.extract(test_file)
        
        # Verify
        assert result.status == ExtractionStatus.FAILED
        assert "not found" in result.error_message.lower()
    
    def test_extract_unsupported_format(self, extractor, temp_dir):
        """Test extracting from unsupported file format."""
        test_file = temp_dir / "test.xyz"
        test_file.write_text("content", encoding='utf-8')
        
        # Extract
        result = extractor.extract(test_file)
        
        # Verify
        assert result.status == ExtractionStatus.UNSUPPORTED
    
    def test_extract_unicode_text(self, extractor, temp_dir):
        """Test extracting Unicode text."""
        # Create file with Unicode
        test_file = temp_dir / "unicode.txt"
        test_content = "Unicode: café, naïve, 日本語\n"
        test_file.write_text(test_content, encoding='utf-8')
        
        # Extract
        result = extractor.extract(test_file)
        
        # Verify
        assert result.status == ExtractionStatus.SUCCESS
        assert "café" in result.text
        assert "日本語" in result.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
