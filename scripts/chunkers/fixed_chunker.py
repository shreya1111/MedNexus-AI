"""
Fixed-size chunker for MedNexus-AI Knowledge Ingestion Framework.

Splits text into fixed-size chunks with optional word boundary preservation.
"""

from typing import List
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from chunkers.base_chunker import BaseChunker, Chunk


class FixedChunker(BaseChunker):
    """Fixed-size text chunker with word boundary support."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        minimum_chunk_length: int = 100,
        maximum_chunk_length: int = 1000,
        word_boundary: bool = True,
        **kwargs
    ):
        """
        Initialize fixed chunker.
        
        Args:
            chunk_size: Fixed chunk size in characters
            chunk_overlap: Overlap between chunks
            minimum_chunk_length: Minimum chunk length
            maximum_chunk_length: Maximum chunk length (same as chunk_size)
            word_boundary: Break at word boundaries
            **kwargs: Additional arguments
        """
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            minimum_chunk_length=minimum_chunk_length,
            maximum_chunk_length=chunk_size,  # Fixed size
            **kwargs
        )
        
        self.word_boundary = word_boundary
    
    def chunk_text(
        self,
        text: str,
        document_id: str,
        source: str,
        **kwargs
    ) -> List[Chunk]:
        """
        Chunk text into fixed-size pieces.
        
        Args:
            text: Text to chunk
            document_id: Document identifier
            source: Source name
            **kwargs: Additional metadata
            
        Returns:
            List of Chunk objects
        """
        # Split into fixed-size chunks
        text_chunks = self._split_fixed_size(text)
        
        # Create Chunk objects
        chunks = []
        char_position = 0
        
        for i, chunk_text in enumerate(text_chunks):
            if not chunk_text.strip():
                continue
            
            start_char = char_position
            end_char = char_position + len(chunk_text)
            
            # Detect special content
            special_content = self._detect_special_content(chunk_text)
            
            chunk = self._create_chunk(
                text=chunk_text,
                document_id=document_id,
                source=source,
                chunk_index=i,
                total_chunks=len(text_chunks),
                start_character=start_char,
                end_character=end_char,
                **{**kwargs, **special_content}
            )
            
            chunks.append(chunk)
            char_position = end_char - self.chunk_overlap
        
        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _split_fixed_size(self, text: str) -> List[str]:
        """
        Split text into fixed-size chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # Adjust to word boundary if enabled
            if self.word_boundary and end < len(text):
                end = self._find_word_boundary(text, end)
            
            chunk = text[start:end]
            
            if len(chunk.strip()) >= self.minimum_chunk_length:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start >= end:
                start = end
        
        return chunks
    
    def _find_word_boundary(self, text: str, position: int) -> int:
        """
        Find nearest word boundary before position.
        
        Args:
            text: Full text
            position: Current position
            
        Returns:
            Adjusted position at word boundary
        """
        # Look backward for space
        search_start = max(0, position - 50)  # Search up to 50 chars back
        
        for i in range(position, search_start, -1):
            if text[i] in {' ', '\n', '\t', '.', '!', '?', ';'}:
                return i + 1
        
        # No word boundary found, use original position
        return position
