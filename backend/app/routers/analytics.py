"""Analytics & Audit Router"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.audit_repository import AuditLogRepository
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.auth_service import get_current_active_user

router = APIRouter()

def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(db))

def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(AuditLogRepository(db))

@router.get("/events")
async def get_analytics_events(
    event_type: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    hours: Optional[int] = Query(24),
    limit: int = Query(100, le=1000),
    current_user: models.User = Depends(get_current_active_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics events"""
    if hours:
        return await analytics_service.get_recent_events(hours=hours, limit=limit)
    else:
        return await analytics_service.get_events(
            user_id=current_user.id,
            agent_id=agent_id,
            event_type=event_type,
            limit=limit
        )

@router.get("/live")
async def get_live_analytics(
    limit: int = Query(50, le=100),
    current_user: models.User = Depends(get_current_active_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get live analytics (last 1 hour)"""
    return await analytics_service.get_recent_events(hours=1, limit=limit)

@router.get("/audit/logs")
async def get_audit_logs(
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    hours: Optional[int] = Query(24),
    limit: int = Query(100, le=1000),
    current_user: models.User = Depends(get_current_active_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Get audit logs"""
    if hours:
        return await audit_service.get_recent_logs(hours=hours, limit=limit)
    else:
        return await audit_service.get_logs(
            user_id=current_user.id,
            resource_type=resource_type,
            action=action,
            limit=limit
        )

@router.get("/audit/live")
async def get_live_audit_logs(
    limit: int = Query(50, le=100),
    current_user: models.User = Depends(get_current_active_user),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Get live audit logs (last 1 hour)"""
    return await audit_service.get_recent_logs(hours=1, limit=limit)

@router.get("/stats/hits")
async def get_api_hit_stats(
    hours: int = Query(24, le=168),
    current_user: models.User = Depends(get_current_active_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get API hit statistics"""
    return await analytics_service.get_api_hit_stats(hours=hours)

@router.get("/stats/tokens")
async def get_token_usage_stats(
    hours: int = Query(24, le=168),
    current_user: models.User = Depends(get_current_active_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get LLM token usage statistics"""
    return await analytics_service.get_token_usage_stats(hours=hours, user_id=current_user.id)

@router.get("/stats/overview")
async def get_stats_overview(
    hours: int = Query(24, le=168),
    current_user: models.User = Depends(get_current_active_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get overview statistics"""
    hits = await analytics_service.get_api_hit_stats(hours=hours)
    tokens = await analytics_service.get_token_usage_stats(hours=hours, user_id=current_user.id)
    
    return {
        "api_hits": hits,
        "token_usage": tokens,
        "period_hours": hours
    }
