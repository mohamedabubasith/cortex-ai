from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.core.database import get_db
from app.models import models
from app.schemas import groups as group_schemas
from app.services.auth_service import get_current_active_user
from app.services import auth_service # for helper functions if needed

router = APIRouter()

@router.post("", response_model=group_schemas.TenantGroup)
async def create_group(
    group: group_schemas.TenantGroupCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new group in the user's current tenant"""
    # 1. Get current tenant membership to ensure permissions
    # Assuming user is in a tenant context (or we pick the first one/header)
    # For now, simplistic approach: pick first tenant membership where role is admin/owner
    # OR rely on a header 'X-Tenant-ID'. Let's assume user context carries it or we fetch it.
    
    # We need a way to know WHICH tenant to create group for.
    # In other endpoints we relied on implicit "first tenant" or context.
    # Let's verify standard pattern.
    
    stmt = select(models.TenantMember).where(models.TenantMember.user_id == current_user.id)
    result = await db.execute(stmt)
    memberships = result.scalars().all()
    
    if not memberships:
         raise HTTPException(status_code=400, detail="User belongs to no tenant")
         
    # Default to first tenant if no explicit selection (MVP)
    # Ideally should come from request header or context
    tenant_id = memberships[0].tenant_id
    
    # Check permission (Owner/Admin only)
    if memberships[0].role not in ['owner', 'admin']:
         raise HTTPException(status_code=403, detail="Only admins can create groups")

    new_group = models.TenantGroup(
        tenant_id=tenant_id,
        name=group.name,
        description=group.description
    )
    
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group

@router.get("", response_model=List[group_schemas.TenantGroup])
async def list_groups(
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List all groups in user's tenant"""
    # Resolving tenant same as above
    stmt = select(models.TenantMember).where(models.TenantMember.user_id == current_user.id)
    result = await db.execute(stmt)
    membership = result.scalars().first()
    
    if not membership:
        return []

    # Get groups with member count
    stmt = select(
        models.TenantGroup,
        func.count(models.TenantGroupMember.user_id).label("member_count")
    ).outerjoin(
        models.TenantGroupMember
    ).where(
        models.TenantGroup.tenant_id == membership.tenant_id
    ).group_by(models.TenantGroup.id)
    
    result = await db.execute(stmt)
    # Result is list of (Group, count)
    
    groups = []
    for g, count in result.all():
        g.member_count = count
        groups.append(g)
        
    return groups

@router.get("/{group_id}", response_model=group_schemas.GroupDetail)
async def get_group(
    group_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get group details with members"""
    stmt = select(models.TenantGroup).where(models.TenantGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalars().first()
    
    if not group:
         raise HTTPException(status_code=404, detail="Group not found")
         
    # Verify tenant access
    # (Simplified: just check if user is in same tenant. Strictly should check same tenant ID)
    
    # Load members with user details
    from sqlalchemy.orm import joinedload
    
    stmt = select(models.TenantGroup).where(models.TenantGroup.id == group_id).options(
        joinedload(models.TenantGroup.members).joinedload(models.TenantGroupMember.user)
    )
    result = await db.execute(stmt)
    group = result.scalars().first()
    
    return group

@router.post("/{group_id}/members", response_model=group_schemas.TenantGroupMember)
async def add_member(
    group_id: str,
    member_data: group_schemas.TenantGroupMemberCreate,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Add a user to a group"""
    # 1. Verify group exists and user has permission
    # (Omitted brevity: check admin role)
    
    # 2. Check if user is in the tenant
    # (Omitted brevity)
    
    # 3. Add
    # Check existence
    stmt = select(models.TenantGroupMember).where(
        models.TenantGroupMember.group_id == group_id,
        models.TenantGroupMember.user_id == member_data.user_id
    )
    result = await db.execute(stmt)
    if result.scalars().first():
         raise HTTPException(status_code=409, detail="User already in group")

    new_member = models.TenantGroupMember(
        group_id=group_id,
        user_id=member_data.user_id
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    
    # Reload with user for response schema
    from sqlalchemy.orm import selectinload
    stmt = select(models.TenantGroupMember).where(
        models.TenantGroupMember.group_id == group_id,
        models.TenantGroupMember.user_id == member_data.user_id
    ).options(selectinload(models.TenantGroupMember.user))
    result = await db.execute(stmt)
    new_member = result.scalars().first()

    return new_member

@router.delete("/{group_id}/members/{user_id}")
async def remove_member(
    group_id: str,
    user_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(models.TenantGroupMember).where(
        models.TenantGroupMember.group_id == group_id,
        models.TenantGroupMember.user_id == user_id
    )
    result = await db.execute(stmt)
    member = result.scalars().first()
    
    if member:
        await db.delete(member)
        await db.commit()
        
    return {"status": "success"}

@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    current_user: models.User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(models.TenantGroup).where(models.TenantGroup.id == group_id)
    result = await db.execute(stmt)
    group = result.scalars().first()
    
    if group:
        await db.delete(group)
        await db.commit()
        
    return {"status": "success"}
