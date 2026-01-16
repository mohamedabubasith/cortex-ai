"""Analytics Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.models import models
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta

class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        event_data: dict = None,
        meta_data: dict = None
    ) -> models.Analytics:
        """Log analytics event"""
        event = models.Analytics(
            id=str(uuid.uuid4()),
            user_id=user_id,
            agent_id=agent_id,
            tenant_id=tenant_id,
            event_type=event_type,
            event_data=event_data or {},
            meta_data=meta_data or {}
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event
    
    async def get_events(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[models.Analytics]:
        """Get analytics events"""
        query = select(models.Analytics)
        
        if user_id:
            query = query.where(models.Analytics.user_id == user_id)
        if agent_id:
            query = query.where(models.Analytics.agent_id == agent_id)
        if tenant_id:
            query = query.where(models.Analytics.tenant_id == tenant_id)
        if event_type:
            query = query.where(models.Analytics.event_type == event_type)
        
        query = query.order_by(desc(models.Analytics.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_recent_events(self, hours: int = 24, limit: int = 100) -> List[models.Analytics]:
        """Get recent events"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(models.Analytics)
            .where(models.Analytics.created_at >= since)
            .order_by(desc(models.Analytics.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_api_hit_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get API hit statistics"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(
                func.count(models.Analytics.id).label('total_hits'),
                func.count(func.distinct(models.Analytics.user_id)).label('unique_users')
            )
            .where(
                models.Analytics.event_type.in_(['api_hit', 'chat']),
                models.Analytics.created_at >= since
            )
        )
        row = result.first()
        
        return {
            "total_hits": row.total_hits if row else 0,
            "unique_users": row.unique_users if row else 0,
            "period_hours": hours
        }
    
    async def get_token_usage_stats(self, hours: int = 24, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM token usage statistics"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get all chat events with token data
        query = select(models.Analytics).where(
            models.Analytics.event_type == 'chat',
            models.Analytics.created_at >= since
        )
        
        if user_id:
            query = query.where(models.Analytics.user_id == user_id)
        
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_requests = 0
        
        for event in events:
            if event.event_data and 'tokens' in event.event_data:
                tokens = event.event_data['tokens']
                total_prompt_tokens += tokens.get('prompt_tokens', 0)
                total_completion_tokens += tokens.get('completion_tokens', 0)
                total_requests += 1
        
        return {
            "total_requests": total_requests,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "avg_tokens_per_request": round((total_prompt_tokens + total_completion_tokens) / total_requests, 2) if total_requests > 0 else 0,
            "period_hours": hours
        }
