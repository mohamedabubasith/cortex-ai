from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any, tenant_id: Optional[str] = None) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100, tenant_id: Optional[str] = None) -> List[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        if tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: dict, tenant_id: Optional[str] = None) -> ModelType:
        if tenant_id:
            obj_in["tenant_id"] = tenant_id
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: ModelType) -> ModelType:
        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj
