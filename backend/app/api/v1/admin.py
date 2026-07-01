"""
Admin API endpoints.

Handles system administration and user management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.admin import (
    UserList,
    UserDetail,
    UserUpdateRequest,
    SystemStats,
    SystemHealth,
    ActivityLogList
)
from app.services.admin_service import AdminService
from app.dependencies.auth import get_current_active_user
from app.database.models import User


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=UserList)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users (admin only).
    
    Args:
        page: Page number
        page_size: Items per page
        role: Optional role filter
        is_active: Optional active status filter
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Paginated list of users
    """
    service = AdminService(db)
    users, total = await service.get_users(
        admin_user=current_user,
        page=page,
        page_size=page_size,
        role=role,
        is_active=is_active
    )
    
    has_more = (page * page_size) < total
    
    return UserList(
        users=users,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed user information (admin only).
    
    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Detailed user information
    """
    service = AdminService(db)
    user = await service.get_user(
        admin_user=current_user,
        user_id=user_id
    )
    
    return UserDetail(**user)


@router.put("/users/{user_id}", response_model=UserDetail)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user (admin only).
    
    Args:
        user_id: User ID
        request: User update request
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Updated user information
    """
    service = AdminService(db)
    user = await service.update_user(
        admin_user=current_user,
        user_id=user_id,
        full_name=request.full_name,
        role=request.role,
        is_active=request.is_active,
        is_verified=request.is_verified
    )
    
    return UserDetail(**user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (admin only).
    
    Args:
        user_id: User ID
        current_user: Current authenticated admin user
        db: Database session
    """
    service = AdminService(db)
    await service.delete_user(
        admin_user=current_user,
        user_id=user_id
    )


@router.get("/stats", response_model=SystemStats)
async def get_system_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system-wide statistics (admin only).
    
    Args:
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        System statistics
    """
    service = AdminService(db)
    stats = await service.get_system_stats(admin_user=current_user)
    
    return SystemStats(**stats)


@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system health status (admin only).
    
    Args:
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        System health information
    """
    service = AdminService(db)
    health = await service.get_system_health(admin_user=current_user)
    
    return SystemHealth(**health)


@router.get("/logs", response_model=ActivityLogList)
async def get_activity_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    status_code: Optional[int] = Query(None, description="Filter by status code"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity logs (admin only).
    
    Args:
        page: Page number
        page_size: Items per page
        user_id: Optional user ID filter
        endpoint: Optional endpoint filter
        status_code: Optional status code filter
        current_user: Current authenticated admin user
        db: Database session
        
    Returns:
        Paginated activity logs
    """
    service = AdminService(db)
    logs, total = await service.get_activity_logs(
        admin_user=current_user,
        page=page,
        page_size=page_size,
        user_id=user_id,
        endpoint=endpoint,
        status_code=status_code
    )
    
    has_more = (page * page_size) < total
    
    return ActivityLogList(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more
    )
