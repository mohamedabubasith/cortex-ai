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
        chunk_size: int,
        chunk_overlap: int,
        embedding_model: str = "paraphrase-multilingual:latest",
        status: str = "queued",
        tenant_id: str = None,
        parsing_strategy: str = "fast",
    ) -> models.KnowledgeBase:
        """Create KB record"""
        kb = models.KnowledgeBase(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            name=filename,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=embedding_model,
            parsing_strategy=parsing_strategy,
            status=status
        )
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        return kb
    
    async def get_by_id(self, kb_id: str, user_id: str, tenant_id: str, is_admin: bool = False) -> Optional[models.KnowledgeBase]:
        """Get KB by ID (Owner, Member, or Admin) scoped to Tenant"""
        if is_admin:
            # Admin can access any KB in the tenant
            stmt = select(models.KnowledgeBase).where(
                models.KnowledgeBase.id == kb_id,
                models.KnowledgeBase.tenant_id == tenant_id
            )
        else:
            # Regular user must be Owner or Member AND belong to tenant
            stmt = select(models.KnowledgeBase).outerjoin(models.KnowledgeBaseMember).where(
                models.KnowledgeBase.id == kb_id,
                models.KnowledgeBase.tenant_id == tenant_id,
                (models.KnowledgeBase.user_id == user_id) | (models.KnowledgeBaseMember.user_id == user_id)
            ).distinct()
        
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_all(self, user_id: str, tenant_id: str, is_admin: bool = False) -> List[models.KnowledgeBase]:
        """Get all KB files for user (Owned + Shared) in Tenant or All if Admin"""
        if is_admin:
             stmt = select(models.KnowledgeBase).where(
                 models.KnowledgeBase.tenant_id == tenant_id
             ).order_by(models.KnowledgeBase.created_at.desc())
        else:
            stmt = select(models.KnowledgeBase).outerjoin(models.KnowledgeBaseMember).where(
                models.KnowledgeBase.tenant_id == tenant_id,
                (models.KnowledgeBase.user_id == user_id) | (models.KnowledgeBaseMember.user_id == user_id)
            ).order_by(models.KnowledgeBase.created_at.desc()).distinct()
        
        result = await self.db.execute(stmt)
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
        """Delete KB record (Only Owner can delete)"""
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

    async def add_member(self, kb_id: str, user_id: str, role: str = "viewer") -> models.KnowledgeBaseMember:
        """Add member to KB"""
        member = models.KnowledgeBaseMember(
            kb_id=kb_id,
            user_id=user_id,
            role=role
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(self, kb_id: str, user_id: str) -> bool:
        """Remove member from KB"""
        result = await self.db.execute(
            select(models.KnowledgeBaseMember).where(
                models.KnowledgeBaseMember.kb_id == kb_id,
                models.KnowledgeBaseMember.user_id == user_id
            )
        )
        member = result.scalars().first()
        if member:
            await self.db.delete(member)
            await self.db.commit()
            return True
        return False
