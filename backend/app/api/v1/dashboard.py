"""
Dashboard API endpoints.

Handles analytics and metrics requests.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.dashboard_service import DashboardService
from app.dependencies.auth import get_current_active_user
from app.database.models import User


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics for current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dashboard statistics
    """
    service = DashboardService(db)
    stats = await service.get_dashboard_stats(user_id=current_user.id)
    
    return stats


@router.get("/stats/all")
async def get_all_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics for all users (admin only).
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dashboard statistics
    """
    # Check if user is admin
    if not current_user.is_superuser and current_user.role.value != 'administrator':
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Admin access required")
    
    service = DashboardService(db)
    stats = await service.get_dashboard_stats(user_id=None)
    
    return stats


@router.get("/trend")
async def get_usage_trend(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage trend over time.
    
    Args:
        days: Number of days
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Usage trend data
    """
    service = DashboardService(db)
    trend = await service.get_usage_trend(user_id=current_user.id, days=days)
    
    return trend


@router.get("/health")
async def get_system_health(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system health metrics.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        System health
    """
    service = DashboardService(db)
    health = await service.get_system_health()
    
    return health
