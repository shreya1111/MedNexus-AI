"""
Recursive character chunker for MedNexus-AI Knowledge Ingestion Framework.

Splits text recursively using multiple separators for natural breakpoints.
"""

from typing import List, Optional
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from chunkers.base_chunker import BaseChunker, Chunk


class RecursiveChunker(BaseChunker):
    """
    Recursive character text splitter.
    
    Tries to split on separators in order, recursively splitting
    chunks that are still too large.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        minimum_chunk_length: int = 100,
        maximum_chunk_length: int = 2000,
        preserve_headers: bool = True,
        preserve_lists: bool = True,
        preserve_tables: bool = True,
        **kwargs
    ):
        """
        Initialize recursive chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            separators: List of separators to try (in order)
            minimum_chunk_length: Minimum chunk length
            maximum_chunk_length: Maximum chunk length
            preserve_headers: Try to keep headers with following content
            preserve_lists: Try to keep list items together
            preserve_tables: Try to keep tables together
            **kwargs: Additional arguments
        """
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            minimum_chunk_length=minimum_chunk_length,
            maximum_chunk_length=maximum_chunk_length,
            **kwargs
        )
        
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]
        self.preserve_headers = preserve_headers
        self.preserve_lists = preserve_lists
        self.preserve_tables = preserve_tables
    
    def chunk_text(
        self,
        text: str,
        document_id: str,
        source: str,
        **kwargs
    ) -> List[Chunk]:
        """
        Chunk text recursively.
        
        Args:
            text: Text to chunk
            document_id: Document identifier
            source: Source name
            **kwargs: Additional metadata
            
        Returns:
            List of Chunk objects
        """
        # Split text into chunks
        text_chunks = self._split_text_recursive(text)
        
        # Create Chunk objects with metadata
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
        
        # Update total_chunks for all chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        self.logger.debug(
            f"Created {len(chunks)} chunks for document {document_id}"
        )
        
        return chunks
    
    def _split_text_recursive(
        self,
        text: str,
        separators: Optional[List[str]] = None
    ) -> List[str]:
        """
        Split text recursively using separators.
        
        Args:
            text: Text to split
            separators: List of separators to try
            
        Returns:
            List of text chunks
        """
        if separators is None:
            separators = self.separators
        
        # Base case: text is small enough
        if len(text) <= self.chunk_size:
            return [text] if text else []
        
        # Try each separator
        for separator in separators:
            if separator == "":
                # Last resort: character-level split
                return self._split_by_characters(text)
            
            if separator in text:
                splits = text.split(separator)
                
                # Keep separator with split (except for last separator)
                if separator != separators[-1]:
                    splits = [s + separator if i < len(splits) - 1 else s 
                             for i, s in enumerate(splits)]
                
                # Merge splits into chunks
                chunks = self._merge_splits(splits, separator)
                
                # Recursively split chunks that are still too large
                final_chunks = []
                for chunk in chunks:
                    if len(chunk) > self.maximum_chunk_length:
                        # Try next separator
                        next_separators = separators[separators.index(separator) + 1:]
                        if next_separators:
                            final_chunks.extend(
                                self._split_text_recursive(chunk, next_separators)
                            )
                        else:
                            final_chunks.append(chunk)
                    else:
                        final_chunks.append(chunk)
                
                return final_chunks
        
        # Fallback: return as single chunk
        return [text]
    
    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """
        Merge splits into chunks with overlap.
        
        Args:
            splits: List of text splits
            separator: Separator used
            
        Returns:
            List of merged chunks
        """
        chunks = []
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_length = len(split)
            
            # Check if adding this split would exceed chunk size
            if current_length + split_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "".join(current_chunk)
                if len(chunk_text.strip()) >= self.minimum_chunk_length:
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, separator)
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text) if overlap_text else 0
            
            # Add split to current chunk
            current_chunk.append(split)
            current_length += split_length
        
        # Add final chunk
        if current_chunk:
            chunk_text = "".join(current_chunk)
            if len(chunk_text.strip()) >= self.minimum_chunk_length:
                chunks.append(chunk_text)
        
        return chunks
    
    def _get_overlap_text(
        self,
        current_chunk: List[str],
        separator: str
    ) -> str:
        """
        Get overlap text from current chunk.
        
        Args:
            current_chunk: Current chunk parts
            separator: Separator used
            
        Returns:
            Overlap text
        """
        chunk_text = "".join(current_chunk)
        
        if len(chunk_text) <= self.chunk_overlap:
            return chunk_text
        
        # Take last N characters for overlap
        return chunk_text[-self.chunk_overlap:]
    
    def _split_by_characters(self, text: str) -> List[str]:
        """
        Split text by characters (last resort).
        
        Args:
            text: Text to split
            
        Returns:
            List of character-split chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
            
            # Prevent infinite loop
            if start >= end:
                break
        
        return chunks
