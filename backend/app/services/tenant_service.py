"""Tenant Management Service"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException

from app.models.models import Tenant, TenantMember, User
from app.schemas import schemas


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_permission(self, user: User, tenant_id: str, require_owner: bool = False) -> bool:
        """Check if user has permission to manage tenant members"""
        # Super admins can do anything
        if user.is_superuser:
            return True

        # Check tenant membership
        query = select(TenantMember).where(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == user.id
            )
        )
        result = await self.db.execute(query)
        membership = result.scalars().first()

        if not membership:
            return False

        if require_owner:
            return membership.role == "owner"
        
        # For non-owner actions, both owner and admin can manage
        return membership.role in ["owner", "admin"]

    async def create_tenant(
        self,
        tenant_data: schemas.TenantCreate,
        requesting_user: User
    ) -> Tenant:
        """Create a new tenant and assign creator as owner"""
        # 1. Create tenant
        new_tenant = Tenant(
            name=tenant_data.name,
            slug=tenant_data.slug
        )
        self.db.add(new_tenant)
        try:
            await self.db.commit()
            await self.db.refresh(new_tenant)
        except Exception as e:
            await self.db.rollback()
            # Likely duplicate slug or name constraint
            raise HTTPException(status_code=400, detail=f"Failed to create tenant. Name or slug might already exist.")

        # 2. Add creator as Owner
        member = TenantMember(
            tenant_id=new_tenant.id,
            user_id=requesting_user.id,
            role="owner"
        )
        self.db.add(member)
        await self.db.commit()
        
        return new_tenant

    async def add_member(
        self,
        tenant_id: str,
        user_id: str,
        role: str,
        requesting_user: User
    ) -> TenantMember:
        """Add a user to a tenant with specified role"""
        # Check permission
        if not await self._check_permission(requesting_user, tenant_id, require_owner=True):
            raise HTTPException(
                status_code=403,
                detail="Only tenant owners and super admins can add members"
            )

        # Validate role
        # Validate role
        valid_roles = ["owner", "admin", "member", "viewer"]
        if role not in valid_roles:
            # Check if it's a valid custom role ID for this tenant
            from app.models.models import OrganizationRole
            role_query = select(OrganizationRole).where(
                and_(
                    OrganizationRole.id == role,
                    OrganizationRole.tenant_id == tenant_id
                )
            )
            role_result = await self.db.execute(role_query)
            if not role_result.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role. Must be one of {', '.join(valid_roles)} or a valid custom role ID."
                )

        # Check if user exists
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        target_user = user_result.scalars().first()
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already a member
        existing_query = select(TenantMember).where(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == user_id
            )
        )
        existing_result = await self.db.execute(existing_query)
        existing_member = existing_result.scalars().first()

        if existing_member:
            raise HTTPException(
                status_code=400,
                detail="User is already a member of this tenant"
            )

        # Create membership
        new_member = TenantMember(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role
        )
        self.db.add(new_member)
        await self.db.commit()
        await self.db.refresh(new_member)

        return new_member

    async def remove_member(
        self,
        tenant_id: str,
        user_id: str,
        requesting_user: User
    ) -> Dict[str, Any]:
        """Remove a user from a tenant"""
        # Check permission
        if not await self._check_permission(requesting_user, tenant_id, require_owner=True):
            raise HTTPException(
                status_code=403,
                detail="Only tenant owners and super admins can remove members"
            )

        # Get the member to remove
        query = select(TenantMember).where(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        member = result.scalars().first()

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        # Prevent removing the last owner
        if member.role == "owner":
            owner_count_query = select(TenantMember).where(
                and_(
                    TenantMember.tenant_id == tenant_id,
                    TenantMember.role == "owner"
                )
            )
            owner_result = await self.db.execute(owner_count_query)
            owner_count = len(owner_result.scalars().all())

            if owner_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove the last owner of a tenant"
                )

        # Delete the membership
        await self.db.delete(member)
        await self.db.commit()

        return {"message": "Member removed successfully"}

    async def update_member_role(
        self,
        tenant_id: str,
        user_id: str,
        new_role: str,
        requesting_user: User
    ) -> TenantMember:
        """Update a member's role in the tenant"""
        # Check permission
        if not await self._check_permission(requesting_user, tenant_id, require_owner=True):
            raise HTTPException(
                status_code=403,
                detail="Only tenant owners and super admins can update member roles"
            )

        # Validate role
        # Validate role
        valid_roles = ["owner", "admin", "member", "viewer"]
        if new_role not in valid_roles:
            # Check if it's a valid custom role ID for this tenant
            from app.models.models import OrganizationRole
            role_query = select(OrganizationRole).where(
                and_(
                    OrganizationRole.id == new_role,
                    OrganizationRole.tenant_id == tenant_id
                )
            )
            role_result = await self.db.execute(role_query)
            if not role_result.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid role. Must be one of {', '.join(valid_roles)} or a valid custom role ID."
                )

        # Get the member
        query = select(TenantMember).where(
            and_(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        member = result.scalars().first()

        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        # Prevent downgrading the last owner
        if member.role == "owner" and new_role != "owner":
            owner_count_query = select(TenantMember).where(
                and_(
                    TenantMember.tenant_id == tenant_id,
                    TenantMember.role == "owner"
                )
            )
            owner_result = await self.db.execute(owner_count_query)
            owner_count = len(owner_result.scalars().all())

            if owner_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change role of the last owner"
                )

        # Update the role
        member.role = new_role
        await self.db.commit()
        await self.db.refresh(member)

        return member

    async def list_members(
        self,
        tenant_id: str,
        requesting_user: User
    ) -> List[TenantMember]:
        """List all members of a tenant"""
        # Any tenant member can view other members
        if not await self._check_permission(requesting_user, tenant_id, require_owner=False):
            raise HTTPException(
                status_code=403,
                detail="You must be a member of this tenant to view its members"
            )

        # Get all members with user details
        from sqlalchemy.orm import selectinload
        query = select(TenantMember).where(
            TenantMember.tenant_id == tenant_id
        ).options(selectinload(TenantMember.user))
        
        result = await self.db.execute(query)
        members = result.scalars().all()

        return members

    async def delete_tenant(
        self,
        tenant_id: str,
        requesting_user: User
    ) -> Dict[str, Any]:
        """Delete a tenant and all its resources (super admin only)"""
        # Only super admins can delete tenants
        if not requesting_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="Only super admins can delete tenants"
            )

        # Get the tenant
        query = select(Tenant).where(Tenant.id == tenant_id)
        result = await self.db.execute(query)
        tenant = result.scalars().first()

        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Delete tenant (cascade will handle members and resources)
        await self.db.delete(tenant)
        await self.db.commit()

        return {
            "message": "Tenant deleted successfully",
            "tenant_id": tenant_id,
            "tenant_name": tenant.name
        }
