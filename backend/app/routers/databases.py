from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services.auth_service import get_current_active_user
from app.services.database_service import database_service

router = APIRouter()

@router.post("/", response_model=schemas.DatabaseConnectionResponse)
async def create_connection(
    agent_id: str,
    connection: schemas.DatabaseConnectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify agent ownership
    result = await db.execute(
        select(models.Agent)
        .where(models.Agent.id == agent_id, models.Agent.owner_id == current_user.id)
    )
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    encrypted_password = database_service.encrypt_password(connection.password)
    
    db_connection = models.DatabaseConnection(
        agent_id=agent_id,
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

@router.get("/", response_model=List[schemas.DatabaseConnectionResponse])
async def get_connections(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify agent ownership
    result = await db.execute(
        select(models.Agent)
        .where(models.Agent.id == agent_id, models.Agent.owner_id == current_user.id)
    )
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await db.execute(
        select(models.DatabaseConnection)
        .where(models.DatabaseConnection.agent_id == agent_id)
    )
    return result.scalars().all()

@router.post("/{connection_id}/test")
async def test_connection(
    agent_id: str,
    connection_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify ownership via agent
    result = await db.execute(
        select(models.DatabaseConnection)
        .join(models.Agent)
        .where(
            models.DatabaseConnection.id == connection_id,
            models.Agent.id == agent_id,
            models.Agent.owner_id == current_user.id
        )
    )
    connection = result.scalars().first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    success = await database_service.test_connection(connection)
    return {"status": "success" if success else "failed"}

@router.post("/{connection_id}/execute")
async def execute_query(
    agent_id: str,
    connection_id: str,
    request: schemas.QueryExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Verify ownership
    result = await db.execute(
        select(models.DatabaseConnection)
        .join(models.Agent)
        .where(
            models.DatabaseConnection.id == connection_id,
            models.Agent.id == agent_id,
            models.Agent.owner_id == current_user.id
        )
    )
    connection = result.scalars().first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Basic safety check (very naive, real app needs better parsing/permissions)
    query_lower = request.query.lower().strip()
    if not query_lower.startswith("select"):
        return {"error": "Only SELECT queries are allowed for safety"}

    results = await database_service.execute_query(connection, request.query)
    return {"results": results}
