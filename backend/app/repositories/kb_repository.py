"""Knowledge Base Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import models
from app.repositories.base_repository import BaseRepository
from typing import Optional, List
import uuid

class KBRepository(BaseRepository[models.KnowledgeBase]):
    def __init__(self, db: AsyncSession):
        super().__init__(models.KnowledgeBase, db)
    
    async def create_kb(
        self,
        user_id: str,
        tenant_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        status: str = "pending"
    ) -> models.KnowledgeBase:
        """Create KB record support both legacy and new multi-tenant flows"""
        return await self.create(
            {
                "name": filename,
                "filename": filename,
                "file_path": file_path,
                "file_type": file_type,
                "status": status
            },
            user_id=user_id,
            tenant_id=tenant_id
        )
    
    async def get_by_id(self, kb_id: str, user_id: str) -> Optional[models.KnowledgeBase]:
        """Get KB by ID with user filtering"""
        result = await self.db.execute(
            select(models.KnowledgeBase).where(
                models.KnowledgeBase.id == kb_id,
                models.KnowledgeBase.user_id == user_id
            )
        )
        return result.scalars().first()
    
    async def get_all_for_user(self, user_id: str) -> List[models.KnowledgeBase]:
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
    
    async def get_all(self, user: models.User, tenant_id: str) -> List[models.KnowledgeBase]:
        """Get all KB files for tenant (and visible to user)"""
        # Strict tenant filtering
        query = select(models.KnowledgeBase).where(
            models.KnowledgeBase.tenant_id == tenant_id
        ).order_by(models.KnowledgeBase.created_at.desc())
        
        # If we wanted to enforce strict ownership or RLS beyond tenant, we'd add it here.
        # For now, all tenant members can view all tenant KBs (simplified).
        # OR we could filter by user_id if we want private-only default.
        # query = query.where(models.KnowledgeBase.user_id == user.id)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def delete_kb(self, kb_id: str, user_id: str) -> bool:
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
