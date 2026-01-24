from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import os
import uuid

from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.repositories.kb_repository import KBRepository
from app.services.kb_service import KBService
from app.services.auth_service import get_current_active_user

router = APIRouter()

def get_kb_service(db: AsyncSession = Depends(get_db)) -> KBService:
    """Dependency injection for KB service"""
    return KBService(KBRepository(db))

@router.post("/upload", response_model=schemas.KnowledgeBase)
async def upload_kb_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    llm_config_id: Optional[str] = Form(None),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    kb_service: KBService = Depends(get_kb_service)
):
    """Upload knowledge base file"""
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md', '.doc', '.json', '.xlsx', '.xls', '.csv', '.pptx', '.ppt']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Supported formats: {', '.join(allowed_extensions)}"
        )
    
    file_path = None
    try:
        user_upload_dir = os.path.abspath(f"uploads/{current_user.id}")
        os.makedirs(user_upload_dir, exist_ok=True)
        
        file_path = os.path.join(user_upload_dir, f"{uuid.uuid4()}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_size = os.path.getsize(file_path)
        
        # 100MB limit
        if file_size > 100 * 1024 * 1024:
             os.remove(file_path)
             raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB.")
        
        llm_config = None
        if llm_config_id:
            result = await db.execute(
                select(models.LLMConfiguration).where(
                    models.LLMConfiguration.id == llm_config_id,
                    models.LLMConfiguration.user_id == current_user.id
                )
            )
            llm_config = result.scalars().first()
        else:
            # Fallback: Use the first available LLM config
            result = await db.execute(
                select(models.LLMConfiguration).where(
                    models.LLMConfiguration.user_id == current_user.id
                )
            )
            llm_config = result.scalars().first()
        
        if not llm_config:
            # We allow upload but warn
            print("WARNING: No LLM Config found! Indexing will be skipped for now.")
        
        # Create KB record immediately
        kb = await kb_service.create_kb_record(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            file_type=file_ext,
            file_size=file_size,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Get tenant ID (simplified: fetch user's first tenant or None)
        # For now we can pass None or handle it inside service
        tenant_id = None 
        
        # Process in background
        if llm_config:
            background_tasks.add_task(
                kb_service.process_kb,
                kb.id,
                file_path,
                current_user.id,
                tenant_id,
                chunk_size,
                chunk_overlap,
                llm_config,
                current_user.email
            )
        
        return kb
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if it was created during this request
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        logger_error = str(e).lower()
        if "no space left" in logger_error:
             raise HTTPException(status_code=507, detail="Server storage is full.")
        
        print(f"ERROR in upload_kb_file: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/{kb_id}/status")
async def get_kb_status(
    kb_id: str,
    current_user: models.User = Depends(get_current_active_user),
    kb_service: KBService = Depends(get_kb_service)
):
    """Get Cognee processing status"""
    status = await kb_service.get_status(kb_id, current_user.id, user_email = current_user.email)
    
    if not status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return status

@router.get("", response_model=List[schemas.KnowledgeBase])
async def get_kb_files(
    current_user: models.User = Depends(get_current_active_user),
    kb_service: KBService = Depends(get_kb_service)
):
    """Get all KB files"""
    return await kb_service.get_all(current_user.id, user_email = current_user.email)

@router.post("/{kb_id}/query")
async def query_kb(
    kb_id: str,
    query_request: schemas.KBQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    kb_service: KBService = Depends(get_kb_service)
):
    """Query KB"""
    result = await db.execute(
        select(models.LLMConfiguration).where(
            models.LLMConfiguration.id == query_request.llm_config_id,
            models.LLMConfiguration.user_id == current_user.id
        )
    )
    llm_config = result.scalars().first()
    
    if not llm_config:
        raise HTTPException(status_code=404, detail="LLM configuration not found. Please check your settings.")
    
    result = await kb_service.query(kb_id, current_user.id, query_request.query, llm_config, user_email = current_user.email)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.delete("/{kb_id}")
async def delete_kb(
    kb_id: str,
    current_user: models.User = Depends(get_current_active_user),
    kb_service: KBService = Depends(get_kb_service)
):
    """Delete KB"""
    result = await kb_service.delete(kb_id, current_user.id, user_email = current_user.email)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result
