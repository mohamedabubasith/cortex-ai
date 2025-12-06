from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services.auth_service import get_current_active_user
from app.services.database_service import database_service

router = APIRouter()


@router.post("/databases", response_model=schemas.DatabaseConnectionResponse)
async def create_db_connection(
    connection: schemas.DatabaseConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    encrypted_password = database_service.encrypt_password(connection.password)
    
    db_connection = models.DatabaseConnection(
        user_id=current_user.id,
        name=connection.name,
        type=connection.type,
        host=connection.host,
        port=connection.port,
        username=connection.username,
        encrypted_password=encrypted_password,
        database_name=connection.database_name,
        ssl_mode=connection.ssl_mode
    )
    db.add(db_connection)
    await db.commit()
    await db.refresh(db_connection)
    return db_connection

@router.get("/databases", response_model=List[schemas.DatabaseConnectionResponse])
async def get_db_connections(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    result = await db.execute(select(models.DatabaseConnection).where(models.DatabaseConnection.user_id == current_user.id))
    return result.scalars().all()

@router.delete("/databases/{db_id}")
async def delete_db_connection(
    db_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    result = await db.execute(select(models.DatabaseConnection).where(models.DatabaseConnection.id == db_id, models.DatabaseConnection.user_id == current_user.id))
    db_conn = result.scalars().first()
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    await db.delete(db_conn)
    await db.commit()
    return {"status": "success"}
