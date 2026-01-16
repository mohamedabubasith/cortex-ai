from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import User, TenantMember
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(self.model).where(self.model.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()
