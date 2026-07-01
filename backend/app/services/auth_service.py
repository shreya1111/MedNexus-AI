"""
Authentication service.

Handles user authentication, registration, and token management.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import User, RefreshToken
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ValidationError
)
from app.schemas.user import UserCreate


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize auth service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def register_user(self, user_create: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_create: User creation data
            
        Returns:
            Created user
            
        Raises:
            ConflictError: If email already exists
        """
        # Check if user exists
        result = await self.db.execute(
            select(User).where(User.email == user_create.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise ConflictError("Email already registered")
        
        # Create user
        user = User(
            email=user_create.email,
            full_name=user_create.full_name,
            role=user_create.role,
            hashed_password=get_password_hash(user_create.password),
            is_active=True,
            is_verified=False,  # Email verification required
            is_superuser=False
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Get user
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        # Generate tokens
        access_token = create_access_token(data={"sub": user.id})
        refresh_token_str = create_refresh_token(data={"sub": user.id})
        
        # Store refresh token
        refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        )
        
        self.db.add(refresh_token)
        await self.db.commit()
        
        return user, access_token, refresh_token_str
    
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Tuple[str, str]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Decode token
        payload = decode_token(refresh_token)
        if not payload:
            raise AuthenticationError("Invalid or expired refresh token")
        
        # Verify token type
        if not verify_token_type(payload, "refresh"):
            raise AuthenticationError("Invalid token type")
        
        # Get user ID
        user_id: int = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Verify token exists and not revoked
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked == False
            )
        )
        stored_token = result.scalar_one_or_none()
        
        if not stored_token:
            raise AuthenticationError("Refresh token not found or revoked")
        
        if stored_token.expires_at < datetime.utcnow():
            raise AuthenticationError("Refresh token expired")
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Revoke old refresh token
        stored_token.is_revoked = True
        stored_token.revoked_at = datetime.utcnow()
        
        # Generate new tokens
        new_access_token = create_access_token(data={"sub": user.id})
        new_refresh_token = create_refresh_token(data={"sub": user.id})
        
        # Store new refresh token
        new_token = RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=datetime.utcnow() + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
        )
        
        self.db.add(new_token)
        await self.db.commit()
        
        return new_access_token, new_refresh_token
    
    async def logout_user(self, refresh_token: str) -> None:
        """
        Logout user by revoking refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
        """
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.is_revoked == False
            )
        )
        stored_token = result.scalar_one_or_none()
        
        if stored_token:
            stored_token.is_revoked = True
            stored_token.revoked_at = datetime.utcnow()
            await self.db.commit()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User or None
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User or None
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
