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
        event_data: dict = None,
        meta_data: dict = None
    ) -> models.Analytics:
        """Log analytics event"""
        event = models.Analytics(
            id=str(uuid.uuid4()),
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
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[models.Analytics]:
        """Get analytics events"""
        query = select(models.Analytics)
        
        if user_id:
            query = query.where(models.Analytics.user_id == user_id)
        if agent_id:
            query = query.where(models.Analytics.agent_id == agent_id)
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

        return {
            "total_requests": total_requests,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "avg_tokens_per_request": round((total_prompt_tokens + total_completion_tokens) / total_requests, 2) if total_requests > 0 else 0,
            "period_hours": hours
        }

    async def get_usage_histogram(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get usage histogram grouped by hour"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Fetch necessary fields only
        # We need created_at and event_type
        # To support SQLite (dev) and Postgres (prod) datetime handling, we'll fetch objects and group in Python
        # ideally we should use date_trunc for performance, but this is safer for now.
        
        # Increase limit to accommodate reasonable traffic, or remove limit? 
        # Removing limit is risky if millions of rows.
        # But for 'hours=12' it's probably fine.
        
        query = (
            select(models.Analytics)
            .where(
                models.Analytics.created_at >= since,
                models.Analytics.event_type.in_(['chat', 'api_hit'])
            )
            .order_by(models.Analytics.created_at)
        )
        
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        # Initialize buckets
        buckets = {}
        # Start from 'since' hour
        start_time = since.replace(minute=0, second=0, microsecond=0)
        
        # Create all hour keys up to now
        for i in range(hours + 1):
            h = start_time + timedelta(hours=i)
            key = h.strftime('%H:00')
            buckets[key] = {'time': key, 'chats': 0, 'hits': 0}
            
        # Fill buckets
        for event in events:
            if not event.created_at: continue
            
            # Simple hour extraction. 
            # Note: event.created_at should be timezone aware or naive UTC.
            # Assuming UTC.
            h_key = event.created_at.strftime('%H:00')
            
            if h_key in buckets:
                if event.event_type == 'chat':
                    buckets[h_key]['chats'] += 1
                elif event.event_type == 'api_hit':
                    buckets[h_key]['hits'] += 1
                    
        # Return as list
        # Sort by actual datetime logic if needed, but dict preservation helps?
        # Let's ensure order based on the initialization loop
        sorted_keys = []
        for i in range(hours + 1):
            h = start_time + timedelta(hours=i)
            sorted_keys.append(h.strftime('%H:00'))
            
        # We might have duplicates keys if crossing midnight? e.g. 23:00 today and 23:00 yesterday?
        # Yes! '12:00' is ambiguous if spanning > 24h.
        # But request is usually 12h or 24h.
        # If > 24h, the key collision happens.
        # For this specific chart (12h), strictly speaking we want relative ordering.
        # For now, let's trust the loop order and use a list of dicts directly.
        
        histogram = []
        
        # Re-initialize properly with unique slot tracking if needed, but for "12h" view:
        # Front end typically expects [{time: "10:00", ...}, {time: "11:00", ...}]
        # If we just return the full list in order, frontend maps it.
        
        # Better approach: List of objects in time order
        
        time_slots = []
        current = start_time
        now = datetime.utcnow()
        
        while current <= now + timedelta(hours=1): # buffer
            time_slots.append(current)
            current += timedelta(hours=1)
            
        # Map slots to data
        final_data = []
        for slot in time_slots:
            slot_key = slot.strftime('%H:00') 
            # We must be careful about which events belong here.
            # event.created_at matches slot if created_at.hour == slot.hour AND created_at.day == slot.day
            
            chats = 0
            hits = 0
            
            for event in events:
                # Basic match (ignoring seconds/minutes)
                if (event.created_at.year == slot.year and 
                    event.created_at.month == slot.month and 
                    event.created_at.day == slot.day and 
                    event.created_at.hour == slot.hour):
                    
                    if event.event_type == 'chat': chats += 1
                    elif event.event_type == 'api_hit': hits += 1
            
            final_data.append({
                "time": slot_key,
                "chats": chats,
                "hits": hits,
                # "iso": slot.isoformat() # Optional debugging
            })
            
        return final_data[-hours:] # Return only requested count
