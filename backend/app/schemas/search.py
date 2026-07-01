"""
Search schemas for request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Search request schema."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    filters: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    """Individual search result."""
    chunk_id: str
    document: str
    similarity: float
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Search response schema."""
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time_ms: float


class HybridSearchRequest(BaseModel):
    """Hybrid search request schema."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)
    vector_weight: float = Field(0.7, ge=0.0, le=1.0)
    bm25_weight: float = Field(0.3, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = None
