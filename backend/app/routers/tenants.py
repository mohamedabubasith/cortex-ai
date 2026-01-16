from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import User, TenantMember
from app.services.auth_service import get_current_active_user
from app.services.tenant_service import TenantService
from app.schemas import schemas

router = APIRouter()


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "member"  # owner, admin, member, viewer


class UpdateRoleRequest(BaseModel):
    role: str


class TenantMemberResponse(BaseModel):
    tenant_id: str
    user_id: str
    role: str
    user_email: str
    user_name: str | None

    class Config:
        from_attributes = True



@router.post("/", response_model=schemas.Tenant)
async def create_tenant(
    tenant: schemas.TenantCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new tenant.
    Authenticated user becomes the 'owner' of the new tenant.
    """
    service = TenantService(db)
    return await service.create_tenant(tenant, current_user)


@router.post("/{tenant_id}/members", response_model=dict)
async def add_tenant_member(
    tenant_id: str,
    request: AddMemberRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a user to a tenant with specified role.
    
    Permissions: Tenant owner or super admin
    """
    service = TenantService(db)
    member = await service.add_member(
        tenant_id=tenant_id,
        user_id=request.user_id,
        role=request.role,
        requesting_user=current_user
    )
    
    return {
        "message": "Member added successfully",
        "tenant_id": member.tenant_id,
        "user_id": member.user_id,
        "role": member.role
    }


@router.delete("/{tenant_id}/members/{user_id}")
async def remove_tenant_member(
    tenant_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a user from a tenant.
    
    Permissions: Tenant owner or super admin
    """
    service = TenantService(db)
    result = await service.remove_member(
        tenant_id=tenant_id,
        user_id=user_id,
        requesting_user=current_user
    )
    return result


@router.put("/{tenant_id}/members/{user_id}")
async def update_member_role(
    tenant_id: str,
    user_id: str,
    request: UpdateRoleRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a tenant member's role.
    
    Permissions: Tenant owner or super admin
    """
    service = TenantService(db)
    member = await service.update_member_role(
        tenant_id=tenant_id,
        user_id=user_id,
        new_role=request.role,
        requesting_user=current_user
    )
    
    return {
        "message": "Role updated successfully",
        "tenant_id": member.tenant_id,
        "user_id": member.user_id,
        "role": member.role
    }


@router.get("/{tenant_id}/members")
async def list_tenant_members(
    tenant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all members of a tenant.
    
    Permissions: Any tenant member
    """
    service = TenantService(db)
    members = await service.list_members(
        tenant_id=tenant_id,
        requesting_user=current_user
    )
    
    # Format response
    result = []
    for member in members:
        result.append({
            "tenant_id": member.tenant_id,
            "user_id": member.user_id,
            "role": member.role,
            "user_email": member.user.email,
            "user_name": member.user.full_name,
            "joined_at": member.created_at.isoformat()
        })
    
    return result


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a tenant and all its resources.
    
    Permissions: Super admin only
    
    This will cascade delete:
    - All tenant members
    - All agents
    - All knowledge bases
    - All database connections
    - All MCP connections
    - All LLM configurations
    """
    service = TenantService(db)
    result = await service.delete_tenant(
        tenant_id=tenant_id,
        requesting_user=current_user
    )
    return result
