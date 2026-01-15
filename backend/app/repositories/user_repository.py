from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.models import User, TenantMember
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(self.model).where(self.model.email == email).options(
            selectinload(self.model.tenant_memberships).selectinload(TenantMember.tenant)
        )
        result = await self.db.execute(query)
        return result.scalars().first()
