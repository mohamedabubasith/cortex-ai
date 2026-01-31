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
            meta_data=metadata
        )
    
    async def get_events(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ):
        """Get analytics events"""
        return await self.analytics_repo.get_events(
            tenant_id=tenant_id,
            user_id=user_id,
            agent_id=agent_id,
            event_type=event_type,
            limit=limit
        )
    
    async def get_recent_events(self, tenant_id: str = None, hours: int = 24, limit: int = 100):
        """Get recent events"""
        return await self.analytics_repo.get_recent_events(tenant_id=tenant_id, hours=hours, limit=limit)
    
    async def get_api_hit_stats(self, tenant_id: str = None, hours: int = 24):
        """Get API hit statistics"""
        return await self.analytics_repo.get_api_hit_stats(tenant_id=tenant_id, hours=hours)
    
    async def get_token_usage_stats(self, tenant_id: str = None, hours: int = 24, user_id: str = None):
        """Get token usage statistics"""
        return await self.analytics_repo.get_token_usage_stats(tenant_id=tenant_id, hours=hours, user_id=user_id)

    async def get_usage_histogram(self, tenant_id: str = None, hours: int = 24):
        """Get usage histogram"""
        return await self.analytics_repo.get_usage_histogram(tenant_id=tenant_id, hours=hours)
