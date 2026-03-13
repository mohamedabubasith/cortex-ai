from typing import List, Optional
from sqlalchemy import select
from app.models.models import Agent, KnowledgeBase
from app.repositories.base_repository import BaseRepository
from app.core.encryption import decrypt_value

from sqlalchemy.orm import selectinload


def _decrypt_agent_llm(agent: Agent) -> Agent:
    """Decrypt the api_key on an agent's related llm_config in-place."""
    if agent and agent.llm_config and agent.llm_config.api_key:
        try:
            agent.llm_config.api_key = decrypt_value(agent.llm_config.api_key)
        except Exception:
            pass  # Already plaintext (legacy row)
    return agent


class AgentRepository(BaseRepository[Agent]):
    async def get_by_owner(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[Agent]:
        result = await self.db.execute(
            select(self.model)
            .where(self.model.owner_id == owner_id)
            .options(
                selectinload(self.model.llm_config),
                selectinload(self.model.knowledge_bases),
                selectinload(self.model.database_connections),
                selectinload(self.model.mcp_connections),
                selectinload(self.model.owner)
            )
            .offset(skip)
            .limit(limit)
        )
        return [_decrypt_agent_llm(a) for a in result.scalars().all()]

    async def get_by_id_and_owner(self, agent_id: str, owner_id: str) -> Optional[Agent]:
        result = await self.db.execute(
            select(self.model)
            .where(self.model.id == agent_id, self.model.owner_id == owner_id)
            .options(
                selectinload(self.model.llm_config),
                selectinload(self.model.knowledge_bases),
                selectinload(self.model.database_connections),
                selectinload(self.model.mcp_connections),
                selectinload(self.model.owner)
            )
        )
        agent = result.scalars().first()
        return _decrypt_agent_llm(agent) if agent else None

    async def get_by_share_token(self, share_token: str) -> Optional[Agent]:
        result = await self.db.execute(
            select(self.model)
            .where(self.model.share_token == share_token)
            .options(
                selectinload(self.model.llm_config),
                selectinload(self.model.knowledge_bases),
                selectinload(self.model.database_connections),
                selectinload(self.model.mcp_connections),
                selectinload(self.model.owner)
            )
        )
        agent = result.scalars().first()
        return _decrypt_agent_llm(agent) if agent else None

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
