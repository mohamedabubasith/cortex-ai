from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import shutil
import os
import uuid

from app.models import models
from app.schemas import schemas
from app.repositories.agent_repository import AgentRepository
from app.services.mcp_service import mcp_service
from app.services.access_control_service import AccessControlService

from sqlalchemy.orm import selectinload

class AgentService:
    def __init__(self, db: AsyncSession, repo: AgentRepository, access_service: AccessControlService):
        self.db = db
        self.repo = repo
        self.access_service = access_service

    async def create_agent(self, agent_in: schemas.AgentCreate, user: models.User, tenant_id: str) -> models.Agent:
        agent_data = agent_in.dict(exclude={"kb_ids", "db_connection_ids", "mcp_connection_ids"})
        
        agent = await self.repo.create(
            agent_data,
            user_id=user.id,
            tenant_id=tenant_id
        )
        
        # Link Resources
        if agent_in.kb_ids:
            await self._link_kbs(agent, agent_in.kb_ids)
        if agent_in.db_connection_ids:
            await self._link_dbs(agent, agent_in.db_connection_ids)
        if agent_in.mcp_connection_ids:
            await self._link_mcps(agent, agent_in.mcp_connection_ids)
            
        # Refresh with relationships loaded
        return await self.get_agent(agent.id, user, tenant_id)

    async def _link_kbs(self, agent: models.Agent, kb_ids: List[str]):
        stmt = select(models.KnowledgeBase).where(models.KnowledgeBase.id.in_(kb_ids))
        result = await self.db.execute(stmt)
        kbs = result.scalars().all()
        agent.knowledge_bases = kbs
        await self.db.commit()

    async def _link_dbs(self, agent: models.Agent, db_ids: List[str]):
        stmt = select(models.DatabaseConnection).where(models.DatabaseConnection.id.in_(db_ids))
        result = await self.db.execute(stmt)
        dbs = result.scalars().all()
        agent.database_connections = dbs
        await self.db.commit()

    async def _link_mcps(self, agent: models.Agent, mcp_ids: List[str]):
        stmt = select(models.MCPConnection).where(models.MCPConnection.id.in_(mcp_ids))
        result = await self.db.execute(stmt)
        mcps = result.scalars().all()
        agent.mcp_connections = mcps
        await self.db.commit()

    async def get_agents(self, user: models.User, tenant_id: str, skip: int = 0, limit: int = 100) -> List[models.Agent]:
        """
        List agents accessible to user:
        1. Agents they own
        2. Agents in tenants where they're a member (if owner/admin role)
        3. Agents explicitly shared with them
        """
        from sqlalchemy import or_, select as sql_select
        from app.models.models import TenantMember, ResourceAccess
        
        # Get all tenant IDs where user is a member
        tenant_query = sql_select(TenantMember.tenant_id).where(
            TenantMember.user_id == user.id
        )
        tenant_result = await self.db.execute(tenant_query)
        user_tenant_ids = [row[0] for row in tenant_result.fetchall()]
        
        # Build query with eager loading
        stmt = select(models.Agent).offset(skip).limit(limit).options(
            selectinload(models.Agent.knowledge_bases),
            selectinload(models.Agent.database_connections),
            selectinload(models.Agent.mcp_connections),
            selectinload(models.Agent.llm_config)
        )
        
        # Filter logic
        if not user.is_superuser:
            conditions = []
            
            # 1. Agents in user's tenants
            if user_tenant_ids:
                conditions.append(models.Agent.tenant_id.in_(user_tenant_ids))
            
            # 2. Agents owned by user (even if in different tenant)
            conditions.append(models.Agent.owner_id == user.id)
            
            # 3. Agents explicitly shared with user
            shared_query = sql_select(ResourceAccess.resource_id).where(
                ResourceAccess.user_id == user.id,
                ResourceAccess.resource_type == "agent"
            )
            shared_result = await self.db.execute(shared_query)
            shared_agent_ids = [row[0] for row in shared_result.fetchall()]
            if shared_agent_ids:
                conditions.append(models.Agent.id.in_(shared_agent_ids))
            
            stmt = stmt.where(or_(*conditions))
            
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_agent(self, agent_id: str, user: models.User, tenant_id: str) -> models.Agent:
        # First fetch the agent to get its tenant_id
        stmt = select(models.Agent).where(models.Agent.id == agent_id).options(
            selectinload(models.Agent.knowledge_bases),
            selectinload(models.Agent.database_connections),
            selectinload(models.Agent.mcp_connections),
            selectinload(models.Agent.llm_config)
        )
        result = await self.db.execute(stmt)
        agent = result.scalars().first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check permissions using the RESOURCE's tenant_id for role-based sharing
        # This allows role-based access across tenants if shared
        resource_tenant_id = agent.tenant_id if agent.tenant_id else tenant_id
        if not await self.access_service.has_access(user, agent_id, "agent", "viewer", resource_tenant_id):
            raise HTTPException(status_code=403, detail="Access Denied")

        return agent

    async def update_agent(self, agent_id: str, agent_update: schemas.AgentUpdate, user: models.User, tenant_id: str) -> models.Agent:
        # Requires Editor access
        if not await self.access_service.has_access(user, agent_id, "agent", "editor", tenant_id):
            raise HTTPException(status_code=403, detail="Access Denied")
            
        agent = await self.get_agent(agent_id, user, tenant_id)
        
        update_data = agent_update.dict(exclude_unset=True, exclude={"kb_ids", "db_connection_ids", "mcp_connection_ids"})
        for key, value in update_data.items():
            setattr(agent, key, value)
            
        if agent_update.kb_ids is not None:
            await self._link_kbs(agent, agent_update.kb_ids)
            
        if agent_update.db_connection_ids is not None:
            await self._link_dbs(agent, agent_update.db_connection_ids)
            
        if agent_update.mcp_connection_ids is not None:
            await self._link_mcps(agent, agent_update.mcp_connection_ids)
            
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def delete_agent(self, agent_id: str, user: models.User, tenant_id: str):
        # Requires Admin access
        if not await self.access_service.has_access(user, agent_id, "agent", "admin", tenant_id):
            raise HTTPException(status_code=403, detail="Access Denied")
            
        agent = await self.get_agent(agent_id, user, tenant_id)
        await self.db.delete(agent)
        await self.db.commit()
        return {"status": "success", "message": "Agent deleted"}

    async def regenerate_share_url(self, agent_id: str, user: models.User, tenant_id: str) -> models.Agent:
        # Requires Admin access to change visibility settings
        if not await self.access_service.has_access(user, agent_id, "agent", "admin", tenant_id):
            raise HTTPException(status_code=403, detail="Access Denied")
            
        agent = await self.get_agent(agent_id, user, tenant_id)
        agent.share_token = str(uuid.uuid4())
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def update_mcp_config(self, agent_id: str, config: schemas.MCPConfig, user: models.User, tenant_id: str):
        if not await self.access_service.has_access(user, agent_id, "agent", "editor", tenant_id):
            raise HTTPException(status_code=403, detail="Access Denied")
            
        agent = await self.get_agent(agent_id, user, tenant_id)
        agent.mcp_config = config.dict()
        await self.db.commit()
        
        is_connected = await mcp_service.test_connection(config.server_url)
        return {"status": "success", "connected": is_connected}
