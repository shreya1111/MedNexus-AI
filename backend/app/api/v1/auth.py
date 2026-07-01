"""
Authentication API endpoints.

Handles user registration, login, logout, and token refresh.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.user import (
    User,
    UserCreate,
    Token,
    LoginRequest,
    RefreshTokenRequest
)
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.database.models import User as UserModel


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_create: User creation data
        db: Database session
        
    Returns:
        Created user
    """
    service = AuthService(db)
    user = await service.register_user(user_create)
    return user


@router.post("/login", response_model=Token)
async def login(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get access token.
    
    Args:
        login_request: Login credentials
        db: Database session
        
    Returns:
        Access and refresh tokens
    """
    service = AuthService(db)
    user, access_token, refresh_token = await service.authenticate_user(
        email=login_request.email,
        password=login_request.password
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token.
    
    Args:
        refresh_request: Refresh token request
        db: Database session
        
    Returns:
        New access and refresh tokens
    """
    service = AuthService(db)
    access_token, refresh_token = await service.refresh_access_token(
        refresh_request.refresh_token
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_request: RefreshTokenRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user by revoking refresh token.
    
    Args:
        refresh_request: Refresh token to revoke
        current_user: Current authenticated user
        db: Database session
    """
    service = AuthService(db)
    await service.logout_user(refresh_request.refresh_token)


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user data
    """
    return current_user
