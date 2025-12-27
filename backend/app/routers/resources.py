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

@router.post("/databases/test")
async def test_db_connection(
    connection: schemas.DatabaseConnectionCreate,
    current_user: models.User = Depends(get_current_active_user)
):
    """Test database connection without saving it"""
    # Create a temporary connection object for testing
    temp_connection = models.DatabaseConnection(
        name=connection.name,
        type=connection.type,
        host=connection.host,
        port=connection.port,
        username=connection.username,
        encrypted_password=database_service.encrypt_password(connection.password),
        database_name=connection.database_name,
        ssl_mode=connection.ssl_mode
    )
    
    try:
        success = await database_service.test_connection(temp_connection)
        if success:
            return {"status": "success", "message": "Connection successful!"}
        else:
            return {"status": "failed", "message": "Connection failed. Please check your credentials."}
    except Exception as e:
        error_message = str(e)
        # Provide more user-friendly error messages for common issues
        if "password authentication failed" in error_message.lower():
            return {"status": "failed", "message": "Authentication failed. Please check your username and password."}
        elif "does not exist" in error_message.lower():
            return {"status": "failed", "message": "Database does not exist. Please check the database name."}
        elif "connection refused" in error_message.lower() or "could not connect" in error_message.lower():
            return {"status": "failed", "message": "Could not connect to database server. Please check host and port."}
        else:
            return {"status": "failed", "message": error_message if error_message else "Connection failed. Please check your credentials."}

@router.post("/databases/{db_id}/test")
async def test_existing_db_connection(
    db_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Test an existing saved database connection by ID"""
    result = await db.execute(
        select(models.DatabaseConnection).where(
            models.DatabaseConnection.id == db_id,
            models.DatabaseConnection.user_id == current_user.id
        )
    )
    db_conn = result.scalars().first()
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    try:
        success = await database_service.test_connection(db_conn)
        if success:
            return {"status": "success", "message": "Connection successful!"}
        else:
            return {"status": "failed", "message": "Connection failed. Please check your credentials."}
    except Exception as e:
        # Handle decryption errors (e.g., when encryption key has changed)
        error_message = str(e)
        if "InvalidToken" in error_message or "Signature did not match" in error_message:
            return {
                "status": "failed", 
                "message": "Unable to decrypt password. The encryption key may have changed. Please delete and recreate this connection."
            }
        # Provide more user-friendly error messages for common database issues
        elif "password authentication failed" in error_message.lower():
            return {"status": "failed", "message": "Authentication failed. Please check your username and password."}
        elif "does not exist" in error_message.lower():
            return {"status": "failed", "message": "Database does not exist. Please check the database name."}
        elif "connection refused" in error_message.lower() or "could not connect" in error_message.lower():
            return {"status": "failed", "message": "Could not connect to database server. Please check host and port."}
        else:
            return {"status": "failed", "message": error_message if error_message else "Connection test failed. Please check your credentials."}

@router.put("/databases/{db_id}", response_model=schemas.DatabaseConnectionResponse)
async def update_db_connection(
    db_id: str,
    connection_update: schemas.DatabaseConnectionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update an existing database connection"""
    result = await db.execute(
        select(models.DatabaseConnection).where(
            models.DatabaseConnection.id == db_id,
            models.DatabaseConnection.user_id == current_user.id
        )
    )
    db_conn = result.scalars().first()
    if not db_conn:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    # Update fields if provided
    if connection_update.name is not None:
        db_conn.name = connection_update.name
    if connection_update.type is not None:
        db_conn.type = connection_update.type
    if connection_update.host is not None:
        db_conn.host = connection_update.host
    if connection_update.port is not None:
        db_conn.port = connection_update.port
    if connection_update.username is not None:
        db_conn.username = connection_update.username
    if connection_update.database_name is not None:
        db_conn.database_name = connection_update.database_name
    if connection_update.ssl_mode is not None:
        db_conn.ssl_mode = connection_update.ssl_mode
    if connection_update.password is not None:
        db_conn.encrypted_password = database_service.encrypt_password(connection_update.password)
    
    await db.commit()
    await db.refresh(db_conn)
    return db_conn

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
