from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import LLMConfiguration
from app.repositories.base_repository import BaseRepository

class LLMRepository(BaseRepository[LLMConfiguration]):
    """
    LLM Configuration Repository.
    Inherits from BaseRepository to provide unified RBAC/Multi-tenancy filtering.
    Maintains backward compatibility with LLMConfigService.
    """
    def __init__(self, db: AsyncSession):
        super().__init__(LLMConfiguration, db)

    async def create(
        self,
        user_id: str,
        name: str,
        api_key: str,
        model: str,
        provider: str = None,
        base_url: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> LLMConfiguration:
        """Create LLM config with original signature support"""
        obj_in = {
            "name": name,
            "api_key": api_key,
            "model": model,
            "provider": provider,
            "base_url": base_url
        }
        return await super().create(obj_in, user_id=user_id, tenant_id=tenant_id)

    async def get_by_id(self, llm_id: str, user_id: str) -> Optional[LLMConfiguration]:
        """Backward compatible get_by_id using manual filtering for safety"""
        from sqlalchemy import select
        result = await self.db.execute(
            select(self.model).where(
                self.model.id == llm_id,
                self.model.user_id == user_id
            )
        )
        return result.scalars().first()

    async def get_all(self, user_id: str) -> List[LLMConfiguration]:
        """Backward compatible get_all for specified user"""
        from sqlalchemy import select
        result = await self.db.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return result.scalars().all()

    async def update(
        self,
        llm_id: str,
        user_id: str,
        **kwargs
    ) -> Optional[LLMConfiguration]:
        """Backward compatible update wrapper"""
        llm = await self.get_by_id(llm_id, user_id)
        if not llm:
            return None
        
        # BaseRepository.update expects a dict
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        return await super().update(llm, update_data)

    async def delete(self, llm_id: str, user_id: str) -> bool:
        """Backward compatible delete wrapper"""
        llm = await self.get_by_id(llm_id, user_id)
        if not llm:
            return False
        await super().delete(llm)
        return True
