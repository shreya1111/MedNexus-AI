"""
Profile service for user profile and settings management.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.models import User, Conversation, Session as ChatSession, Document, MedicalReport
from app.core.security import verify_password, get_password_hash
from app.core.exceptions import ValidationError, NotFoundError


class ProfileService:
    """Profile service for user management."""
    
    # Default settings
    DEFAULT_SETTINGS = {
        "theme": "system",
        "language": "en",
        "notifications_enabled": True,
        "email_notifications": True,
        "ai_model": "gemini-2.0-flash",
        "retrieval_top_k": 5,
        "chunk_size": 512,
        "embedding_provider": "google"
    }
    
    def __init__(self, db: AsyncSession):
        """
        Initialize profile service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_profile(self, user: User) -> Dict[str, Any]:
        """
        Get user profile with statistics.
        
        Args:
            user: Current user
            
        Returns:
            Profile information with statistics
        """
        # Get conversation statistics
        conv_result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user.id)
        )
        total_messages = conv_result.scalar_one()
        
        # Get sessions count
        sessions_result = await self.db.execute(
            select(func.count(ChatSession.id)).where(ChatSession.user_id == user.id)
        )
        total_conversations = sessions_result.scalar_one()
        
        # Get documents count
        docs_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.user_id == user.id)
        )
        total_documents = docs_result.scalar_one()
        
        # Get reports count
        reports_result = await self.db.execute(
            select(func.count(MedicalReport.id)).where(MedicalReport.user_id == user.id)
        )
        total_reports = reports_result.scalar_one()
        
        # Calculate member since
        member_since = user.created_at.strftime("%B %Y")
        days_active = (datetime.utcnow() - user.created_at).days
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
            "statistics": {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "total_documents": total_documents,
                "total_reports": total_reports,
                "member_since": member_since,
                "days_active": days_active
            }
        }
    
    async def update_profile(
        self,
        user: User,
        full_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user profile.
        
        Args:
            user: Current user
            full_name: New full name
            email: New email
            
        Returns:
            Updated profile information
        """
        if full_name:
            user.full_name = full_name
        
        if email and email != user.email:
            # Check if email already exists
            existing = await self.db.execute(
                select(User).where(User.email == email)
            )
            if existing.scalar_one_or_none():
                raise ValidationError("Email already in use")
            
            user.email = email
            user.is_verified = False  # Require re-verification
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        return await self.get_profile(user)
    
    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> None:
        """
        Change user password.
        
        Args:
            user: Current user
            current_password: Current password
            new_password: New password
        """
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise ValidationError("Current password is incorrect")
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def get_settings(self, user: User) -> Dict[str, Any]:
        """
        Get user settings.
        
        Args:
            user: Current user
            
        Returns:
            User settings
        """
        # For now, return default settings
        # In production, store in database or separate settings table
        return self.DEFAULT_SETTINGS.copy()
    
    async def update_settings(
        self,
        user: User,
        settings_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user settings.
        
        Args:
            user: Current user
            settings_update: Settings to update
            
        Returns:
            Updated settings
        """
        # Get current settings
        current_settings = await self.get_settings(user)
        
        # Update with new values
        for key, value in settings_update.items():
            if value is not None and key in current_settings:
                current_settings[key] = value
        
        # In production, save to database
        # For now, just return updated settings
        
        return current_settings
