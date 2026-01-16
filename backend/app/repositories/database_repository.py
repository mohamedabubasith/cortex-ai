from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import DatabaseConnection
from app.repositories.base_repository import BaseRepository

class DatabaseRepository(BaseRepository[DatabaseConnection]):
    def __init__(self, db: AsyncSession):
        super().__init__(DatabaseConnection, db)
