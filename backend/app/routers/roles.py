
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.models import models
from app.schemas import roles as role_schemas
from app.services.auth_service import get_current_active_user, get_current_tenant
from app.services.permission_service import PermissionService

router = APIRouter()

async def check_permission(request: Request, required_perm: str):
    # Bypass logic if superuser, handled in logic/service usually?
    # Simple check against hydrated state
    user_perms = getattr(request.state, "permissions", [])
    # Re-use service logic for wildcards
    # Or simplified here:
    if required_perm in user_perms: return True
    for p in user_perms:
        if p.endswith(".*") and required_perm.startswith(p[:-2]):
            return True
            
    # Raise
    raise HTTPException(status_code=403, detail=f"Missing permission: {required_perm}")

@router.get("", response_model=List[role_schemas.TenantRole])
async def list_roles(
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """List all available roles in the tenant"""
    stmt = select(models.TenantRole).where(
        models.TenantRole.tenant_id == current_tenant.id
    ).options(selectinload(models.TenantRole.permissions))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/permissions", response_model=List[role_schemas.Permission])
async def list_system_permissions(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available system permissions (for UI selector)"""
    stmt = select(models.Permission)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=role_schemas.TenantRole)
async def create_role(
    role_in: role_schemas.TenantRoleCreate,
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Create a new custom role"""
    # Permission Check
    await check_permission(request, "iam.role.manage")
    
    new_role = models.TenantRole(
        tenant_id=current_tenant.id,
        name=role_in.name,
        description=role_in.description,
        is_system_role=False
    )
    db.add(new_role)
    await db.flush() # get ID
    
    # Add Permissions
    for perm_slug in role_in.permissions:
        db.add(models.RolePermission(role_id=new_role.id, permission_slug=perm_slug))
        
    await db.commit()
    await db.refresh(new_role)
    
    # Reload with perms
    stmt = select(models.TenantRole).where(models.TenantRole.id == new_role.id).options(selectinload(models.TenantRole.permissions))
    new_role = (await db.execute(stmt)).scalars().first()
    
    return new_role

@router.put("/{role_id}", response_model=role_schemas.TenantRole)
async def update_role(
    role_id: str,
    role_in: role_schemas.TenantRoleUpdate,
    request: Request,
    current_user: models.User = Depends(get_current_active_user),
    current_tenant: models.Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Update custom role permissions"""
    await check_permission(request, "iam.role.manage")
    
    stmt = select(models.TenantRole).where(models.TenantRole.id == role_id, models.TenantRole.tenant_id == current_tenant.id)
    role = (await db.execute(stmt)).scalars().first()
    
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    if role.is_system_role:
        raise HTTPException(status_code=400, detail="Cannot edit system roles directly.")
        
    if role_in.name: role.name = role_in.name
    if role_in.description: role.description = role_in.description
    
    if role_in.permissions is not None:
        # Clear existing
        # This is a full replace logic
        from sqlalchemy import delete
        await db.execute(delete(models.RolePermission).where(models.RolePermission.role_id == role.id))
        
        for perm_slug in role_in.permissions:
             db.add(models.RolePermission(role_id=role.id, permission_slug=perm_slug))
             
    await db.commit()
    
    # Reload
    stmt = select(models.TenantRole).where(models.TenantRole.id == role.id).options(selectinload(models.TenantRole.permissions))
    role = (await db.execute(stmt)).scalars().first()
    return role
