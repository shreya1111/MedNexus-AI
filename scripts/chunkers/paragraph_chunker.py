"""
Paragraph-aware chunker for MedNexus-AI Knowledge Ingestion Framework.

Splits text by paragraphs, combining them to reach target chunk size.
"""

from typing import List
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from chunkers.base_chunker import BaseChunker, Chunk


class ParagraphChunker(BaseChunker):
    """Paragraph-aware text chunker."""
    
    def __init__(
        self,
        target_chunk_size: int = 1000,
        chunk_overlap: int = 100,
        minimum_chunk_length: int = 200,
        maximum_chunk_length: int = 2000,
        separator: str = "\n\n",
        preserve_headers: bool = True,
        **kwargs
    ):
        """
        Initialize paragraph chunker.
        
        Args:
            target_chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            minimum_chunk_length: Minimum chunk length
            maximum_chunk_length: Maximum chunk length
            separator: Paragraph separator
            preserve_headers: Keep headers with following paragraphs
            **kwargs: Additional arguments
        """
        super().__init__(
            chunk_size=target_chunk_size,
            chunk_overlap=chunk_overlap,
            minimum_chunk_length=minimum_chunk_length,
            maximum_chunk_length=maximum_chunk_length,
            **kwargs
        )
        
        self.separator = separator
        self.preserve_headers = preserve_headers
    
    def chunk_text(
        self,
        text: str,
        document_id: str,
        source: str,
        **kwargs
    ) -> List[Chunk]:
        """
        Chunk text by paragraphs.
        
        Args:
            text: Text to chunk
            document_id: Document identifier
            source: Source name
            **kwargs: Additional metadata
            
        Returns:
            List of Chunk objects
        """
        # Split by paragraphs
        paragraphs = text.split(self.separator)
        
        # Combine paragraphs into chunks
        text_chunks = self._combine_paragraphs(paragraphs)
        
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
            char_position = end_char
        
        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _combine_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """
        Combine paragraphs into chunks.
        
        Args:
            paragraphs: List of paragraphs
            
        Returns:
            List of combined chunks
        """
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            # Check if adding this paragraph exceeds maximum
            if current_length + para_length > self.maximum_chunk_length and current_chunk:
                # Save current chunk
                chunk_text = self.separator.join(current_chunk)
                if len(chunk_text.strip()) >= self.minimum_chunk_length:
                    chunks.append(chunk_text)
                
                # Start new chunk
                current_chunk = []
                current_length = 0
            
            # Add paragraph to current chunk
            current_chunk.append(para)
            current_length += para_length
            
            # Check if we've reached target size
            if current_length >= self.chunk_size:
                chunk_text = self.separator.join(current_chunk)
                if len(chunk_text.strip()) >= self.minimum_chunk_length:
                    chunks.append(chunk_text)
                
                # Start new chunk
                current_chunk = []
                current_length = 0
        
        # Add final chunk
        if current_chunk:
            chunk_text = self.separator.join(current_chunk)
            if len(chunk_text.strip()) >= self.minimum_chunk_length:
                chunks.append(chunk_text)
        
        return chunks
