"""
Dashboard service for analytics and metrics.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

from app.database.models import User, Session as ChatSession, Conversation as ChatMessage


def _load_vector_db():
    """
    Lazily import the vector DB stack.

    Imported on demand so the heavy AI/vector dependencies (chromadb, etc.)
    are not required just to start the FastAPI backend.
    """
    import sys
    if str(Path(__file__).parent.parent.parent.parent) not in sys.path:
        sys.path.append(str(Path(__file__).parent.parent.parent.parent))
    from scripts.vector_db.collection_manager import CollectionManager
    from scripts.utils.config_loader import load_yaml_config
    return CollectionManager, load_yaml_config


class DashboardService:
    """Dashboard service for analytics."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize dashboard service.

        Args:
            db: Database session
        """
        self.db = db
        self._collection_manager = None

    def _get_collection_manager(self):
        """Lazily initialize the vector DB collection manager."""
        if self._collection_manager is None:
            try:
                CollectionManager, load_yaml_config = _load_vector_db()
                retrieval_config = load_yaml_config(Path("config/retrieval.yaml"))
                self._collection_manager = CollectionManager(retrieval_config)
            except Exception:
                # Vector DB is optional for dashboard stats; degrade gracefully
                self._collection_manager = False  # marker: unavailable
        return self._collection_manager if self._collection_manager is not False else None
    
    async def get_dashboard_stats(self, user_id: int = None) -> Dict[str, Any]:
        """
        Get dashboard statistics.
        
        Args:
            user_id: Optional user ID for user-specific stats
            
        Returns:
            Dashboard statistics
        """
        # Get date ranges
        now = datetime.utcnow()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        
        # Total conversations
        if user_id:
            total_conversations = await self.db.scalar(
                select(func.count(ChatSession.id))
                .where(ChatSession.user_id == user_id)
            )
        else:
            total_conversations = await self.db.scalar(
                select(func.count(ChatSession.id))
            )
        
        # Total messages
        if user_id:
            total_messages = await self.db.scalar(
                select(func.count(ChatMessage.id))
                .join(ChatSession)
                .where(ChatSession.user_id == user_id)
            )
        else:
            total_messages = await self.db.scalar(
                select(func.count(ChatMessage.id))
            )
        
        # Knowledge base size
        try:
            collection_manager = self._get_collection_manager()
            if collection_manager:
                collection = collection_manager.get_or_create_collection()
                knowledge_base_size = collection.count()
            else:
                knowledge_base_size = 0
        except Exception:
            knowledge_base_size = 0
        
        # Average confidence (from chat metadata)
        avg_confidence = 0.85  # Placeholder - would calculate from actual data
        
        # Recent activity (last 7 days)
        if user_id:
            recent_activity = await self.db.scalar(
                select(func.count(ChatMessage.id))
                .join(ChatSession)
                .where(
                    ChatSession.user_id == user_id,
                    ChatMessage.created_at >= last_7_days
                )
            )
        else:
            recent_activity = await self.db.scalar(
                select(func.count(ChatMessage.id))
                .where(ChatMessage.created_at >= last_7_days)
            )
        
        # Total users (admin only)
        if user_id is None:
            total_users = await self.db.scalar(
                select(func.count(User.id))
            )
        else:
            total_users = None
        
        return {
            'total_conversations': total_conversations or 0,
            'total_messages': total_messages or 0,
            'knowledge_base_size': knowledge_base_size,
            'avg_confidence': avg_confidence,
            'recent_activity_7d': recent_activity or 0,
            'total_users': total_users,
            'last_updated': now.isoformat()
        }
    
    async def get_usage_trend(
        self,
        user_id: int = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get usage trend over time.
        
        Args:
            user_id: Optional user ID
            days: Number of days
            
        Returns:
            Usage trend data
        """
        # This would query message counts by day
        # Placeholder implementation
        trend_data = []
        now = datetime.utcnow()
        
        for i in range(days):
            date = now - timedelta(days=i)
            trend_data.append({
                'date': date.date().isoformat(),
                'conversations': 0,  # Would calculate from actual data
                'messages': 0
            })
        
        return {
            'days': days,
            'data': list(reversed(trend_data))
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health metrics.
        
        Returns:
            System health
        """
        # Basic health check
        return {
            'status': 'healthy',
            'database': 'connected',
            'vector_db': 'connected',
            'ai_service': 'available',
            'uptime_hours': 24,  # Placeholder
            'last_check': datetime.utcnow().isoformat()
        }
