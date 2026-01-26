"""Audit Service"""
from typing import List, Optional
from app.repositories.audit_repository import AuditLogRepository

class AuditService:
    def __init__(self, audit_repo: AuditLogRepository):
        self.audit_repo = audit_repo
    
    async def log_action(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: dict = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log an audit action"""
        return await self.audit_repo.create_log(
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            tenant_id=tenant_id,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def get_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ):
        """Get audit logs"""
        return await self.audit_repo.get_logs(
            user_id=user_id,
            tenant_id=tenant_id,
            resource_type=resource_type,
            action=action,
            limit=limit
        )
    
    async def get_recent_logs(self, tenant_id: Optional[str] = None, hours: int = 24, limit: int = 100):
        """Get recent logs"""
        return await self.audit_repo.get_recent_logs(tenant_id=tenant_id, hours=hours, limit=limit)
