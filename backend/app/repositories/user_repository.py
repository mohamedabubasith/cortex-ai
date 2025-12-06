from typing import Optional
from sqlalchemy import select
from app.models.models import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(self.model).where(self.model.email == email))
        return result.scalars().first()
