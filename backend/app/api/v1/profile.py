"""
Profile and Settings API endpoints.

Handles user profile management and settings.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    PasswordChangeRequest,
    SettingsResponse,
    SettingsUpdateRequest
)
from app.services.profile_service import ProfileService
from app.dependencies.auth import get_current_active_user
from app.database.models import User


router = APIRouter(tags=["Profile"])


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user profile with statistics.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User profile with statistics
    """
    service = ProfileService(db)
    profile = await service.get_profile(user=current_user)
    
    return ProfileResponse(**profile)


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile.
    
    Args:
        request: Profile update request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated profile
    """
    service = ProfileService(db)
    profile = await service.update_profile(
        user=current_user,
        full_name=request.full_name,
        email=request.email
    )
    
    return ProfileResponse(**profile)


@router.post("/profile/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.
    
    Args:
        request: Password change request
        current_user: Current authenticated user
        db: Database session
    """
    service = ProfileService(db)
    await service.change_password(
        user=current_user,
        current_password=request.current_password,
        new_password=request.new_password
    )


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user settings.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User settings
    """
    service = ProfileService(db)
    settings = await service.get_settings(user=current_user)
    
    return SettingsResponse(**settings)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    request: SettingsUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user settings.
    
    Args:
        request: Settings update request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated settings
    """
    service = ProfileService(db)
    
    # Convert request to dict, excluding None values
    settings_update = request.model_dump(exclude_none=True)
    
    settings = await service.update_settings(
        user=current_user,
        settings_update=settings_update
    )
    
    return SettingsResponse(**settings)
