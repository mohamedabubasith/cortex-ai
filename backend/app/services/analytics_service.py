"""Analytics Service"""
from typing import List, Optional
from app.repositories.analytics_repository import AnalyticsRepository

class AnalyticsService:
    def __init__(self, analytics_repo: AnalyticsRepository):
        self.analytics_repo = analytics_repo
    
    async def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_data: dict = None,
        metadata: dict = None
    ):
        """Log an analytics event"""
        return await self.analytics_repo.create_event(
            event_type=event_type,
            user_id=user_id,
            agent_id=agent_id,
            event_data=event_data,
            metadata=metadata
        )
    
    async def get_events(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ):
        """Get analytics events"""
        return await self.analytics_repo.get_events(
            user_id=user_id,
            agent_id=agent_id,
            event_type=event_type,
            limit=limit
        )
    
    async def get_recent_events(self, hours: int = 24, limit: int = 100):
        """Get recent events"""
        return await self.analytics_repo.get_recent_events(hours=hours, limit=limit)
    
    async def get_api_hit_stats(self, hours: int = 24):
        """Get API hit statistics"""
        return await self.analytics_repo.get_api_hit_stats(hours=hours)
    
    async def get_token_usage_stats(self, hours: int = 24, user_id: str = None):
        """Get token usage statistics"""
        return await self.analytics_repo.get_token_usage_stats(hours=hours, user_id=user_id)
