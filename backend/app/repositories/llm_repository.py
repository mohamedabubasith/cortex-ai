"""LLM Configuration Repository"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import models
from app.core.encryption import encrypt_value, decrypt_value
from typing import Optional, List
import uuid


def _decrypt_config(llm: models.LLMConfiguration) -> models.LLMConfiguration:
    """Decrypt the api_key on a loaded ORM object in-place."""
    if llm and llm.api_key:
        try:
            llm.api_key = decrypt_value(llm.api_key)
        except Exception:
            # Key was stored in plaintext (legacy row) — leave as-is
            pass
    return llm


class LLMRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        tenant_id: str,
        name: str,
        provider: str,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ) -> models.LLMConfiguration:
        """Create LLM config — api_key is encrypted before persisting."""
        llm = models.LLMConfiguration(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            name=name,
            provider=provider,
            api_key=encrypt_value(api_key),
            model=model,
            base_url=base_url
        )
        self.db.add(llm)
        await self.db.commit()
        await self.db.refresh(llm)
        return _decrypt_config(llm)

    async def get_by_id(self, llm_id: str, tenant_id: str) -> Optional[models.LLMConfiguration]:
        """Get LLM by ID — returns object with decrypted api_key."""
        result = await self.db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.id == llm_id,
                models.LLMConfiguration.tenant_id == tenant_id
            )
        )
        llm = result.scalars().first()
        return _decrypt_config(llm) if llm else None

    async def get_all(self, tenant_id: str) -> List[models.LLMConfiguration]:
        """Get all LLM configs for tenant — returns objects with decrypted api_keys."""
        result = await self.db.execute(
            select(models.LLMConfiguration)
            .where(models.LLMConfiguration.tenant_id == tenant_id)
            .order_by(models.LLMConfiguration.created_at.desc())
        )
        configs = result.scalars().all()
        return [_decrypt_config(c) for c in configs]

    async def update(
        self,
        llm_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Optional[models.LLMConfiguration]:
        """Update LLM config — api_key is re-encrypted if a new value is provided."""
        result = await self.db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.id == llm_id,
                models.LLMConfiguration.tenant_id == tenant_id
            )
        )
        llm = result.scalars().first()

        if llm:
            if name is not None:
                llm.name = name
            if api_key is not None:
                llm.api_key = encrypt_value(api_key)
            if model is not None:
                llm.model = model
            if base_url is not None:
                llm.base_url = base_url

            await self.db.commit()
            await self.db.refresh(llm)
            return _decrypt_config(llm)

        return None

    async def delete(self, llm_id: str, tenant_id: str) -> bool:
        """Delete LLM config."""
        result = await self.db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.id == llm_id,
                models.LLMConfiguration.tenant_id == tenant_id
            )
        )
        llm = result.scalars().first()

        if llm:
            await self.db.delete(llm)
            await self.db.commit()
            return True

        return False
