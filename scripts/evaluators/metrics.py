"""
Metrics dataclasses for chunk quality evaluation.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


@dataclass
class ChunkMetrics:
    """Comprehensive metrics for chunk quality analysis."""
    
    # Dataset statistics
    total_documents: int = 0
    total_chunks: int = 0
    chunks_per_document_avg: float = 0.0
    chunks_per_document_median: float = 0.0
    
    # Chunk size metrics
    avg_chunk_size: float = 0.0
    min_chunk_size: int = 0
    max_chunk_size: int = 0
    median_chunk_size: float = 0.0
    std_chunk_size: float = 0.0
    tiny_chunks_count: int = 0
    oversized_chunks_count: int = 0
    
    # Token metrics
    avg_tokens: float = 0.0
    min_tokens: int = 0
    max_tokens: int = 0
    median_tokens: float = 0.0
    tokens_exceeding_limit: int = 0
    
    # Overlap metrics
    avg_overlap_percentage: float = 0.0
    min_overlap_percentage: float = 0.0
    max_overlap_percentage: float = 0.0
    missing_overlap_count: int = 0
    excessive_overlap_count: int = 0
    
    # Duplicate detection
    exact_duplicates: int = 0
    near_duplicates: int = 0
    duplicate_chunk_ids: int = 0
    duplicate_rate: float = 0.0
    
    # Structure preservation
    header_preservation_score: float = 0.0
    list_preservation_score: float = 0.0
    table_preservation_score: float = 0.0
    chunks_with_headers: int = 0
    chunks_with_lists: int = 0
    chunks_with_tables: int = 0
    
    # Density metrics
    avg_useful_text_ratio: float = 0.0
    avg_whitespace_ratio: float = 0.0
    avg_density_score: float = 0.0
    
    # Metadata validation
    missing_metadata_count: int = 0
    invalid_metadata_count: int = 0
    metadata_completeness: float = 0.0
    
    # Language metrics
    language_consistency: float = 0.0
    mixed_language_chunks: int = 0
    encoding_errors: int = 0
    
    # Readability metrics
    avg_sentence_length: float = 0.0
    avg_words_per_chunk: float = 0.0
    readability_score: float = 0.0
    
    # Processing metrics
    evaluation_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)


@dataclass
class QualityScore:
    """Quality score breakdown."""
    
    overall_score: float = 0.0  # 0-100
    
    # Component scores (0-1)
    chunk_size_score: float = 0.0
    metadata_score: float = 0.0
    structure_score: float = 0.0
    list_score: float = 0.0
    table_score: float = 0.0
    duplicate_score: float = 0.0
    overlap_score: float = 0.0
    readability_score: float = 0.0
    density_score: float = 0.0
    
    # Weights used
    weights: Dict[str, float] = field(default_factory=dict)
    
    # Issues detected
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def grade(self) -> str:
        """Get letter grade."""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"


@dataclass
class BenchmarkResult:
    """Benchmark comparison result."""
    
    strategy: str
    avg_chunk_size: float
    chunk_count: int
    overlap_percentage: float
    duplicate_rate: float
    processing_time: float
    quality_score: float
    recommended_use_case: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Recommendation:
    """Quality improvement recommendation."""
    
    priority: str  # "high", "medium", "low"
    category: str  # "chunk_size", "overlap", "duplicates", etc.
    issue: str
    recommendation: str
    confidence: float  # 0-1
    affected_chunks: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
