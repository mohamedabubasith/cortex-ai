from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import text, select
from app.core.database import get_db, set_rls_context
from app.services.auth_service import get_current_user
from app.schemas.shares import ResourceShareCreate, ResourceShareResponse
from app.models.models import ResourceShare, User
from app.models.models import Agent, KnowledgeBase, DatabaseConnection, LLMConfiguration


router = APIRouter(tags=["sharing"])

async def verify_resource_ownership(db: AsyncSession, resource_type: str, resource_id: str, user: User) -> bool:
    """
    Verifies if the user is the owner of the resource OR has tenant admin privileges.
    Returns True if authorized, False otherwise.
    """
    # 0. Tenant Admin override
    if getattr(user, "is_tenant_admin", False): # Explicit check if property exists
         return True

    # Check "admin" share
    query = select(ResourceShare).where(
        ResourceShare.resource_id == resource_id,
        ResourceShare.grantee_id == user.id,
        ResourceShare.permission == 'admin'
    )
    result = await db.execute(query)
    admin_share = result.scalars().first()
    
    if admin_share:
        return True

    # Verify RLS Context
    # rls_check = await db.execute(text("SELECT current_setting('app.current_user_id', true)"))
    # val = rls_check.scalar()
    # print(f"DEBUG API: RLS User Check (in verify): {val}")
    
    # Check Ownership Table-by-Table
    target_table = None
    owner_field = "user_id" # Default
    
    if resource_type == "agent":
        target_table = Agent
        owner_field = "owner_id"
    elif resource_type == "kb":
        target_table = KnowledgeBase
    elif resource_type == "db_connection":
        target_table = DatabaseConnection
    elif resource_type == "llm_config":
        target_table = LLMConfiguration
    else:
        raise HTTPException(status_code=400, detail="Invalid resource type")
        
    query = select(target_table).where(getattr(target_table, "id") == resource_id)
    result = await db.execute(query)
    resource = result.scalars().first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    real_owner = getattr(resource, owner_field) if resource else None
    if str(real_owner) == str(user.id):
        return True
        
    return False

@router.post("", response_model=ResourceShareResponse)
async def create_share(
    share_data: ResourceShareCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Share a resource with a user or group.
    Requires: Ownership of the resource OR 'admin' permission on the resource.
    """
    async with db.begin():
        # Set RLS Context (Inside transaction to ensure persistence)
        await set_rls_context(db, current_user)
        
        # 1. Verify Permission
        is_authorized = await verify_resource_ownership(db, share_data.resource_type, share_data.resource_id, current_user)
        if not is_authorized:
             raise HTTPException(status_code=403, detail="Not authorized to share this resource")
    
        # 2. Check if share already exists (Update if so? Or Error? Spec said Upsert)
        query = select(ResourceShare).where(
            ResourceShare.resource_id == share_data.resource_id,
            ResourceShare.grantee_id == share_data.grantee_id
        )
        result = await db.execute(query)
        existing_share = result.scalars().first()
        
        if existing_share:
            existing_share.permission = share_data.permission
            existing_share.shared_by = current_user.id
            # await db.commit() # Handled by block
            await db.flush()
            await db.refresh(existing_share)
            return existing_share
    
        # 3. Create New
        new_share = ResourceShare(
            tenant_id=current_user.tenant_id,
            resource_id=share_data.resource_id,
            resource_type=share_data.resource_type,
            grantee_id=share_data.grantee_id,
            grantee_type=share_data.grantee_type,
            permission=share_data.permission,
            shared_by=current_user.id
        )
        db.add(new_share)
        # await db.commit()
        await db.flush()
        await db.refresh(new_share)
        return new_share

@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    share_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Revoke (delete) a share.
    Requires: Ownership of the resource OR 'admin' permission.
    """
    async with db.begin():
        await set_rls_context(db, current_user)
    
        query = select(ResourceShare).where(ResourceShare.id == share_id)
        result = await db.execute(query)
        share = result.scalars().first()
        
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")
            
        # Verify Permission on the RESOURCE this share points to
        is_authorized = await verify_resource_ownership(db, share.resource_type, share.resource_id, current_user)
        
        if not is_authorized and str(share.shared_by) == str(current_user.id):
            is_authorized = True
            
        if not is_authorized:
            raise HTTPException(status_code=403, detail="Not authorized to revoke this share")
            
        await db.delete(share)
        # await db.commit()
    return None

@router.get("/resource/{resource_id}", response_model=List[ResourceShareResponse])
async def list_shares(
    resource_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all shares for a specific resource.
    Requires: Ownership/Admin access.
    """
    async with db.begin():
        await set_rls_context(db, current_user)
        
        query = select(ResourceShare).where(ResourceShare.resource_id == resource_id)
        result = await db.execute(query)
        shares = result.scalars().all()
        return shares
