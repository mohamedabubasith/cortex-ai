from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from app.core.database import Base
from app.models.models import User

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any, user: Optional[User] = None, tenant_id: Optional[str] = None) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        
        # If user is provided, we check for ownership or explicit sharing
        # If only tenant_id is provided (legacy/internal), we filter by tenant
        if user:
            if not user.is_superuser:
                # Check ownership OR explicit share in ResourceAccess OR tenant-wide access if user is admin/owner
                # For now, we'll implement a combined query or rely on the service layer.
                # To maintain repository simplicity, let's allow filtration by owner_id or tenant_id.
                conditions = [self.model.tenant_id == tenant_id] if tenant_id else []
                # If the model has owner_id or user_id
                if hasattr(self.model, 'owner_id'):
                    conditions.append(self.model.owner_id == user.id)
                elif hasattr(self.model, 'user_id'):
                    conditions.append(self.model.user_id == user.id)
                
                # If we have conditions, use OR
                if conditions:
                    query = query.where(or_(*conditions))
        elif tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
            
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100, user: Optional[User] = None, tenant_id: Optional[str] = None) -> List[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        
        if user:
            if not user.is_superuser:
                conditions = [self.model.tenant_id == tenant_id] if tenant_id else []
                if hasattr(self.model, 'owner_id'):
                    conditions.append(self.model.owner_id == user.id)
                elif hasattr(self.model, 'user_id'):
                    conditions.append(self.model.user_id == user.id)
                
                if conditions:
                    query = query.where(or_(*conditions))
        elif tenant_id:
            query = query.where(self.model.tenant_id == tenant_id)
            
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: dict, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> ModelType:
        if tenant_id:
            obj_in["tenant_id"] = tenant_id
        if user_id:
            # Handle both owner_id and user_id naming conventions
            if hasattr(self.model, 'owner_id'):
                obj_in["owner_id"] = user_id
            elif hasattr(self.model, 'user_id'):
                obj_in["user_id"] = user_id
                
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
