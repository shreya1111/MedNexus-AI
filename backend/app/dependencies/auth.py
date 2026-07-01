"""
Authentication dependencies.

Provides dependency injection for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models import User, UserRole
from app.core.security import decode_token, verify_token_type
from app.core.exceptions import AuthenticationError, AuthorizationError


# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user.
    
    Args:
        credentials: Bearer token credentials
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        AuthenticationError: If authentication fails
    """
    token = credentials.credentials
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    
    # Verify token type
    if not verify_token_type(payload, "access"):
        raise AuthenticationError("Invalid token type")
    
    # Get user ID from payload
    user_id: int = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("User account is inactive")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user
        
    Raises:
        AuthenticationError: If user is inactive
    """
    if not current_user.is_active:
        raise AuthenticationError("User account is inactive")
    
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current verified user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Verified user
        
    Raises:
        AuthenticationError: If user is not verified
    """
    if not current_user.is_verified:
        raise AuthenticationError("User email is not verified")
    
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current superuser.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Superuser
        
    Raises:
        AuthorizationError: If user is not superuser
    """
    if not current_user.is_superuser:
        raise AuthorizationError("Superuser privileges required")
    
    return current_user


def require_role(*allowed_roles: UserRole):
    """
    Dependency factory for role-based access control.
    
    Args:
        allowed_roles: Allowed user roles
        
    Returns:
        Dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and not current_user.is_superuser:
            raise AuthorizationError(
                f"Role {current_user.role} not authorized. Required: {allowed_roles}"
            )
        return current_user
    
    return role_checker


# Common role dependencies
require_patient = require_role(UserRole.PATIENT)
require_doctor = require_role(UserRole.DOCTOR)
require_researcher = require_role(UserRole.RESEARCHER)
require_admin = require_role(UserRole.ADMINISTRATOR)
