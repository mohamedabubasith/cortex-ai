from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services.auth_service import get_current_active_user
from app.services.database_service import database_service
import shutil
import os

router = APIRouter()

# --- LLM Configurations ---

@router.post("/llm", response_model=schemas.LLMConfiguration)
async def create_llm_config(
    config: schemas.LLMConfigurationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_config = models.LLMConfiguration(**config.dict(), user_id=current_user.id)
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config

@router.get("/llm", response_model=List[schemas.LLMConfiguration])
async def get_llm_configs(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    result = await db.execute(select(models.LLMConfiguration).where(models.LLMConfiguration.user_id == current_user.id))
    return result.scalars().all()

@router.delete("/llm/{config_id}")
async def delete_llm_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    result = await db.execute(select(models.LLMConfiguration).where(models.LLMConfiguration.id == config_id, models.LLMConfiguration.user_id == current_user.id))
    config = result.scalars().first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    await db.delete(config)
    await db.commit()
    return {"status": "success"}

@router.put("/llm/{config_id}", response_model=schemas.LLMConfiguration)
async def update_llm_config(
    config_id: str,
    config_update: schemas.LLMConfigurationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    result = await db.execute(select(models.LLMConfiguration).where(models.LLMConfiguration.id == config_id, models.LLMConfiguration.user_id == current_user.id))
    db_config = result.scalars().first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    update_data = config_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
        
    await db.commit()
    await db.refresh(db_config)
    return db_config

@router.post("/llm/test")
async def test_llm_connection(
    request: schemas.LLMConnectionTestRequest,
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Test the LLM connection by making a simple request.
    """
    try:
        from openai import AsyncOpenAI
        
        # Configure client
        client_kwargs = {"api_key": request.api_key}
        if request.base_url:
            client_kwargs["base_url"] = request.base_url
            
        client = AsyncOpenAI(**client_kwargs)
        
        # Simple test call
        await client.models.list()
        
        return {"status": "success", "message": "Connection successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")

# --- Knowledge Bases (Production-Grade) ---

@router.post("/kb/upload", response_model=schemas.KnowledgeBase)
async def upload_kb_file(
    file: UploadFile = File(...),
    llm_config_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Upload and index a knowledge base file.
    Supports PDF, DOCX, TXT, MD, etc.
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.docx', '.txt', '.md', '.doc'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Ensure upload directory exists
        upload_dir = f"uploads/{current_user.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = f"{upload_dir}/{file.filename}"
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Create KB record with pending status
        kb_file = models.KnowledgeBase(
            user_id=current_user.id,
            name=file.filename,
            filename=file.filename,
            file_path=file_path,
            file_type=file.content_type or 'application/octet-stream',
            status="pending"
        )
        db.add(kb_file)
        await db.commit()
        await db.refresh(kb_file)
        
        # Trigger indexing in background if LLM config is provided
        if llm_config_id:
            from app.services.cognee_service import cognee_service
            
            # Get LLM config
            llm_result = await db.execute(
                select(models.LLMConfiguration).where(
                    models.LLMConfiguration.id == llm_config_id,
                    models.LLMConfiguration.user_id == current_user.id
                )
            )
            llm_config = llm_result.scalars().first()
            
            if llm_config:
                # Start indexing (async)
                dataset_name = f"doc_{kb_file.id}"
                
                # Update status to processing
                kb_file.status = "processing"
                await db.commit()
                
                # Index in background
                result = await cognee_service.upload_and_index(
                    llm_config, 
                    file_path, 
                    file.filename, 
                    dataset_name
                )
                
                # Update status based on result
                kb_file.status = result["status"]
                await db.commit()
                await db.refresh(kb_file)
        
        return kb_file
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if something went wrong
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/kb", response_model=List[schemas.KnowledgeBase])
async def get_kb_files(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get all knowledge base files for current user."""
    result = await db.execute(
        select(models.KnowledgeBase).where(
            models.KnowledgeBase.user_id == current_user.id
        ).order_by(models.KnowledgeBase.created_at.desc())
    )
    return result.scalars().all()

@router.get("/kb/{kb_id}/status")
async def get_kb_status(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get the processing status of a knowledge base file."""
    result = await db.execute(
        select(models.KnowledgeBase).where(
            models.KnowledgeBase.id == kb_id,
            models.KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge Base not found")
    
    # Also check Cognee service status
    from app.services.cognee_service import cognee_service
    dataset_name = f"doc_{kb.id}"
    cognee_status = await cognee_service.get_processing_status(dataset_name)
    
    return {
        "id": kb.id,
        "filename": kb.filename,
        "status": kb.status,
        "cognee_status": cognee_status,
        "created_at": kb.created_at.isoformat() if kb.created_at else None
    }

@router.post("/kb/{kb_id}/query")
async def query_kb_document(
    kb_id: str,
    query_request: schemas.KBQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Query a specific knowledge base document.
    Returns relevant context from the document based on the query.
    """
    # Get KB
    result = await db.execute(
        select(models.KnowledgeBase).where(
            models.KnowledgeBase.id == kb_id,
            models.KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge Base not found")
    
    # Check if indexed
    if kb.status != "indexed":
        raise HTTPException(
            status_code=400, 
            detail=f"Document not ready for querying. Current status: {kb.status}"
        )

    # Get LLM Config
    llm_result = await db.execute(
        select(models.LLMConfiguration).where(
            models.LLMConfiguration.id == query_request.llm_config_id,
            models.LLMConfiguration.user_id == current_user.id
        )
    )
    llm_config = llm_result.scalars().first()
    if not llm_config:
        raise HTTPException(status_code=404, detail="LLM Configuration not found")

    # Query Cognee
    from app.services.cognee_service import cognee_service
    dataset_name = f"doc_{kb.id}"
    
    result = await cognee_service.query(llm_config, query_request.query, dataset_name)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("message", "Query failed"))
    
    return {
        "answer": result.get("context") or "No relevant context found.",
        "results_count": result.get("count", 0)
    }

@router.delete("/kb/{kb_id}")
async def delete_kb_file(
    kb_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a knowledge base file and its indexed data from Cognee.
    """
    result = await db.execute(
        select(models.KnowledgeBase).where(
            models.KnowledgeBase.id == kb_id,
            models.KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalars().first()
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge Base not found")
    
    # Delete from Cognee if indexed
    if kb.status == "indexed":
        from app.services.cognee_service import cognee_service
        
        # Get user's LLM config (first one available)
        llm_result = await db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.user_id == current_user.id
            ).limit(1)
        )
        llm_config = llm_result.scalars().first()
        
        dataset_name = f"doc_{kb.id}"
        delete_result = await cognee_service.delete_dataset(llm_config, dataset_name)
        
        if not delete_result["success"]:
            # Log warning but continue with file deletion
            print(f"Warning: Failed to delete from Cognee: {delete_result.get('message')}")
    
    # Delete file from disk
    try:
        if os.path.exists(kb.file_path):
            os.remove(kb.file_path)
    except Exception as e:
        print(f"Warning: Failed to delete file from disk: {e}")
    
    # Delete from database
    await db.delete(kb)
    await db.commit()
    
    return {"status": "success", "message": f"Successfully deleted {kb.filename}"}

# --- Database Connections (Global) ---

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
