"""
Admin service for system administration.
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import psutil
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.database.models import (
    User, UserRole, Conversation, Session as ChatSession,
    Document, MedicalReport, APIUsage
)
from app.core.exceptions import NotFoundError, ValidationError, PermissionDenied


class AdminService:
    """Admin service for system management."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize admin service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def _check_admin(self, user: User) -> None:
        """Check if user is admin."""
        if not user.is_superuser:
            raise PermissionDenied("Admin access required")
    
    async def get_users(
        self,
        admin_user: User,
        page: int = 1,
        page_size: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get users list with pagination.
        
        Args:
            admin_user: Admin user
            page: Page number
            page_size: Items per page
            role: Filter by role
            is_active: Filter by active status
            
        Returns:
            Tuple of (users list, total count)
        """
        self._check_admin(admin_user)
        
        # Build query
        query = select(User)
        count_query = select(func.count(User.id))
        
        # Apply filters
        filters = []
        if role:
            filters.append(User.role == UserRole(role))
        if is_active is not None:
            filters.append(User.is_active == is_active)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(desc(User.created_at)).offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return [
            {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "last_login": user.last_login,
                "created_at": user.created_at
            }
            for user in users
        ], total
    
    async def get_user(
        self,
        admin_user: User,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed user information.
        
        Args:
            admin_user: Admin user
            user_id: User ID
            
        Returns:
            Detailed user information
        """
        self._check_admin(admin_user)
        
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Get user statistics
        conv_result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user.id)
        )
        total_messages = conv_result.scalar_one()
        
        sessions_result = await self.db.execute(
            select(func.count(ChatSession.id)).where(ChatSession.user_id == user.id)
        )
        total_conversations = sessions_result.scalar_one()
        
        docs_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.user_id == user.id)
        )
        total_documents = docs_result.scalar_one()
        
        reports_result = await self.db.execute(
            select(func.count(MedicalReport.id)).where(MedicalReport.user_id == user.id)
        )
        total_reports = reports_result.scalar_one()
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_superuser": user.is_superuser,
            "last_login": user.last_login,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "statistics": {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "total_documents": total_documents,
                "total_reports": total_reports
            }
        }
    
    async def update_user(
        self,
        admin_user: User,
        user_id: int,
        full_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update user information.
        
        Args:
            admin_user: Admin user
            user_id: User ID
            full_name: New full name
            role: New role
            is_active: Active status
            is_verified: Verified status
            
        Returns:
            Updated user information
        """
        self._check_admin(admin_user)
        
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        # Don't allow admin to modify their own admin status
        if user.id == admin_user.id and is_active is False:
            raise ValidationError("Cannot deactivate your own account")
        
        if full_name:
            user.full_name = full_name
        
        if role:
            user.role = UserRole(role)
        
        if is_active is not None:
            user.is_active = is_active
        
        if is_verified is not None:
            user.is_verified = is_verified
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        return await self.get_user(admin_user, user_id)
    
    async def delete_user(
        self,
        admin_user: User,
        user_id: int
    ) -> None:
        """
        Delete a user.
        
        Args:
            admin_user: Admin user
            user_id: User ID
        """
        self._check_admin(admin_user)
        
        if user_id == admin_user.id:
            raise ValidationError("Cannot delete your own account")
        
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User not found")
        
        await self.db.delete(user)
        await self.db.commit()
    
    async def get_system_stats(self, admin_user: User) -> Dict[str, Any]:
        """
        Get system-wide statistics.
        
        Args:
            admin_user: Admin user
            
        Returns:
            System statistics
        """
        self._check_admin(admin_user)
        
        # Total users
        users_result = await self.db.execute(select(func.count(User.id)))
        total_users = users_result.scalar_one()
        
        # Active users (logged in within 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_result = await self.db.execute(
            select(func.count(User.id)).where(User.last_login >= thirty_days_ago)
        )
        active_users = active_result.scalar_one()
        
        # Total conversations
        sessions_result = await self.db.execute(select(func.count(ChatSession.id)))
        total_conversations = sessions_result.scalar_one()
        
        # Total messages
        messages_result = await self.db.execute(select(func.count(Conversation.id)))
        total_messages = messages_result.scalar_one()
        
        # Total documents
        docs_result = await self.db.execute(select(func.count(Document.id)))
        total_documents = docs_result.scalar_one()
        
        # Total reports
        reports_result = await self.db.execute(select(func.count(MedicalReport.id)))
        total_reports = reports_result.scalar_one()
        
        # Average confidence
        conf_result = await self.db.execute(
            select(func.avg(Conversation.confidence)).where(Conversation.confidence.isnot(None))
        )
        avg_confidence = conf_result.scalar_one() or 0.0
        
        # Average latency
        latency_result = await self.db.execute(
            select(func.avg(Conversation.latency_ms)).where(Conversation.latency_ms.isnot(None))
        )
        avg_latency_ms = latency_result.scalar_one() or 0.0
        
        # Total searches (API usage for search endpoints)
        search_result = await self.db.execute(
            select(func.count(APIUsage.id)).where(APIUsage.endpoint.like('%/search%'))
        )
        total_searches = search_result.scalar_one()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_documents": total_documents,
            "total_reports": total_reports,
            "total_searches": total_searches,
            "avg_confidence": float(avg_confidence),
            "avg_latency_ms": float(avg_latency_ms)
        }
    
    async def get_system_health(self, admin_user: User) -> Dict[str, Any]:
        """
        Get system health status.
        
        Args:
            admin_user: Admin user
            
        Returns:
            System health information
        """
        self._check_admin(admin_user)
        
        # Check database (already connected if we got here)
        database_status = "healthy"
        
        # Check vector DB (simplified - would need actual connection)
        vector_db_status = "healthy"
        
        # Check AI service (simplified - would need actual check)
        ai_service_status = "healthy"
        
        # System resources
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        overall_status = "healthy"
        if cpu_usage > 80 or memory.percent > 80 or disk.percent > 90:
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "database": database_status,
            "vector_db": vector_db_status,
            "ai_service": ai_service_status,
            "cpu_usage": cpu_usage,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent
        }
    
    async def get_activity_logs(
        self,
        admin_user: User,
        page: int = 1,
        page_size: int = 50,
        user_id: Optional[int] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get activity logs with pagination.
        
        Args:
            admin_user: Admin user
            page: Page number
            page_size: Items per page
            user_id: Filter by user ID
            endpoint: Filter by endpoint
            status_code: Filter by status code
            
        Returns:
            Tuple of (logs list, total count)
        """
        self._check_admin(admin_user)
        
        # Build query
        query = select(APIUsage, User.email).join(User, APIUsage.user_id == User.id)
        count_query = select(func.count(APIUsage.id))
        
        # Apply filters
        filters = []
        if user_id:
            filters.append(APIUsage.user_id == user_id)
        if endpoint:
            filters.append(APIUsage.endpoint.like(f"%{endpoint}%"))
        if status_code:
            filters.append(APIUsage.status_code == status_code)
        
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(desc(APIUsage.request_time)).offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "id": row.APIUsage.id,
                "user_id": row.APIUsage.user_id,
                "user_email": row.email,
                "action": row.APIUsage.method,
                "endpoint": row.APIUsage.endpoint,
                "status_code": row.APIUsage.status_code,
                "timestamp": row.APIUsage.request_time,
                "latency_ms": row.APIUsage.response_time_ms
            }
            for row in rows
        ], total
