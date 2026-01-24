"""LLM Configuration Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import models
from typing import Optional, List
import uuid

class LLMRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: str,
        name: str,
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> models.LLMConfiguration:
        """Create LLM config"""
        llm = models.LLMConfiguration(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url
        )
        self.db.add(llm)
        await self.db.commit()
        await self.db.refresh(llm)
        return llm
    
    async def get_by_id(self, llm_id: str, user_id: str) -> Optional[models.LLMConfiguration]:
        """Get LLM by ID"""
        result = await self.db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.id == llm_id,
                models.LLMConfiguration.user_id == user_id
            )
        )
        return result.scalars().first()
    
    async def get_all(self, user_id: str) -> List[models.LLMConfiguration]:
        """Get all LLM configs for user"""
        result = await self.db.execute(
            select(models.LLMConfiguration)
            .where(models.LLMConfiguration.user_id == user_id)
            .order_by(models.LLMConfiguration.created_at.desc())
        )
        return result.scalars().all()
    
    async def update(
        self,
        llm_id: str,
        user_id: str,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Optional[models.LLMConfiguration]:
        """Update LLM config"""
        result = await self.db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.id == llm_id,
                models.LLMConfiguration.user_id == user_id
            )
        )
        llm = result.scalars().first()
        
        if llm:
            if name is not None:
                llm.name = name
            if api_key is not None:
                llm.api_key = api_key
            if model is not None:
                llm.model = model
            if base_url is not None:
                llm.base_url = base_url
            
            await self.db.commit()
            await self.db.refresh(llm)
        
        return llm
    
    async def delete(self, llm_id: str, user_id: str) -> bool:
        """Delete LLM config"""
        result = await self.db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.id == llm_id,
                models.LLMConfiguration.user_id == user_id
            )
        )
        llm = result.scalars().first()
        
        if llm:
            await self.db.delete(llm)
            await self.db.commit()
            return True
        
        return False
