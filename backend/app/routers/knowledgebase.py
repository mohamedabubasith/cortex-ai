from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging
import os
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models import models
from app.schemas import schemas
from app.repositories.kb_repository import KBRepository
from app.services.kb_service import KBService, run_kb_ingestion_background
from app.services.kb_chunk_limits import clamp_chunk_size_overlap
from app.services.auth_service import get_current_active_user, get_current_tenant

router = APIRouter()
logger = logging.getLogger(__name__)

def get_kb_service(db: AsyncSession = Depends(get_db)) -> KBService:
    """Dependency injection for KB service"""
    return KBService(KBRepository(db))


@router.get("/ingest-settings", response_model=schemas.KBIngestSettings)
async def kb_ingest_settings(_user: models.User = Depends(get_current_active_user)):
    """Chunk size bounds for the UI (characters), derived from embedding model token budget."""
    mx = settings.kb_max_chunk_chars
    mn = settings.KB_MIN_CHUNK_CHARS
    dcs = min(1024, mx)
    dco = min(200, max(0, dcs - 1))
    return schemas.KBIngestSettings(
        min_chunk_size=mn,
        max_chunk_size=mx,
        max_chunk_overlap=max(0, mx - 1),
        default_chunk_size=dcs,
        default_chunk_overlap=dco,
        embedding_model=settings.OLLAMA_MODEL,
        embedding_max_input_tokens=settings.KB_EMBEDDING_MAX_INPUT_TOKENS,
        chars_per_token_estimate=settings.KB_CHUNK_CHARS_PER_TOKEN,
        rag_embedding_batch_size=settings.RAG_EMBEDDING_BATCH_SIZE,
    )


@router.post("/upload", response_model=schemas.KnowledgeBase)
async def upload_kb_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    llm_config_id: Optional[str] = Form(None),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    embedding_model: Optional[str] = Form(None),
    parsing_strategy: str = Form("fast"),
    enable_graph: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    kb_service: KBService = Depends(get_kb_service)
):
    """Upload knowledge base file for Haystack ingestion (Unstructured + Ollama + Qdrant)."""
    allowed_extensions = [".pdf", ".docx", ".pptx", ".txt", ".md"]
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
                    models.LLMConfiguration.tenant_id == current_tenant.id
                )
            )
            llm_config = result.scalars().first()
        else:
            # Fallback: Use the first available LLM config in tenant
            result = await db.execute(
                select(models.LLMConfiguration).where(
                    models.LLMConfiguration.tenant_id == current_tenant.id
                )
            )
            llm_config = result.scalars().first()
        
        if not llm_config and enable_graph:
            # If graph is requested but no LLM, we should technically warn, 
            # but since frontend handles the disable logic, we just proceed (graph will fail/skip in service).
            # Actually, let's auto-disable graph if no LLM to avoid errors.
            enable_graph = False
            print("INFO: Graph enabled but no LLM config found. Disabling graph integration.")
            
        if not llm_config:
            print("INFO: No LLM Config found. Ingestion will use Ollama embeddings from server configuration.")

        strat = (parsing_strategy or "fast").lower()
        if strat not in ("fast", "hi_res"):
            raise HTTPException(status_code=400, detail="parsing_strategy must be 'fast' or 'hi_res'")

        emb_model = (embedding_model or "").strip() or settings.OLLAMA_MODEL

        raw_cs, raw_co = chunk_size, chunk_overlap
        chunk_size, chunk_overlap = clamp_chunk_size_overlap(chunk_size, chunk_overlap)
        if (chunk_size, chunk_overlap) != (raw_cs, raw_co):
            logger.info(
                "[kb-ingest] upload clamped chunk_size/overlap from %s/%s to %s/%s (max_chunk_chars=%s)",
                raw_cs,
                raw_co,
                chunk_size,
                chunk_overlap,
                settings.kb_max_chunk_chars,
            )

        kb = await kb_service.create_kb_record(
            user_id=current_user.id,
            filename=file.filename,
            file_path=file_path,
            file_type=file_ext,
            file_size=file_size,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            embedding_model=emb_model,
            tenant_id=current_tenant.id,
            enable_graph=enable_graph,
            parsing_strategy=strat,
        )
        
        # Process in background (always). Use a dedicated coroutine with a fresh DB session —
        # the request-scoped session is closed after the response while this task still runs.
        llm_id = llm_config.id if llm_config else None
        background_tasks.add_task(
            run_kb_ingestion_background,
            kb.id,
            file_path,
            current_user.id,
            current_tenant.id,
            chunk_size,
            chunk_overlap,
            emb_model,
            current_user.email,
            enable_graph,
            llm_id,
        )
        logger.info(
            "[kb-ingest] upload accepted; background ingestion scheduled kb_id=%s path=%s size=%s "
            "chunk=%s/%s model=%s strategy=%s (watch server logs for [kb-ingest])",
            kb.id,
            file_path,
            file_size,
            chunk_size,
            chunk_overlap,
            emb_model,
            strat,
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
    current_tenant: models.Tenant = Depends(get_current_tenant),
    kb_service: KBService = Depends(get_kb_service)
):
    """Get ingestion pipeline status for a knowledge base document."""
    status = await kb_service.get_status(kb_id, current_user.id, current_tenant.id, user_email = current_user.email)
    
    if not status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return status

from fastapi import Request

@router.get("", response_model=List[schemas.KnowledgeBase])
async def get_kb_files(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    kb_service: KBService = Depends(get_kb_service),
    db: AsyncSession = Depends(get_db)
):
    """Get all KB files"""
    # Check if user is admin in this tenant
    is_admin = False
    
    # 1. Check Permissions (Preferred)
    if hasattr(request.state, "permissions"):
         if "admin" in request.state.permissions or "kb.read_all" in request.state.permissions:
             is_admin = True
             
    # 2. Check Membership Role directly (Fallback/Legacy)
    # We can check the role name from the membership that authorized current_tenant
    # But since we have RLS, simpler is asking: "Does this user have admin rights?"
    # If get_current_tenant ran, it set request.state.permissions
    
    # Also check if user is a "tenant admin" or "owner" via membership string logic if perms fail
    # iterating user.tenant_memberships? No, that's lazy loading.
    # Let's trust permission or just check "owner" role.
    
    if not is_admin:
        # Fallback manual check on membership if permissions logic isn't perfect yet
         stmt = select(models.TenantMember).where(
            models.TenantMember.user_id == current_user.id,
            models.TenantMember.tenant_id == current_tenant.id
         )
         result = await db.execute(stmt)
         member = result.scalars().first()
         if member and member.role in ["owner", "admin"]:
             is_admin = True

    return await kb_service.get_all(current_user.id, current_tenant.id, user_email = current_user.email, is_admin=is_admin)

@router.delete("/{kb_id}")
async def delete_kb(
    kb_id: str,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    kb_service: KBService = Depends(get_kb_service)
):
    """Delete knowledge base document"""
    result = await kb_service.delete(kb_id, current_user.id, current_tenant.id, user_email=current_user.email)
    
    if not result["success"]:
        if "not found" in result["message"].lower():
             raise HTTPException(status_code=404, detail="Document not found")
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@router.post("/{kb_id}/query")
async def query_kb(
    kb_id: str,
    query_request: schemas.KBQueryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    kb_service: KBService = Depends(get_kb_service)
):
    """Query KB"""
    # Check Admin Status
    is_admin = False
    if hasattr(request.state, "permissions"):
         if "admin" in request.state.permissions or "kb.read_all" in request.state.permissions:
             is_admin = True
    
    if not is_admin:
         stmt = select(models.TenantMember).where(
            models.TenantMember.user_id == current_user.id,
            models.TenantMember.tenant_id == current_tenant.id
         )
         result = await db.execute(stmt)
         member = result.scalars().first()
         if member and member.role in ["owner", "admin"]:
             is_admin = True

    llm_config = None
    if query_request.llm_config_id:
        result = await db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.id == query_request.llm_config_id,
                models.LLMConfiguration.tenant_id == current_tenant.id
            )
        )
        llm_config = result.scalars().first()
        if not llm_config:
             raise HTTPException(status_code=404, detail="Selected LLM configuration not found.")
    else:
        # Try to find a default/any config for the tenant
        result = await db.execute(
            select(models.LLMConfiguration).where(
                models.LLMConfiguration.tenant_id == current_tenant.id
            )
        )
        llm_config = result.scalars().first()

    # Note: We don't raise 404 if llm_config is None anymore, because local embeddings don't need it.
    
    result = await kb_service.query(kb_id, current_user.id, current_tenant.id, query_request.query, llm_config, user_email = current_user.email, is_admin=is_admin)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return result

@router.post("/{kb_id}/share")
async def share_kb(
    kb_id: str,
    share_request: schemas.KBShareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    kb_service: KBService = Depends(get_kb_service)
):
    """Share KB with another user by email"""
    # 1. Lookup User by Email
    result = await db.execute(select(models.User).where(models.User.email == share_request.email))
    target_user = result.scalars().first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User with this email not found")
        
    # Security: Verify they are in the same tenant (fetch memberships)
    # OR: Implicitly if we found the user, but we should enforce tenant isolation if strictly multi-tenant app.
    # However, users can belong to multiple tenants.
    # We should ensure they share AT LEAST ONE tenant.
    
    # Fetch memberships for both
    # For MVP sharing: Check if target user is in current_user's active tenant scope? 
    # Or just allow sharing? The prompt said "share with user B who in the same tenant".
    
    # We explicitly verify they share a tenant.
    u_stmt = select(models.TenantMember.tenant_id).where(models.TenantMember.user_id == current_user.id)
    t_stmt = select(models.TenantMember.tenant_id).where(models.TenantMember.user_id == target_user.id)
    
    u_tenants = (await db.execute(u_stmt)).scalars().all()
    t_tenants = (await db.execute(t_stmt)).scalars().all()
    
    common_tenants = set(u_tenants).intersection(set(t_tenants))
    if not common_tenants:
         raise HTTPException(status_code=403, detail="User is not in your organization/tenant")

    # 2. Share via Service
    result = await kb_service.share_kb(kb_id, current_user.id, target_user.id, current_tenant.id, role=share_request.role)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
        
    return result

@router.delete("/{kb_id}/share/{user_id}")
async def unshare_kb(
    kb_id: str,
    user_id: str,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    kb_service: KBService = Depends(get_kb_service)
):
    """Unshare KB"""
    result = await kb_service.unshare_kb(kb_id, current_user.id, user_id, current_tenant.id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
        
    return result
