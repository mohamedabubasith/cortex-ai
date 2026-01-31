"""Analytics & Audit Router"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.audit_repository import AuditLogRepository
from app.repositories.agent_audit_repository import AgentAuditLogRepository
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.agent_audit_service import AgentAuditService
from app.services.agent_audit_service import AgentAuditService
from app.services.auth_service import get_current_active_user, get_current_tenant

router = APIRouter()

def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(AnalyticsRepository(db))

def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(AuditLogRepository(db))

def get_agent_audit_service(db: AsyncSession = Depends(get_db)) -> AgentAuditService:
    return AgentAuditService(AgentAuditLogRepository(db))

@router.get("/events")
async def get_analytics_events(
    event_type: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    hours: Optional[int] = Query(24),
    limit: int = Query(100, le=1000),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics events"""
    if hours:
        return await analytics_service.get_recent_events(tenant_id=current_tenant.id, hours=hours, limit=limit)
    else:
        return await analytics_service.get_events(
            tenant_id=current_tenant.id,
            user_id=current_user.id,
            agent_id=agent_id,
            event_type=event_type,
            limit=limit
        )

@router.get("/live")
async def get_live_analytics(
    limit: int = Query(50, le=100),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get live analytics (last 1 hour)"""
    return await analytics_service.get_recent_events(tenant_id=current_tenant.id, hours=1, limit=limit)

@router.get("/audit/logs")
async def get_audit_logs(
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    hours: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    audit_service: AuditService = Depends(get_audit_service)
):
    """Get audit logs - admins see all tenant logs, users see only their own"""
    
    # Check Role
    is_tenant_admin = False
    for member in current_user.tenant_memberships:
        if member.tenant_id == current_tenant.id:
             role_name = member.role.lower() if hasattr(member.role, 'lower') else str(member.role).lower()
             if role_name in ["owner", "admin"]:
                is_tenant_admin = True
                break
            
    if current_user.is_superuser:
        # Global Admin: show all logs (ignoring tenant for now, or maybe global logs)
        # Assuming we want tenant context even for superuser?
        # Let's show tenant logs for now + null tenant logs?
        # For safety, let's treat Superuser as Tenant Admin of current tenant + more.
        return await audit_service.get_logs(
            tenant_id=current_tenant.id, # Or None for global?
            resource_type=resource_type,
            action=action,
            limit=limit
        )
    elif is_tenant_admin:
        # Tenant Admin: show all tenant logs
        if hours:
            return await audit_service.get_recent_logs(tenant_id=current_tenant.id, hours=hours, limit=limit)
        else:
            return await audit_service.get_logs(
                tenant_id=current_tenant.id,
                resource_type=resource_type,
                action=action,
                limit=limit
            )
    else:
        # Regular user: show only their own logs in this tenant
        return await audit_service.get_logs(
            user_id=current_user.id,
            tenant_id=current_tenant.id,
            resource_type=resource_type,
            action=action,
            limit=limit
        )

@router.delete("/audit/logs")
async def clear_audit_logs(
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Clear audit logs - users clear their own, admins clear all in tenant"""
    from sqlalchemy import delete
    
    # Check Role
    is_tenant_admin = False
    for member in current_user.tenant_memberships:
        if member.tenant_id == current_tenant.id:
             role_name = member.role.lower() if hasattr(member.role, 'lower') else str(member.role).lower()
             if role_name in ["owner", "admin"]:
                is_tenant_admin = True
                break
            
    if current_user.is_superuser:
        # Admin: clear all logs (Global? Or Tenant?)
        # Let's clear tenant logs for safety
        stmt = delete(models.AuditLog).where(models.AuditLog.tenant_id == current_tenant.id)
    elif is_tenant_admin:
         # Tenant Admin: clear tenant logs
        stmt = delete(models.AuditLog).where(models.AuditLog.tenant_id == current_tenant.id)
    else:
        # Regular user: clear only their own logs in tenant
        stmt = delete(models.AuditLog).where(
            models.AuditLog.user_id == current_user.id,
            models.AuditLog.tenant_id == current_tenant.id
        )
    
    await db.execute(stmt)
    await db.commit()
    
    return {"message": "Audit logs cleared"}

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
    current_tenant: models.Tenant = Depends(get_current_tenant),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get API hit statistics"""
    return await analytics_service.get_api_hit_stats(tenant_id=current_tenant.id, hours=hours)

@router.get("/stats/tokens")
async def get_token_usage_stats(
    hours: int = Query(24, le=168),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get LLM token usage statistics"""
    # For regular users, we filter by user_id + tenant_id
    # If admin (owner/admin), maybe show all tenant tokens?
    # Logic: current_user.id is always passed in original code, implying per-user stats?
    # The original code passed user_id=current_user.id. Use that to be safe + tenant isolation.
    return await analytics_service.get_token_usage_stats(tenant_id=current_tenant.id, hours=hours, user_id=current_user.id)

@router.get("/stats/overview")
async def get_stats_overview(
    hours: int = Query(24, le=168),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get overview statistics"""
    hits = await analytics_service.get_api_hit_stats(tenant_id=current_tenant.id, hours=hours)
    tokens = await analytics_service.get_token_usage_stats(tenant_id=current_tenant.id, hours=hours, user_id=current_user.id)
    
    return {
        "api_hits": hits,
        "token_usage": tokens,
        "period_hours": hours
    }

@router.get("/stats/usage")
async def get_usage_stats(
    hours: int = Query(24, le=168),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get usage histogram"""
    return await analytics_service.get_usage_histogram(tenant_id=current_tenant.id, hours=hours)

@router.get("/stats/agents")
async def get_top_agents_stats(
    limit: int = Query(5, le=20),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    agent_audit_service: AgentAuditService = Depends(get_agent_audit_service)
):
    """Get top agents by token usage"""
    return await agent_audit_service.get_top_agents_by_tokens(tenant_id=current_tenant.id, limit=limit)

# Agent Audit Log Endpoints
@router.get("/agent-audit/logs")
async def get_agent_audit_logs(
    agent_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    agent_audit_service: AgentAuditService = Depends(get_agent_audit_service)
):
    """Get agent audit logs - users see their own, admins see all in tenant"""
    
    # Check Role
    is_tenant_admin = False
    for member in current_user.tenant_memberships:
        if member.tenant_id == current_tenant.id:
            # Check role (handle both string and possible relationship access if needed, but assuming string based on existing code)
            # Existing code was: member.role in ["owner", "admin"]
            # We'll make it case-insensitive
            role_name = member.role.lower() if hasattr(member.role, 'lower') else str(member.role).lower()
            if role_name in ["owner", "admin"]:
                is_tenant_admin = True
                break
            
    if current_user.is_superuser:
        # Admin: show all logs (Global? Or Tenant Join?)
        # Pass tenant_id to filter by tenant context
        return await agent_audit_service.get_logs(
            tenant_id=current_tenant.id, 
            agent_id=agent_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
    elif is_tenant_admin:
         # Tenant Admin: show all logs in tenant
        return await agent_audit_service.get_logs(
            tenant_id=current_tenant.id,
            agent_id=agent_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
    else:
        # Regular user: show only their own logs in tenant
        # We pass both user_id and tenant_id for extra safety, though user_id implies ownership.
        return await agent_audit_service.get_logs(
            user_id=current_user.id,
            tenant_id=current_tenant.id,
            agent_id=agent_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )

@router.delete("/agent-audit/logs")
async def clear_agent_audit_logs(
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    agent_audit_service: AgentAuditService = Depends(get_agent_audit_service)
):
    """Clear agent audit logs - users clear their own, admins clear all in tenant"""
    
    # Check Role
    is_tenant_admin = False
    for member in current_user.tenant_memberships:
        if member.tenant_id == current_tenant.id:
            # Check role (handle both string and possible relationship access if needed, but assuming string based on existing code)
            # Existing code was: member.role in ["owner", "admin"]
            # We'll make it case-insensitive
            role_name = member.role.lower() if hasattr(member.role, 'lower') else str(member.role).lower()
            if role_name in ["owner", "admin"]:
                is_tenant_admin = True
                break
            
    if current_user.is_superuser or is_tenant_admin:
        # Admin: clear all logs in tenant
        await agent_audit_service.delete_logs(tenant_id=current_tenant.id)
    else:
        # Regular user: clear only their own logs
        await agent_audit_service.delete_logs(user_id=current_user.id, tenant_id=current_tenant.id)
    
    return {"message": "Agent audit logs cleared"}
