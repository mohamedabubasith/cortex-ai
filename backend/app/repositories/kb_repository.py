"""Knowledge Base Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import models
from typing import Optional, List
import uuid

class KBRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(
        self,
        user_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        status: str = "pending"
    ) -> models.KnowledgeBase:
        """Create KB record"""
        kb = models.KnowledgeBase(
            id=str(uuid.uuid4()),
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            status=status
        )
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        return kb
    
    async def get_by_id(self, kb_id: str, user_id: str) -> Optional[models.KnowledgeBase]:
        """Get KB by ID"""
        result = await self.db.execute(
            select(models.KnowledgeBase).where(
                models.KnowledgeBase.id == kb_id,
                models.KnowledgeBase.user_id == user_id
            )
        )
        return result.scalars().first()
    
    async def get_all(self, user_id: str) -> List[models.KnowledgeBase]:
        """Get all KB files for user"""
        result = await self.db.execute(
            select(models.KnowledgeBase)
            .where(models.KnowledgeBase.user_id == user_id)
            .order_by(models.KnowledgeBase.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_status(self, kb_id: str, status: str):
        """Update KB status"""
        result = await self.db.execute(
            select(models.KnowledgeBase).where(models.KnowledgeBase.id == kb_id)
        )
        kb = result.scalars().first()
        if kb:
            kb.status = status
            await self.db.commit()
            await self.db.refresh(kb)
        return kb
    
    async def delete(self, kb_id: str, user_id: str) -> bool:
        """Delete KB record"""
        result = await self.db.execute(
            select(models.KnowledgeBase).where(
                models.KnowledgeBase.id == kb_id,
                models.KnowledgeBase.user_id == user_id
            )
        )
        kb = result.scalars().first()
        if kb:
            await self.db.delete(kb)
            await self.db.commit()
            return True
        return False
