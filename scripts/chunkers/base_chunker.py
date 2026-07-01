"""
Base chunker class for MedNexus-AI Knowledge Ingestion Framework.

Provides abstract base class for all chunking strategies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import hashlib

import sys
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger


@dataclass
class Chunk:
    """Represents a single chunk of text with metadata."""
    
    chunk_id: str
    document_id: str
    source: str
    text: str
    chunk_index: int
    total_chunks: int
    start_character: int
    end_character: int
    word_count: int
    created_at: str
    checksum: str
    
    # Optional metadata
    title: Optional[str] = None
    section: Optional[str] = None
    language: Optional[str] = "en"
    tokens: Optional[int] = None
    has_code: bool = False
    has_list: bool = False
    has_table: bool = False
    parent_document_checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return asdict(self)
    
    def validate(self) -> List[str]:
        """
        Validate chunk data.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.chunk_id:
            errors.append("chunk_id is required")
        
        if not self.document_id:
            errors.append("document_id is required")
        
        if not self.source:
            errors.append("source is required")
        
        if not self.text or not self.text.strip():
            errors.append("text is empty")
        
        if self.chunk_index < 0:
            errors.append("chunk_index must be non-negative")
        
        if self.total_chunks <= 0:
            errors.append("total_chunks must be positive")
        
        if self.chunk_index >= self.total_chunks:
            errors.append("chunk_index must be less than total_chunks")
        
        if self.start_character < 0:
            errors.append("start_character must be non-negative")
        
        if self.end_character <= self.start_character:
            errors.append("end_character must be greater than start_character")
        
        if self.word_count < 0:
            errors.append("word_count must be non-negative")
        
        return errors


@dataclass
class ChunkingResult:
    """Result of chunking operation."""
    
    document_id: str
    source: str
    chunks: List[Chunk]
    processing_time_seconds: float
    status: str  # 'success', 'partial', 'failed'
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def chunk_count(self) -> int:
        """Get number of chunks."""
        return len(self.chunks)
    
    @property
    def total_characters(self) -> int:
        """Get total characters across all chunks."""
        return sum(len(chunk.text) for chunk in self.chunks)
    
    @property
    def average_chunk_size(self) -> float:
        """Get average chunk size in characters."""
        return self.total_characters / self.chunk_count if self.chunk_count > 0 else 0


class BaseChunker(ABC):
    """Abstract base class for all chunking strategies."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        minimum_chunk_length: int = 100,
        maximum_chunk_length: int = 2000,
        **kwargs
    ):
        """
        Initialize base chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            minimum_chunk_length: Minimum chunk length
            maximum_chunk_length: Maximum chunk length
            **kwargs: Additional strategy-specific arguments
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.minimum_chunk_length = minimum_chunk_length
        self.maximum_chunk_length = maximum_chunk_length
        
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def chunk_text(
        self,
        text: str,
        document_id: str,
        source: str,
        **kwargs
    ) -> List[Chunk]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Text to chunk
            document_id: Document identifier
            source: Source name
            **kwargs: Additional metadata
            
        Returns:
            List of Chunk objects
        """
        pass
    
    def _calculate_word_count(self, text: str) -> int:
        """Calculate word count."""
        return len(text.split())
    
    def _generate_chunk_id(
        self,
        document_id: str,
        source: str,
        chunk_index: int,
        format_pattern: str = "{source}_{document_id}_{chunk_index:04d}"
    ) -> str:
        """
        Generate deterministic chunk ID.
        
        Args:
            document_id: Document identifier
            source: Source name
            chunk_index: Chunk index
            format_pattern: ID format pattern
            
        Returns:
            Chunk ID string
        """
        return format_pattern.format(
            source=source,
            document_id=document_id,
            chunk_index=chunk_index
        )
    
    def _generate_checksum(self, text: str, algorithm: str = "sha256") -> str:
        """
        Generate checksum for text.
        
        Args:
            text: Text to checksum
            algorithm: Hash algorithm
            
        Returns:
            Checksum hex string
        """
        if algorithm == "sha256":
            return hashlib.sha256(text.encode('utf-8')).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(text.encode('utf-8')).hexdigest()
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    def _get_timestamp(self) -> str:
        """Get ISO format timestamp."""
        return datetime.now().isoformat()
    
    def _create_chunk(
        self,
        text: str,
        document_id: str,
        source: str,
        chunk_index: int,
        total_chunks: int,
        start_character: int,
        end_character: int,
        **kwargs
    ) -> Chunk:
        """
        Create a Chunk object with metadata.
        
        Args:
            text: Chunk text
            document_id: Document identifier
            source: Source name
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks
            start_character: Start position in original text
            end_character: End position in original text
            **kwargs: Additional metadata
            
        Returns:
            Chunk object
        """
        chunk_id = self._generate_chunk_id(document_id, source, chunk_index)
        word_count = self._calculate_word_count(text)
        checksum = self._generate_checksum(text)
        created_at = self._get_timestamp()
        
        return Chunk(
            chunk_id=chunk_id,
            document_id=document_id,
            source=source,
            text=text,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            start_character=start_character,
            end_character=end_character,
            word_count=word_count,
            created_at=created_at,
            checksum=checksum,
            title=kwargs.get('title'),
            section=kwargs.get('section'),
            language=kwargs.get('language', 'en'),
            tokens=kwargs.get('tokens'),
            has_code=kwargs.get('has_code', False),
            has_list=kwargs.get('has_list', False),
            has_table=kwargs.get('has_table', False),
            parent_document_checksum=kwargs.get('parent_document_checksum')
        )
    
    def _validate_chunks(self, chunks: List[Chunk]) -> List[str]:
        """
        Validate all chunks.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            List of validation errors
        """
        all_errors = []
        
        for i, chunk in enumerate(chunks):
            errors = chunk.validate()
            if errors:
                all_errors.extend([f"Chunk {i}: {error}" for error in errors])
        
        # Check for duplicate chunk IDs
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        if len(chunk_ids) != len(set(chunk_ids)):
            all_errors.append("Duplicate chunk IDs found")
        
        return all_errors
    
    def _detect_special_content(self, text: str) -> Dict[str, bool]:
        """
        Detect special content types in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with boolean flags for special content
        """
        return {
            'has_code': '```' in text or '    ' in text,  # Code blocks or indented code
            'has_list': any(line.strip().startswith(('- ', '* ', '1.', '2.', '3.')) for line in text.split('\n')),
            'has_table': '|' in text and text.count('|') > 4,  # Markdown tables
        }
