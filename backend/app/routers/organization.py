from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.models.models import User
from app.services.auth_service import get_current_active_user
from app.services.organization_service import OrganizationService


router = APIRouter()

from pydantic import BaseModel

class RoleCreate(BaseModel):
    name: str
    description: str
    permissions: dict
    tenant_id: str

@router.post("/roles")
async def create_organization_role(
    role: RoleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a custom role.
    """
    """
    Create a custom role.
    """
    service = OrganizationService(db)
    new_role = await service.create_organization_role(role.dict(), role.tenant_id, current_user)
    return new_role


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: dict | None = None
    tenant_id: str

@router.put("/roles/{role_id}")
async def update_organization_role(
    role_id: str,
    role: RoleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a custom role.
    """
    service = OrganizationService(db)
    updated_role = await service.update_organization_role(role_id, role.dict(exclude_unset=True), role.tenant_id, current_user)
    return updated_role

@router.delete("/roles/{role_id}")
async def delete_organization_role(
    role_id: str,
    tenant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a custom role.
    """
    service = OrganizationService(db)
    result = await service.delete_organization_role(role_id, tenant_id, current_user)
    return result


@router.get("/users")
async def list_organization_users(
    tenant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users in the organization.
    Returns detailed user information with roles.
    """
    service = OrganizationService(db)
    users = await service.list_organization_users(tenant_id, current_user)
    return users


@router.get("/roles")
async def list_organization_roles(
    tenant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all roles in the organization.
    For MVP, returns built-in roles with user counts.
    """
    service = OrganizationService(db)
    roles = await service.get_organization_roles(tenant_id, current_user)
    return roles


@router.get("/sharing")
async def get_sharing_overview(
    tenant_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overview of all shared resources in the organization.
    Shows what's shared with whom and at what access level.
    """
    service = OrganizationService(db)
    sharing = await service.get_sharing_overview(tenant_id, current_user)
    return sharing
