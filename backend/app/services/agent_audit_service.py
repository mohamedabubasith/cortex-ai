"""Agent Audit Service"""
from typing import List, Optional
from app.repositories.agent_audit_repository import AgentAuditLogRepository

class AgentAuditService:
    def __init__(self, agent_audit_repo: AgentAuditLogRepository):
        self.agent_audit_repo = agent_audit_repo
    
    async def log_interaction(
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
    ):
        """Log an agent/LLM interaction"""
        return await self.agent_audit_repo.create_log(
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
            tool_calls=tool_calls,
            rag_context=rag_context,
            ip_address=ip_address,
            status=status,
            error_message=error_message
        )
    
    async def get_logs(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """Get agent audit logs"""
        return await self.agent_audit_repo.get_logs(
            user_id=user_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
    
    async def delete_logs(self, user_id: Optional[str] = None, tenant_id: Optional[str] = None):
        """Delete agent audit logs"""
        return await self.agent_audit_repo.delete_logs(user_id=user_id, tenant_id=tenant_id)
        
    async def get_top_agents_by_tokens(self, tenant_id: str, limit: int = 5):
        """Get top agents by token usage"""
        return await self.agent_audit_repo.get_top_agents_by_tokens(tenant_id=tenant_id, limit=limit)
