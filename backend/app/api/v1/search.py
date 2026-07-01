"""
Search API endpoints.

Handles knowledge base search requests.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    HybridSearchRequest
)
from app.services.search_service import SearchService
from app.dependencies.auth import get_current_active_user
from app.database.models import User


router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/vector", response_model=SearchResponse)
async def vector_search(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform vector search on knowledge base.
    
    Args:
        request: Search request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Search results
    """
    service = SearchService(db)
    results = await service.vector_search(
        query=request.query,
        top_k=request.top_k,
        filters=request.filters
    )
    
    return SearchResponse(**results)


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform hybrid search (vector + BM25) on knowledge base.
    
    Args:
        request: Hybrid search request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Search results
    """
    service = SearchService(db)
    results = await service.hybrid_search(
        query=request.query,
        top_k=request.top_k,
        vector_weight=request.vector_weight,
        bm25_weight=request.bm25_weight,
        filters=request.filters
    )
    
    return SearchResponse(**results)


@router.post("", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform default search (vector) on knowledge base.
    
    Args:
        request: Search request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Search results
    """
    service = SearchService(db)
    results = await service.vector_search(
        query=request.query,
        top_k=request.top_k,
        filters=request.filters
    )
    
    return SearchResponse(**results)


@router.get("/stats")
async def get_search_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get search/knowledge base statistics.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Statistics
    """
    service = SearchService(db)
    stats = await service.get_stats()
    
    return stats
