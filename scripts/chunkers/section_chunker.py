"""
Section-aware chunker for MedNexus-AI Knowledge Ingestion Framework.

Splits text by document sections (headers).
"""

from typing import List
from pathlib import Path
import re

import sys
sys.path.append(str(Path(__file__).parent.parent))

from chunkers.base_chunker import BaseChunker, Chunk


class SectionChunker(BaseChunker):
    """Section-aware text chunker for structured documents."""
    
    def __init__(
        self,
        target_chunk_size: int = 1500,
        chunk_overlap: int = 150,
        minimum_chunk_length: int = 300,
        maximum_chunk_length: int = 3000,
        section_markers: Optional[List[str]] = None,
        preserve_section_context: bool = True,
        **kwargs
    ):
        """
        Initialize section chunker.
        
        Args:
            target_chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            minimum_chunk_length: Minimum chunk length
            maximum_chunk_length: Maximum chunk length
            section_markers: List of section header markers
            preserve_section_context: Include section header in chunk
            **kwargs: Additional arguments
        """
        super().__init__(
            chunk_size=target_chunk_size,
            chunk_overlap=chunk_overlap,
            minimum_chunk_length=minimum_chunk_length,
            maximum_chunk_length=maximum_chunk_length,
            **kwargs
        )
        
        self.section_markers = section_markers or ["# ", "## ", "### "]
        self.preserve_section_context = preserve_section_context
    
    def chunk_text(
        self,
        text: str,
        document_id: str,
        source: str,
        **kwargs
    ) -> List[Chunk]:
        """
        Chunk text by sections.
        
        Args:
            text: Text to chunk
            document_id: Document identifier
            source: Source name
            **kwargs: Additional metadata
            
        Returns:
            List of Chunk objects
        """
        # Split by sections
        sections = self._split_by_sections(text)
        
        # Combine sections into chunks
        text_chunks = self._combine_sections(sections)
        
        # Create Chunk objects
        chunks = []
        char_position = 0
        
        for i, (chunk_text, section_title) in enumerate(text_chunks):
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
                section=section_title,
                **{**kwargs, **special_content}
            )
            
            chunks.append(chunk)
            char_position = end_char
        
        # Update total_chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _split_by_sections(self, text: str) -> List[tuple]:
        """
        Split text by section headers.
        
        Args:
            text: Text to split
            
        Returns:
            List of (section_title, section_content) tuples
        """
        sections = []
        lines = text.split('\n')
        
        current_section = None
        current_content = []
        
        for line in lines:
            # Check if line is a section header
            is_header = False
            for marker in self.section_markers:
                if line.strip().startswith(marker):
                    # Save previous section
                    if current_section is not None or current_content:
                        content = '\n'.join(current_content)
                        sections.append((current_section, content))
                    
                    # Start new section
                    current_section = line.strip()
                    current_content = [line] if self.preserve_section_context else []
                    is_header = True
                    break
            
            if not is_header:
                current_content.append(line)
        
        # Add final section
        if current_section is not None or current_content:
            content = '\n'.join(current_content)
            sections.append((current_section, content))
        
        return sections
    
    def _combine_sections(self, sections: List[tuple]) -> List[tuple]:
        """
        Combine sections into chunks.
        
        Args:
            sections: List of (title, content) tuples
            
        Returns:
            List of (chunk_text, section_title) tuples
        """
        chunks = []
        current_title = None
        current_content = []
        current_length = 0
        
        for title, content in sections:
            content_length = len(content)
            
            # Check if adding this section exceeds maximum
            if current_length + content_length > self.maximum_chunk_length and current_content:
                # Save current chunk
                chunk_text = '\n\n'.join(current_content)
                if len(chunk_text.strip()) >= self.minimum_chunk_length:
                    chunks.append((chunk_text, current_title))
                
                # Start new chunk
                current_title = title
                current_content = []
                current_length = 0
            
            # Update title if not set
            if current_title is None:
                current_title = title
            
            # Add content to current chunk
            current_content.append(content)
            current_length += content_length
            
            # Check if we've reached target size
            if current_length >= self.chunk_size:
                chunk_text = '\n\n'.join(current_content)
                if len(chunk_text.strip()) >= self.minimum_chunk_length:
                    chunks.append((chunk_text, current_title))
                
                # Start new chunk
                current_title = None
                current_content = []
                current_length = 0
        
        # Add final chunk
        if current_content:
            chunk_text = '\n\n'.join(current_content)
            if len(chunk_text.strip()) >= self.minimum_chunk_length:
                chunks.append((chunk_text, current_title))
        
        return chunks
