from typing import List, Optional
from sqlalchemy import select
from app.models.models import Agent, KnowledgeBase
from app.repositories.base_repository import BaseRepository

from sqlalchemy.orm import selectinload

class AgentRepository(BaseRepository[Agent]):
    async def get_by_owner(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[Agent]:
        result = await self.db.execute(
            select(self.model)
            .where(self.model.owner_id == owner_id)
            .options(
                selectinload(self.model.llm_config),
                selectinload(self.model.knowledge_bases),
                selectinload(self.model.database_connections)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_id_and_owner(self, agent_id: str, owner_id: str) -> Optional[Agent]:
        result = await self.db.execute(
            select(self.model)
            .where(self.model.id == agent_id, self.model.owner_id == owner_id)
            .options(
                selectinload(self.model.llm_config),
                selectinload(self.model.knowledge_bases),
                selectinload(self.model.database_connections)
            )
        )
        return result.scalars().first()
    
    async def get_by_share_token(self, share_token: str) -> Optional[Agent]:
        result = await self.db.execute(
            select(self.model)
            .where(self.model.share_token == share_token)
            .options(
                selectinload(self.model.llm_config),
                selectinload(self.model.knowledge_bases),
                selectinload(self.model.database_connections),
                selectinload(self.model.owner)  # Load owner for email access
            )
        )
        return result.scalars().first()

    async def get_kb_file(self, agent_id: str, kb_id: str) -> Optional[KnowledgeBase]:
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.id == kb_id, KnowledgeBase.agent_id == agent_id)
        )
        return result.scalars().first()

    async def delete_kb_files(self, agent_id: str):
        await self.db.execute(
            KnowledgeBase.__table__.delete().where(KnowledgeBase.agent_id == agent_id)
        )
