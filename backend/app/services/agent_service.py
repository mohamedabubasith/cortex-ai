from typing import List, Optional
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

from sqlalchemy.orm import selectinload

class AgentService:
    def __init__(self, db: AsyncSession):
        # self.repo = ProjectRepository(models.Agent, db) # Assuming repo is generic or we use db directly
        self.db = db

    async def create_agent(self, agent_in: schemas.AgentCreate, owner_id: str) -> models.Agent:
        agent_data = agent_in.dict(exclude={"kb_ids", "db_connection_ids", "mcp_connection_ids"})
        agent_data["owner_id"] = owner_id
        
        agent = models.Agent(**agent_data)
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        
        # Link Resources
        if agent_in.kb_ids:
            await self._link_kbs(agent, agent_in.kb_ids)
        if agent_in.db_connection_ids:
            await self._link_dbs(agent, agent_in.db_connection_ids)
        if agent_in.mcp_connection_ids:
            await self._link_mcps(agent, agent_in.mcp_connection_ids)
            
        # Refresh with relationships loaded
        stmt = select(models.Agent).where(models.Agent.id == agent.id).options(
            selectinload(models.Agent.knowledge_bases),
            selectinload(models.Agent.database_connections),
            selectinload(models.Agent.mcp_connections),
            selectinload(models.Agent.llm_config)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _link_kbs(self, agent: models.Agent, kb_ids: List[str]):
        # Clear existing links if needed, or just add new ones
        # For simplicity, we'll just add valid ones
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

    async def get_agents(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[models.Agent]:
        # Need to eager load relationships
        stmt = select(models.Agent).where(models.Agent.owner_id == owner_id).offset(skip).limit(limit).options(
            selectinload(models.Agent.knowledge_bases),
            selectinload(models.Agent.database_connections),
            selectinload(models.Agent.mcp_connections),
            selectinload(models.Agent.llm_config)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_agent(self, agent_id: str, owner_id: str) -> models.Agent:
        stmt = select(models.Agent).where(models.Agent.id == agent_id, models.Agent.owner_id == owner_id).options(
            selectinload(models.Agent.knowledge_bases),
            selectinload(models.Agent.database_connections),
            selectinload(models.Agent.mcp_connections),
            selectinload(models.Agent.llm_config)
        )
        result = await self.db.execute(stmt)
        agent = result.scalars().first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    async def update_agent(self, agent_id: str, agent_update: schemas.AgentUpdate, owner_id: str) -> models.Agent:
        agent = await self.get_agent(agent_id, owner_id)
        
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

    async def delete_agent(self, agent_id: str, owner_id: str):
        agent = await self.get_agent(agent_id, owner_id)
        await self.db.delete(agent)
        await self.db.commit()
        return {"status": "success", "message": "Agent deleted"}

    async def regenerate_share_url(self, agent_id: str, owner_id: str) -> models.Agent:
        agent = await self.get_agent(agent_id, owner_id)
        agent.share_token = str(uuid.uuid4())
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def update_mcp_config(self, agent_id: str, config: schemas.MCPConfig, owner_id: str):
        agent = await self.get_agent(agent_id, owner_id)
        agent.mcp_config = config.dict()
        await self.db.commit()
        
        is_connected = await mcp_service.test_connection(config.server_url)
        return {"status": "success", "connected": is_connected}
