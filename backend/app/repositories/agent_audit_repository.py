"""Agent Audit Log Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete as sql_delete
from app.models import models
from typing import List, Optional
import uuid

class AgentAuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_log(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: int = 0,
        user_message: Optional[str] = None,
        llm_response: Optional[str] = None,
        tool_calls: list = None,
        rag_context: dict = None,
        ip_address: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> models.AgentAuditLog:
        """Create agent audit log entry"""
        log = models.AgentAuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            user_message=user_message,
            llm_response=llm_response,
            tool_calls=tool_calls or [],
            rag_context=rag_context or {},
            ip_address=ip_address,
            status=status,
            error_message=error_message
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def get_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[models.AgentAuditLog]:
        """Get agent audit logs"""
        query = select(models.AgentAuditLog)
        
        if tenant_id:
            query = query.join(models.Agent).where(models.Agent.tenant_id == tenant_id)
            
        if user_id:
            query = query.where(models.AgentAuditLog.user_id == user_id)
        if agent_id:
            query = query.where(models.AgentAuditLog.agent_id == agent_id)
        if session_id:
            query = query.where(models.AgentAuditLog.session_id == session_id)
        
        query = query.order_by(desc(models.AgentAuditLog.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete_logs(self, user_id: Optional[str] = None, tenant_id: Optional[str] = None):
        """Delete agent audit logs"""
        if user_id and tenant_id:
            # Delete user logs in tenant
             stmt = sql_delete(models.AgentAuditLog).where(
                 models.AgentAuditLog.user_id == user_id,
                 models.AgentAuditLog.agent_id.in_(
                     select(models.Agent.id).where(models.Agent.tenant_id == tenant_id)
                 )
             )
        elif tenant_id:
            # Delete all logs in tenant
            stmt = sql_delete(models.AgentAuditLog).where(
                 models.AgentAuditLog.agent_id.in_(
                     select(models.Agent.id).where(models.Agent.tenant_id == tenant_id)
                 )
             )
        elif user_id:
            stmt = sql_delete(models.AgentAuditLog).where(models.AgentAuditLog.user_id == user_id)
        else:
            stmt = sql_delete(models.AgentAuditLog)
        
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_top_agents_by_tokens(self, tenant_id: str, limit: int = 5) -> List[dict]:
        """Get top agents by token usage"""
        from sqlalchemy import func
        
        # Select agent_id, agent_name, sum(tokens)
        query = (
            select(
                models.AgentAuditLog.agent_id,
                models.Agent.name.label("agent_name"),
                func.sum(models.AgentAuditLog.total_tokens).label("total_tokens")
            )
            .join(models.Agent, models.AgentAuditLog.agent_id == models.Agent.id)
            .where(models.Agent.tenant_id == tenant_id)
            .group_by(models.AgentAuditLog.agent_id, models.Agent.name)
            .order_by(desc("total_tokens"))
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "agent_id": row.agent_id,
                "name": row.agent_name,
                "tokens": row.total_tokens or 0
            }
            for row in rows
        ]
