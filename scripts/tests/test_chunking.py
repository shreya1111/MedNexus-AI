"""
Unit tests for chunking module.
"""

import pytest
from pathlib import Path
import tempfile
import json

import sys
sys.path.append(str(Path(__file__).parent.parent))

from chunkers.recursive_chunker import RecursiveChunker
from chunkers.fixed_chunker import FixedChunker
from chunkers.paragraph_chunker import ParagraphChunker
from chunkers.section_chunker import SectionChunker
from chunkers.base_chunker import Chunk


class TestRecursiveChunker:
    """Test cases for RecursiveChunker."""
    
    @pytest.fixture
    def chunker(self):
        """Create RecursiveChunker instance."""
        return RecursiveChunker(
            chunk_size=100,
            chunk_overlap=20,
            minimum_chunk_length=20
        )
    
    def test_chunk_short_text(self, chunker):
        """Test chunking short text."""
        text = "This is a short text that fits in one chunk."
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].document_id == "doc1"
        assert chunks[0].source == "test"
    
    def test_chunk_long_text(self, chunker):
        """Test chunking long text."""
        text = " ".join([f"Sentence {i}." for i in range(50)])
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        assert len(chunks) > 1
        # Check overlap
        if len(chunks) > 1:
            # Second chunk should start before first chunk ends (overlap)
            assert chunks[1].start_character < chunks[0].end_character
    
    def test_chunk_metadata(self, chunker):
        """Test chunk metadata generation."""
        text = "Test document with some content."
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        chunk = chunks[0]
        assert chunk.chunk_id.startswith("test_doc1_")
        assert chunk.word_count > 0
        assert chunk.checksum is not None
        assert chunk.created_at is not None
    
    def test_deterministic_ids(self, chunker):
        """Test that chunk IDs are deterministic."""
        text = "Test document."
        chunks1 = chunker.chunk_text(text, "doc1", "test")
        chunks2 = chunker.chunk_text(text, "doc1", "test")
        
        assert chunks1[0].chunk_id == chunks2[0].chunk_id
    
    def test_paragraph_preservation(self, chunker):
        """Test paragraph preservation."""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        # Should try to keep paragraphs together
        assert len(chunks) >= 1


class TestFixedChunker:
    """Test cases for FixedChunker."""
    
    @pytest.fixture
    def chunker(self):
        """Create FixedChunker instance."""
        return FixedChunker(
            chunk_size=100,
            chunk_overlap=10,
            word_boundary=True
        )
    
    def test_fixed_size_chunks(self, chunker):
        """Test fixed-size chunking."""
        text = "a" * 250  # 250 characters
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        # Should create multiple chunks of approximately equal size
        assert len(chunks) > 1
        for chunk in chunks[:-1]:  # All but last
            assert len(chunk.text) <= chunker.chunk_size
    
    def test_word_boundary(self, chunker):
        """Test word boundary preservation."""
        text = "word " * 50  # Many words
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        # Chunks should not break words
        for chunk in chunks:
            # Should not start/end with partial word (except first/last)
            if chunk.chunk_index > 0:
                assert not chunk.text[0].isalnum() or chunk.text[0].isupper()


class TestParagraphChunker:
    """Test cases for ParagraphChunker."""
    
    @pytest.fixture
    def chunker(self):
        """Create ParagraphChunker instance."""
        return ParagraphChunker(
            target_chunk_size=100,
            chunk_overlap=20,
            minimum_chunk_length=20
        )
    
    def test_paragraph_splitting(self, chunker):
        """Test paragraph-based splitting."""
        paragraphs = ["Paragraph 1.", "Paragraph 2.", "Paragraph 3."]
        text = "\n\n".join(paragraphs)
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        assert len(chunks) >= 1
        # Verify paragraphs are kept together when possible
        for chunk in chunks:
            assert "\n\n" in chunk.text or chunk.chunk_index == 0


class TestSectionChunker:
    """Test cases for SectionChunker."""
    
    @pytest.fixture
    def chunker(self):
        """Create SectionChunker instance."""
        return SectionChunker(
            target_chunk_size=150,
            chunk_overlap=20,
            minimum_chunk_length=30
        )
    
    def test_section_detection(self, chunker):
        """Test section header detection."""
        text = "# Section 1\nContent 1.\n\n## Section 2\nContent 2."
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        assert len(chunks) >= 1
        # Check that section metadata is captured
        section_titles = [c.section for c in chunks if c.section]
        assert len(section_titles) > 0


class TestChunkValidation:
    """Test cases for chunk validation."""
    
    def test_valid_chunk(self):
        """Test validation of valid chunk."""
        chunk = Chunk(
            chunk_id="test_doc_0001",
            document_id="doc1",
            source="test",
            text="Valid chunk text.",
            chunk_index=0,
            total_chunks=1,
            start_character=0,
            end_character=17,
            word_count=3,
            created_at="2026-06-28T00:00:00",
            checksum="abc123"
        )
        
        errors = chunk.validate()
        assert len(errors) == 0
    
    def test_invalid_chunk_empty_text(self):
        """Test validation of chunk with empty text."""
        chunk = Chunk(
            chunk_id="test_doc_0001",
            document_id="doc1",
            source="test",
            text="",
            chunk_index=0,
            total_chunks=1,
            start_character=0,
            end_character=0,
            word_count=0,
            created_at="2026-06-28T00:00:00",
            checksum="abc123"
        )
        
        errors = chunk.validate()
        assert "text is empty" in errors
    
    def test_invalid_chunk_indices(self):
        """Test validation of chunk with invalid indices."""
        chunk = Chunk(
            chunk_id="test_doc_0001",
            document_id="doc1",
            source="test",
            text="Text",
            chunk_index=5,
            total_chunks=3,  # Index >= total
            start_character=0,
            end_character=4,
            word_count=1,
            created_at="2026-06-28T00:00:00",
            checksum="abc123"
        )
        
        errors = chunk.validate()
        assert any("chunk_index" in e for e in errors)


class TestChunkMetadata:
    """Test cases for chunk metadata."""
    
    @pytest.fixture
    def chunker(self):
        """Create chunker instance."""
        return RecursiveChunker()
    
    def test_metadata_completeness(self, chunker):
        """Test that all required metadata is generated."""
        text = "Test document content."
        chunks = chunker.chunk_text(text, "doc1", "test_source")
        
        chunk = chunks[0]
        
        # Check required fields
        assert chunk.chunk_id is not None
        assert chunk.document_id == "doc1"
        assert chunk.source == "test_source"
        assert chunk.text == text
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 1
        assert chunk.start_character == 0
        assert chunk.end_character == len(text)
        assert chunk.word_count > 0
        assert chunk.created_at is not None
        assert chunk.checksum is not None
    
    def test_to_dict(self, chunker):
        """Test chunk serialization to dict."""
        text = "Test content."
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        chunk_dict = chunks[0].to_dict()
        
        assert isinstance(chunk_dict, dict)
        assert 'chunk_id' in chunk_dict
        assert 'text' in chunk_dict
        assert 'checksum' in chunk_dict


class TestSpecialContentDetection:
    """Test cases for special content detection."""
    
    @pytest.fixture
    def chunker(self):
        """Create chunker instance."""
        return RecursiveChunker()
    
    def test_code_detection(self, chunker):
        """Test code block detection."""
        text = "Here is code:\n```python\nprint('hello')\n```"
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        # Should detect code
        assert any(chunk.has_code for chunk in chunks)
    
    def test_list_detection(self, chunker):
        """Test list detection."""
        text = "Items:\n- Item 1\n- Item 2\n- Item 3"
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        # Should detect list
        assert any(chunk.has_list for chunk in chunks)
    
    def test_table_detection(self, chunker):
        """Test table detection."""
        text = "| Col1 | Col2 |\n|------|------|\n| A | B |"
        chunks = chunker.chunk_text(text, "doc1", "test")
        
        # Should detect table
        assert any(chunk.has_table for chunk in chunks)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
