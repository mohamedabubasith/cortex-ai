from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import MCPConnection
from app.repositories.base_repository import BaseRepository

class MCPRepository(BaseRepository[MCPConnection]):
    def __init__(self, db: AsyncSession):
        super().__init__(MCPConnection, db)
