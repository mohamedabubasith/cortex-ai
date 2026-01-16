"""Audit Log Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models import models
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_log(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        details: dict = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> models.AuditLog:
        """Create audit log entry"""
        log = models.AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[models.AuditLog]:
        """Get audit logs"""
        query = select(models.AuditLog)
        
        if user_id:
            query = query.where(models.AuditLog.user_id == user_id)
        if tenant_id:
            query = query.where(models.AuditLog.tenant_id == tenant_id)
        if resource_type:
            query = query.where(models.AuditLog.resource_type == resource_type)
        if action:
            query = query.where(models.AuditLog.action == action)
        
        query = query.order_by(desc(models.AuditLog.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_recent_logs(self, hours: int = 24, limit: int = 100) -> List[models.AuditLog]:
        """Get recent logs"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(models.AuditLog)
            .where(models.AuditLog.created_at >= since)
            .order_by(desc(models.AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()
