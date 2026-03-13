"""Analytics Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.models import models
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone

class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_event(
        self,
        event_type: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_data: dict = None,
        meta_data: dict = None
    ) -> models.Analytics:
        """Log analytics event"""
        event = models.Analytics(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            agent_id=agent_id,
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
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[models.Analytics]:
        """Get analytics events"""
        query = select(models.Analytics)
        
        if tenant_id:
            query = query.where(models.Analytics.tenant_id == tenant_id)
        if user_id:
            query = query.where(models.Analytics.user_id == user_id)
        if agent_id:
            query = query.where(models.Analytics.agent_id == agent_id)
        if event_type:
            query = query.where(models.Analytics.event_type == event_type)
        
        query = query.order_by(desc(models.Analytics.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_recent_events(self, tenant_id: Optional[str] = None, hours: int = 24, limit: int = 100) -> List[models.Analytics]:
        """Get recent events"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = select(models.Analytics).where(models.Analytics.created_at >= since)
        if tenant_id:
            query = query.where(models.Analytics.tenant_id == tenant_id)
            
        result = await self.db.execute(
            query
            .order_by(desc(models.Analytics.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_api_hit_stats(self, tenant_id: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """Get API hit statistics"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        filters = [
            models.Analytics.event_type.in_(['api_hit', 'chat']),
            models.Analytics.created_at >= since
        ]
        if tenant_id:
            filters.append(models.Analytics.tenant_id == tenant_id)

        result = await self.db.execute(
            select(
                func.count(models.Analytics.id).label('total_hits'),
                func.count(func.distinct(models.Analytics.user_id)).label('unique_users')
            )
            .where(*filters)
        )
        row = result.first()
        
        return {
            "total_hits": row.total_hits if row else 0,
            "unique_users": row.unique_users if row else 0,
            "period_hours": hours
        }
    
    async def get_token_usage_stats(self, tenant_id: Optional[str] = None, hours: int = 24, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM token usage statistics"""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get all chat events with token data
        query = select(models.Analytics).where(
            models.Analytics.event_type == 'chat',
            models.Analytics.created_at >= since
        )
        
        if tenant_id:
            query = query.where(models.Analytics.tenant_id == tenant_id)
        
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



    async def get_usage_histogram(self, tenant_id: Optional[str] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get usage histogram grouped by hour."""
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=hours)

        query = select(models.Analytics).where(
            models.Analytics.created_at >= since,
            models.Analytics.event_type.in_(['chat', 'api_hit'])
        )
        if tenant_id:
            query = query.where(models.Analytics.tenant_id == tenant_id)
        query = query.order_by(models.Analytics.created_at)

        result = await self.db.execute(query)
        events = result.scalars().all()

        # Build hour-aligned buckets keyed by "YYYY-MM-DDTHH" (UTC)
        start_dt = since.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        buckets: dict = {}
        ordered_keys: list = []

        for i in range(hours + 1):
            slot_dt = start_dt + timedelta(hours=i)
            key = slot_dt.strftime("%Y-%m-%dT%H")
            buckets[key] = {
                "time": slot_dt.strftime("%H:%M"),
                "chats": 0,
                "hits": 0,
            }
            ordered_keys.append(key)

        for event in events:
            if not event.created_at:
                continue
            event_dt = event.created_at
            # Normalise to UTC-aware
            if event_dt.tzinfo is None:
                event_dt = event_dt.replace(tzinfo=timezone.utc)
            else:
                event_dt = event_dt.astimezone(timezone.utc)

            key = event_dt.strftime("%Y-%m-%dT%H")
            if key in buckets:
                if event.event_type == 'chat':
                    buckets[key]['chats'] += 1
                elif event.event_type == 'api_hit':
                    buckets[key]['hits'] += 1

        return [buckets[k] for k in ordered_keys[-hours:]]
